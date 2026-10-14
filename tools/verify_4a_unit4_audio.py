"""Decode every U4 output and newly added fragment; preserve old assets."""
import hashlib
import json
import subprocess
from pathlib import Path

import imageio_ffmpeg
from build_4a_starter_courses import json_write

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "content/drafts/4A-T1-W01-UNIT4"
BASELINE = "f5c9ed5997d5048efe9dc76aa975b848e58f196f"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8")


def decode(path):
    result = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-xerror", "-i", str(path), "-f", "s16le", "-ar", "24000", "-ac", "1", "pipe:1"], capture_output=True)
    if result.returncode or not result.stdout:
        raise RuntimeError(f"Incomplete decode: {path.name}: {result.stderr.decode('utf-8', errors='replace')}")
    return round(len(result.stdout) / 48000, 3)


def blob_hash(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def main():
    plan = json.loads((DRAFT / "audio-generation-plan.json").read_text(encoding="utf-8"))
    if len(plan["items"]) != 154 or len({item["path"] for item in plan["items"]}) != 154:
        raise RuntimeError("Expected 154 distinct finished audio outputs")
    items = []
    for item in plan["items"]:
        path = ROOT / item["path"]
        duration = decode(path)
        if item["module"] == "speaking" and item["kind"].endswith("_repeat") and duration >= 20:
            raise RuntimeError(f"Repeat demo exceeds 20 seconds: {item['path']}")
        items.append(dict(path=item["path"], module=item["module"], course_id=item["course_id"], bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), decoded_seconds=duration))
    fragments = []
    for module in ("listening", "speaking"):
        manifest_path = f"static/audio/{module}/manifest.json"
        current = json.loads((ROOT / manifest_path).read_text(encoding="utf-8"))
        baseline = json.loads(git("show", f"{BASELINE}:{manifest_path}"))
        for group in ("fragments", "courses"):
            for key, value in baseline[group].items():
                if current[group].get(key) != value:
                    raise RuntimeError(f"Old manifest entry changed: {module}/{group}/{key}")
        for key in current["fragments"].keys() - baseline["fragments"].keys():
            path = ROOT / f"static/audio/{module}/fragments/{key}.mp3"
            fragments.append(dict(path=path.relative_to(ROOT).as_posix(), decoded_seconds=decode(path), bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        for temporary in (ROOT / f"static/audio/{module}").rglob("*.tmp"):
            raise RuntimeError(f"Unfinished temporary audio remains: {temporary.name}")
    # Audio is byte-identical to Git; JSON may have checkout-only LF/CRLF
    # differences already present before this batch. Never rewrite old files.
    old_blobs = {}
    for entry in git("ls-tree", "-r", BASELINE, "content/listening", "content/speaking", "static/audio").splitlines():
        metadata, rel = entry.split("\t", 1)
        if not rel.endswith("manifest.json"):
            old_blobs[rel] = metadata.split()[2]
    # One Git process applies repository clean filters to all existing paths.
    hashes = subprocess.check_output(["git", "hash-object", "--stdin-paths"], input=("\n".join(old_blobs)+"\n").encode("utf-8"), cwd=ROOT).decode("utf-8").splitlines()
    newline_only_json = 0
    for (rel, expected), actual in zip(old_blobs.items(), hashes):
        if actual != expected:
            if rel.endswith(".json") and blob_hash((ROOT / rel).read_bytes().replace(b"\r\n", b"\n")) == expected:
                newline_only_json += 1
            else:
                raise RuntimeError(f"Pre-existing course/audio changed: {rel}")
    if len(hashes) != len(old_blobs):
        raise RuntimeError("Incomplete old asset hash check")
    report = dict(baseline=BASELINE, total_outputs=len(items), listening_outputs=sum(item["module"] == "listening" for item in items), speaking_outputs=sum(item["module"] == "speaking" for item in items), full_decode="passed", unfinished_tmp=0, old_assets_checked=len(old_blobs), old_assets_changed=0, old_assets_byte_identical_to_git=len(old_blobs)-newline_only_json, old_json_checkout_newline_only=newline_only_json, old_manifest_entries_changed=0, new_fragments_decoded=len(fragments), items=items, new_fragments=sorted(fragments, key=lambda item: item["path"]))
    json_write(DRAFT / "audio-validation.json", report)
    print(f"PASS: {len(items)} outputs and {len(fragments)} new fragments fully decoded; {report['old_assets_checked']} old assets unchanged ({newline_only_json} JSON checkout newline-only differences).")


if __name__ == "__main__":
    main()
