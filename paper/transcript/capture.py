"""Recapture the public commitment encoding from the pinned upstream verifier (Linux)."""
import io
from pathlib import Path
import subprocess
import tempfile
import zipfile

REV = "6d017708db403bf83977fa70770fc4f7f9e9ff21"
ROOT = Path(__file__).resolve().parents[2]


def main():
    archive = subprocess.check_output(["git", "-C", ROOT, "archive", "--format=zip", REV])
    with tempfile.TemporaryDirectory() as directory:
        src = Path(directory)
        with zipfile.ZipFile(io.BytesIO(archive)) as files:
            files.extractall(src)
        source = src / "src/verification/ref/lvlx/common.c"
        original = source.read_text()
        line = "    fp2_encode(buf + PUBLICKEY_BYTES, &com_curve->A);"
        if original.count(line) != 1:
            raise ValueError("unexpected upstream hash routine")
        trace = r'''
    fputs("COMMITMENT_A=", stderr);
    for (size_t i = 0; i < FP2_ENCODED_BYTES; i++)
        fprintf(stderr, "%02x", buf[PUBLICKEY_BYTES + i]);
    fputc('\n', stderr);'''
        source.write_text("#include <stdio.h>\n" + original.replace(line, line + trace))
        build = src / "build"
        subprocess.run(["cmake", "-S", src, "-B", build, "-DCMAKE_BUILD_TYPE=Release",
                        "-DSQISIGN_BUILD_TYPE=ref", "-DENABLE_SIGN=OFF", "-DGF_RADIX=64"], check=True)
        subprocess.run(["cmake", "--build", build, "-j2", "--target", "sqisign_test_kat_p324_3"], check=True)
        run = subprocess.run([build / "test/sqisign_test_kat_p324_3", "0"],
                             cwd=build / "test", check=True, capture_output=True, text=True)
        lines = [v for v in run.stderr.splitlines() if v.startswith("COMMITMENT_A=")]
        if len(lines) != 1 or len(bytes.fromhex(lines[0].split("=")[1])) != 82:
            raise ValueError("expected one encoded commitment")
        print(lines[0])


if __name__ == "__main__":
    main()
