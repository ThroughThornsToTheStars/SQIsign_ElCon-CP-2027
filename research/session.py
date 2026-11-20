"""One complete session, with balanced within-set profile positions and OS telemetry."""
import argparse
import csv
import datetime
import hashlib
import json
import os
import platform
import random
import time
from pathlib import Path

from benchmark import METRICS, command
from check import PROFILES, SIZES, executable


def reading(path):
    try:
        return path.read_text().strip()
    except OSError:
        return None


def stamp(cpu):
    base = Path(f"/sys/devices/system/cpu/cpu{cpu}")
    return {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "monotonic_ns": time.monotonic_ns(), "load": os.getloadavg(),
            "current_khz": reading(base/"cpufreq/scaling_cur_freq"),
            "cpu_ticks": [line for line in Path("/proc/stat").read_text().splitlines()
                          if line.startswith("cpu")], "siblings": reading(base/"topology/thread_siblings_list")}


def run(output, session, blocks, cpu):
    if session < 1 or not 4 <= blocks < 1000 or blocks % 4:
        raise ValueError("use positive session ID and 4..996 blocks in multiples of four")
    if command("git", "diff", "HEAD", "--name-only"):
        raise RuntimeError("commit tracked changes before measuring")
    output.mkdir(parents=True, exist_ok=False)
    os.sched_setaffinity(0, {cpu})
    seed = 240319 + session
    order = random.Random(seed)
    base = Path(f"/sys/devices/system/cpu/cpu{cpu}/cpufreq")
    meta = {"revision": command("git","rev-parse","HEAD"), "session": session, "order_seed": seed,
            "blocks": blocks, "cpu": cpu, "affinity": sorted(os.sched_getaffinity(0)),
            "platform": platform.platform(), "cc": command("cc","--version").splitlines()[0],
            "nettle": command("pkg-config","--modversion","nettle"), "before": stamp(cpu),
            "cpufreq": {f: reading(base/f) for f in ("scaling_governor","scaling_driver","scaling_min_freq","scaling_max_freq")},
            "no_turbo": reading(Path("/sys/devices/system/cpu/intel_pstate/no_turbo")),
            "binaries": {}, "build_files": {}, "blocks_observed": []}
    for p in PROFILES:
        directory = Path(f"build-{p}-Release")
        for name in ("CMakeCache.txt","compile_commands.json"):
            meta["build_files"][f"{p}/{name}"] = hashlib.sha256((directory/name).read_bytes()).hexdigest()
        for v in SIZES:
            binary = executable(p,v,"Release")
            meta["binaries"][f"{p}/{v}"] = hashlib.sha256(binary.read_bytes()).hexdigest()
            command(str(binary),"trial",str(900000+session))
    meta["after_warmup"] = stamp(cpu)
    metrics = METRICS  # includes batch of 256 domain init+clear calls
    with (output/"raw.csv").open("x") as f:
        writer = csv.writer(f)
        writer.writerow(["session","variant","profile","index","run_order",*metrics])
        position = 0
        for block in range(blocks):
            index = 1000*session + block + 1
            if block % 4 == 0:
                permutations = {v: order.sample(PROFILES,4) for v in SIZES}
            for v in order.sample(list(SIZES),len(SIZES)):
                seq = permutations[v]
                shift = block % 4
                for p in seq[shift:]+seq[:shift]:
                    values = list(map(int,command(str(executable(p,v,"Release")),"trial",str(index)).split(",")))
                    if len(values)!=len(metrics) or min(values)<=0:
                        raise ValueError((v,p,index,values))
                    writer.writerow([session,v,p,index,position,*values])
                    position += 1
            f.flush()
            meta["blocks_observed"].append(stamp(cpu))
    with (output/"memory.csv").open("x") as f:
        w=csv.writer(f)
        w.writerow(["session","variant","profile","index","phase","rss_kib","nettle_rss_kib","private_kib","hwm_kib"])
        for v in SIZES:
            for p in PROFILES:
                index = session*1000+1
                lines=command(str(executable(p,v,"Release")),"memory",str(index)).splitlines()
                if [line.split(",")[0] for line in lines]!=["before","keygen","sign","verify"]:
                    raise ValueError(lines)
                for line in lines:
                    w.writerow([session,v,p,index,*line.split(",")])
    meta["end"] = stamp(cpu)
    (output/"metadata.json").write_text(json.dumps(meta,indent=2)+"\n")


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("output",type=Path)
    parser.add_argument("--session",type=int,required=True)
    parser.add_argument("--blocks",type=int,default=16)
    parser.add_argument("--cpu",type=int,required=True)
    args=parser.parse_args()
    run(args.output,args.session,args.blocks,args.cpu)
