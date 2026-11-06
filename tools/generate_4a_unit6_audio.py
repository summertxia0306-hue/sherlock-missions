"""Generate Unit 6 using the existing voices, cache, and request pacing."""
import sys
import json
from pathlib import Path
from shutil import copyfile

from generate_4a_unit4_audio import paced
import make_audio_v2 as listening
import make_audio_speaking as speaking


def reuse_narrator_fragments():
    """Reuse the same voice, rate and exact text already synthesized for listening."""
    plan_path = Path(listening.ROOT) / "content/drafts/4A-T1-W01-UNIT6/audio-generation-plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    source_entries = listening.load_manifest()["fragments"]
    destination = Path(speaking.FRAG_DIR)
    destination.mkdir(parents=True, exist_ok=True)
    reused = 0
    for item in plan["items"]:
        if item["module"] != "speaking":
            continue
        text = item["clips"][0][1]
        key = listening.frag_key("n", text)
        source = Path(listening.FRAG_DIR) / (key + ".mp3")
        target = destination / (speaking.frag_key(text) + ".mp3")
        metadata = {"role": "n", "voice": speaking.VOICE, "rate": speaking.RATE, "text": text}
        if not target.exists() and source_entries.get(key) == metadata and source.is_file():
            copyfile(source, target)
            reused += 1
    return reused


def main():
    listening.ensure_deps()
    listening.setup_ffmpeg()
    speaking.setup_ffmpeg()
    listening.synth_fragment = paced(listening.synth_fragment)
    speaking.synth = paced(speaking.synth)
    failures = []
    for module, prefix, tool in (("listening", "L", listening), ("speaking", "S", speaking)):
        if module == "speaking":
            print("Exact narrator fragments reused:", reuse_narrator_fragments())
        manifest = tool.load_manifest()
        for day in range(36, 41):
            tool.process_course(f"content/{module}/{prefix}4A-T1-W01-D{day}.json", manifest, failures)
            tool.save_manifest(manifest)
    print("FAILURES", failures)
    return bool(failures)


if __name__ == "__main__":
    sys.exit(main())
