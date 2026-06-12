# -*- coding: utf-8 -*-
"""口语示范音频生成工具（开发期在家长 PC 运行，镜像 make_audio_v2 的模式）。

每题一个 MP3：repeat = Ana 朗读示范句；qa = Ana 朗读问题。
片段按 sha1 哈希命名复用；增量生成；代理走 tools/proxy.txt（与听力工具同款）。

用法：
  python tools/make_audio_speaking.py            # 全部口语课程
  python tools/make_audio_speaking.py S01D01     # 指定课程
"""
import asyncio
import hashlib
import json
import os
import subprocess
import sys

VOICE = "en-US-AnaNeural"   # 与听力旁白同音色（孩子熟悉）
RATE = "-10%"
BITRATE = "64k"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_ROOT = os.path.join(ROOT, "static", "audio", "speaking")
FRAG_DIR = os.path.join(AUDIO_ROOT, "fragments")
MANIFEST_PATH = os.path.join(AUDIO_ROOT, "manifest.json")
CONTENT_DIR = os.path.join(ROOT, "content", "speaking")


def get_proxy():
    for k in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        v = os.environ.get(k)
        if v:
            return v
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxy.txt")
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as fh:
            v = fh.read().strip()
        if v:
            return v
    return None


PROXY = get_proxy()
FFMPEG = None


def ensure_deps():
    need = []
    for mod, pkg in (("edge_tts", "edge-tts"), ("imageio_ffmpeg", "imageio-ffmpeg")):
        try:
            __import__(mod)
        except ImportError:
            need.append(pkg)
    if need:
        print("首次运行：安装依赖 %s（需联网）..." % " ".join(need))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q"] + need)


def setup_ffmpeg():
    global FFMPEG
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def run_ffmpeg(args, cwd=None):
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-y"] + args
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError("ffmpeg 失败: %s" % (r.stderr or "").strip()[-300:])


def frag_key(text):
    return hashlib.sha1(("%s|%s|%s" % (VOICE, text, RATE)).encode("utf-8")).hexdigest()[:16]


async def synth(text, dest):
    import edge_tts
    com = edge_tts.Communicate(text, VOICE, rate=RATE, proxy=PROXY)
    buf = bytearray()
    async for chunk in com.stream():
        if chunk["type"] == "audio":
            buf.extend(chunk["data"])
    if len(buf) < 1000:
        raise RuntimeError("音频过短，疑似生成失败")
    tmp = dest + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(bytes(buf))
    os.replace(tmp, dest)


def load_manifest():
    if os.path.isfile(MANIFEST_PATH):
        with open(MANIFEST_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    return {"fragments": {}, "courses": {}}


def save_manifest(m):
    os.makedirs(AUDIO_ROOT, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)


def speak_text(q):
    return q["text"] if q["type"] == "repeat" else q["question"]


def process_course(path, manifest, failures):
    with open(path, encoding="utf-8") as fh:
        course = json.load(fh)

    sys.path.insert(0, ROOT)
    from speaking import models
    errors = models.validate_course(course, check_audio=False)
    if errors:
        print("课程 %s JSON 校验失败，跳过：" % course.get("course_id"))
        for e in errors:
            print("  -", e)
        failures.append("%s JSON 校验失败" % path)
        return

    cid = course["course_id"]
    os.makedirs(FRAG_DIR, exist_ok=True)
    items = [(q, speak_text(q)) for q in course["questions"]]
    print("课程 %s：%d 个音频目标" % (cid, len(items)))

    async def gen_all():
        for q, text in items:
            k = frag_key(text)
            frag = os.path.join(FRAG_DIR, k + ".mp3")
            manifest["fragments"][k] = {"voice": VOICE, "rate": RATE, "text": text}
            if os.path.isfile(frag):
                continue
            print("  生成 Q%d: %s" % (q["id"], text[:50]))
            for attempt in range(3):
                try:
                    await synth(text, frag)
                    break
                except Exception as e:
                    if attempt == 2:
                        failures.append("%s Q%d | %s | %s" % (cid, q["id"], text, e))
                    else:
                        print("    重试(%d): %s" % (attempt + 1, e))
                        await asyncio.sleep(2)

    asyncio.run(gen_all())

    course_entry = manifest["courses"].setdefault(cid, {})
    merged = skipped = 0
    for q, text in items:
        k = frag_key(text)
        frag = os.path.join(FRAG_DIR, k + ".mp3")
        dest = os.path.join(ROOT, q["audio"])
        if not os.path.isfile(frag):
            continue
        if course_entry.get(q["audio"]) == k and os.path.isfile(dest):
            skipped += 1
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        run_ffmpeg(["-i", frag, "-ar", "24000", "-ac", "1", "-b:a", BITRATE, dest],
                   cwd=FRAG_DIR)
        course_entry[q["audio"]] = k
        merged += 1
    print("  生成 %d 个，复用跳过 %d 个" % (merged, skipped))


def main():
    ensure_deps()
    setup_ffmpeg()
    print("代理设置: %s" % (PROXY if PROXY else "未使用（直连）"))
    if len(sys.argv) > 1:
        targets = [os.path.join(CONTENT_DIR, sys.argv[1].replace(".json", "") + ".json")]
    else:
        targets = sorted(os.path.join(CONTENT_DIR, f)
                         for f in os.listdir(CONTENT_DIR) if f.endswith(".json"))
    if not targets:
        print("content/speaking 下没有课程 JSON")
        return
    manifest = load_manifest()
    failures = []
    for t in targets:
        process_course(t, manifest, failures)
    save_manifest(manifest)
    if failures:
        print("\n⚠️ 以下条目失败，请重跑或检查：")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("\n全部完成。音频在 static/audio/speaking/，记得 commit + push。")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\n出错了：", e)
        print("常见原因同听力工具：代理未配置（tools/proxy.txt）或 edge-tts 需升级。")
        sys.exit(1)
