"""Verify the public p324_3 challenge fixture against upstream KAT record 0."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
KAT = HERE.parents[1] / "KAT/PQCsignKAT_270_SQIsign_p324_3.rsp"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    vector = json.loads((HERE / "count0.json").read_text(encoding="utf-8"))
    fields = {}
    with KAT.open(encoding="ascii") as records:
        for line in records:
            if " = " not in line:
                continue
            key, value = line.strip().split(" = ", 1)
            if key == "count" and fields:
                break
            if key in {"count", "pk", "msg", "sm"}:
                fields[key] = value
    require(fields["count"] == "0", "wrong KAT record")
    pk, msg, sm = (bytes.fromhex(fields[key]) for key in ("pk", "msg", "sm"))
    a = bytes.fromhex(vector["commitment_A_hex"])
    require((len(pk), len(a), len(msg), len(sm)) == (83, 82, 33, 233), "unexpected sizes")
    require(sm[200:] == msg, "unexpected signed-message layout")
    transcript = b"SQI" + pk + a + msg
    expected = sm[182:198]  # 82-byte auxiliary A, four 25-byte responses, then challenge
    actual = hashlib.shake_256(transcript).digest(16)
    require(vector["pk_hex"] == pk.hex() and vector["message_hex"] == msg.hex(), "public fields differ")
    require(vector["challenge_hex"] == expected.hex(), "fixture differs from upstream signature")
    require(actual == expected, "Fiat-Shamir challenge mismatch")
    require(hashlib.shake_256(transcript + b"\x00").digest(16) != expected, "altered input matched")
    print(f"PASS: {len(transcript)} transcript bytes; challenge {actual.hex()}")


if __name__ == "__main__":
    main()
