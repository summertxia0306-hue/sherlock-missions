"""Generate only Unit 5, preserving established voices/cache and pacing."""
import sys
from generate_4a_unit4_audio import paced
import make_audio_v2 as listening
import make_audio_speaking as speaking


def main():
    listening.ensure_deps()
    listening.setup_ffmpeg()
    speaking.setup_ffmpeg()
    listening.synth_fragment = paced(listening.synth_fragment)
    speaking.synth = paced(speaking.synth)
    failures = []
    for module, prefix, tool in (("listening", "L", listening), ("speaking", "S", speaking)):
        manifest = tool.load_manifest()
        for day in range(31, 36):
            tool.process_course(f"content/{module}/{prefix}4A-T1-W01-D{day}.json", manifest, failures)
            tool.save_manifest(manifest)
    print("FAILURES", failures)
    return bool(failures)


if __name__ == "__main__":
    sys.exit(main())
