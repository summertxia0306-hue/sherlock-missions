# -*- coding: utf-8 -*-
"""听力音频生成工具 v2（开发期在家长 PC 运行，不在线上跑）。

变化（对照旧 make_audio.py）：
- 输入从"扫 HTML 台词"改为"读课程 JSON 的 transcript 字段"，杜绝误配音界面文案
- 输出从"base64 内嵌 HTML"改为"独立 MP3 + 清单"
- 分角色片段按 sha1(role|text|rate) 命名 → 跨课程自动复用，只生成缺失项
- 每题把片段 + 0.6s 停顿合成一个成品 MP3（设计决策A），路径以 JSON 的 audio 字段为准
- manifest.json 记录片段与成品的对应关系，归档课程的音频可据此人工清理

用法：
  python tools/make_audio_v2.py                    # 处理 content/listening 下全部课程
  python tools/make_audio_v2.py W01D01             # 只处理指定课程
依赖（首次自动安装）：edge-tts, imageio-ffmpeg（拼接直接用 ffmpeg，无 pydub）
"""
import asyncio
import hashlib
import json
import os
import subprocess
import sys

VOICES = {"n": "en-US-AnaNeural", "f": "en-US-AriaNeural", "m": "en-US-GuyNeural"}
RATE = "-10%"          # 约0.9倍速，与旧配音版一致


def get_proxy():
    """代理来源（按优先级）：环境变量 HTTPS_PROXY/HTTP_PROXY → tools/proxy.txt。

    如果你浏览器靠代理上网，Python 默认不走代理会连不上微软语音服务器。
    在 tools/ 下新建 proxy.txt，写一行代理地址即可，例如：http://127.0.0.1:7890
    """
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
GAP_MS = 600           # 片段间停顿
BITRATE = "64k"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_ROOT = os.path.join(ROOT, "static", "audio", "listening")
FRAG_DIR = os.path.join(AUDIO_ROOT, "fragments")
MANIFEST_PATH = os.path.join(AUDIO_ROOT, "manifest.json")
CONTENT_DIR = os.path.join(ROOT, "content", "listening")


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


FFMPEG = None


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


