"""Generate only D26-D30 with mature tools and bounded request pacing.

The Microsoft endpoint currently throttles rapid synthesis (HTTP 429). Wait
three seconds before every uncached fragment request, including retries. This
runner changes no voice, rate, cache hash, merge logic or published audio route.
"""
import asyncio
import sys

import make_audio_v2 as listening
import make_audio_speaking as speaking


def paced(synth):
    async def call(*args):
        await asyncio.sleep(3)
        return await synth(*args)
    return call


def main():
    listening.ensure_deps()
    listening.setup_ffmpeg()
    speaking.setup_ffmpeg()
    listening.synth_fragment = paced(listening.synth_fragment)
    speaking.synth = paced(speaking.synth)
    failures = []
    for module, prefix, tool in (("listening", "L", listening), ("speaking", "S", speaking)):
        manifest = tool.load_manifest()
        for day in range(26, 31):
            tool.process_course(f"content/{module}/{prefix}4A-T1-W01-D{day}.json", manifest, failures)
            tool.save_manifest(manifest)
    print("FAILURES", failures)
    return bool(failures)


if __name__ == "__main__":
    sys.exit(main())