def ensure_silence():
    """生成 0.6s 静音片段（与 edge-tts 输出同为 24kHz 单声道）。"""
    path = os.path.join(FRAG_DIR, "_silence.mp3")
    if not os.path.isfile(path):
        run_ffmpeg(["-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                    "-t", "%.2f" % (GAP_MS / 1000.0), "-b:a", BITRATE, path])
    return path


def frag_key(role, text):
    return hashlib.sha1(("%s|%s|%s" % (role, text, RATE)).encode("utf-8")).hexdigest()[:16]


def load_manifest():
    if os.path.isfile(MANIFEST_PATH):
        with open(MANIFEST_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    return {"fragments": {}, "courses": {}}


def save_manifest(m):
    os.makedirs(AUDIO_ROOT, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)


def collect_items(course):
    """course JSON → [{label, out_rel, clips:[[role,text],...]}]"""
    items = []
    if course.get("test_audio") and course.get("test_transcript"):
        items.append({"label": "试音", "out_rel": course["test_audio"],
                      "clips": course["test_transcript"]})
    for sec in course["sections"]:
        if sec.get("shared_audio"):
            items.append({"label": "%s短文" % sec["name"], "out_rel": sec["passage_audio"],
                          "clips": sec["passage_transcript"]})
        for q in sec["questions"]:
            if q["type"] == "passage_judge":
                continue
            items.append({"label": "Q%s" % q["id"], "out_rel": q["audio"],
                          "clips": q["transcript"]})
    return items


async def synth_fragment(role, text, dest):
    import edge_tts
    com = edge_tts.Communicate(text, VOICES[role], rate=RATE, proxy=PROXY)
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


async def ensure_fragments(items, manifest, failures):
    os.makedirs(FRAG_DIR, exist_ok=True)
    todo = {}
    for it in items:
        for role, text in it["clips"]:
            k = frag_key(role, text)
            path = os.path.join(FRAG_DIR, k + ".mp3")
            if not os.path.isfile(path):
                todo[k] = (role, text, path, it["label"])
            manifest["fragments"][k] = {"role": role, "voice": VOICES[role],
                                        "rate": RATE, "text": text}
    if todo:
        print("需生成片段 %d 个：" % len(todo))
    for i, (k, (role, text, path, label)) in enumerate(sorted(todo.items()), 1):
        print("  [%d/%d] %s %s: %s" % (i, len(todo), label, VOICES[role], text[:50]))
        for attempt in range(3):
            try:
                await synth_fragment(role, text, path)
                break
            except Exception as e:
                if attempt == 2:
                    failures.append("%s | %s | %s" % (label, text, e))
                else:
                    print("    重试(%d): %s" % (attempt + 1, e))
                    await asyncio.sleep(2)


def merge_item(item):
    """片段 + 静音 → 成品单 MP3。直接用 ffmpeg concat，无 pydub/ffprobe 依赖。

    列表文件只写文件名（cwd=FRAG_DIR），避开中文路径的编码坑。
    """
    missing = [t for r, t in item["clips"]
               if not os.path.isfile(os.path.join(FRAG_DIR, frag_key(r, t) + ".mp3"))]
    if missing:
        raise RuntimeError("片段缺失（上一步生成失败）: %s" % missing[0][:40])
    dest = os.path.join(ROOT, item["out_rel"])
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    names = []
    for i, (role, text) in enumerate(item["clips"]):
        if i:
            names.append("_silence.mp3")
        names.append(frag_key(role, text) + ".mp3")

    if len(names) == 1:
        run_ffmpeg(["-i", names[0], "-ar", "24000", "-ac", "1",
                    "-b:a", BITRATE, dest], cwd=FRAG_DIR)
        return
    ensure_silence()
    listfile = os.path.join(FRAG_DIR, "_concat.txt")
    with open(listfile, "w", encoding="utf-8") as fh:
        for n in names:
            fh.write("file '%s'\n" % n)
    try:
        run_ffmpeg(["-f", "concat", "-safe", "0", "-i", "_concat.txt",
                    "-ar", "24000", "-ac", "1", "-b:a", BITRATE, dest],
                   cwd=FRAG_DIR)
    finally:
        try:
            os.remove(listfile)
        except OSError:
            pass


def content_hash(item):
    return hashlib.sha1((json.dumps(item["clips"], ensure_ascii=False) + RATE)
                        .encode("utf-8")).hexdigest()[:16]


def process_course(path, manifest, failures):
    with open(path, encoding="utf-8") as fh:
        course = json.load(fh)

    sys.path.insert(0, ROOT)
    from listening import models
    errors = models.validate_course(course, check_audio=False)
    if errors:
        print("课程 %s JSON 校验失败，跳过：" % course.get("course_id"))
        for e in errors:
            print("  -", e)
        failures.append("%s JSON 校验失败" % path)
        return

    cid = course["course_id"]
    items = collect_items(course)
    print("课程 %s：%d 个音频目标" % (cid, len(items)))

    asyncio.run(ensure_fragments(items, manifest, failures))

    course_entry = manifest["courses"].setdefault(cid, {})
    merged = skipped = 0
    for it in items:
        h = content_hash(it)
        dest = os.path.join(ROOT, it["out_rel"])
        if course_entry.get(it["out_rel"]) == h and os.path.isfile(dest):
            skipped += 1
            continue
        try:
            merge_item(it)
            course_entry[it["out_rel"]] = h
            merged += 1
        except Exception as e:
            failures.append("%s %s 合成失败: %s" % (cid, it["label"], e))
    print("  合成 %d 个，复用跳过 %d 个" % (merged, skipped))


def main():
    ensure_deps()
    setup_ffmpeg()
    print("代理设置: %s" % (PROXY if PROXY else "未使用（直连）"))
    targets = []
    if len(sys.argv) > 1:
        targets = [os.path.join(CONTENT_DIR, sys.argv[1].replace(".json", "") + ".json")]
    else:
        targets = sorted(os.path.join(CONTENT_DIR, f)
                         for f in os.listdir(CONTENT_DIR) if f.endswith(".json"))
    if not targets:
        print("content/listening 下没有课程 JSON")
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
    print("\n全部完成。音频在 static/audio/listening/，记得 commit + push 触发重新部署。")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\n出错了：", e)
        print("常见原因：")
        print(" 1) 连不上微软语音服务器（Cannot connect / DNS）：")
        print("    - 开着代理工具的话，在 tools/ 下新建 proxy.txt 写一行代理地址，")
        print("      如 http://127.0.0.1:7890（clash 默认端口），再重跑")
        print("    - 或把网络的 DNS 改为 223.5.5.5 后重跑")
        print(" 2) edge-tts 需升级: pip install -U edge-tts")
        sys.exit(1)
