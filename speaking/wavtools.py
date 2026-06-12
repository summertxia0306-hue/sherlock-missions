# -*- coding: utf-8 -*-
"""wav → 讯飞要求的 16kHz/16bit/单声道 PCM。纯标准库（不依赖 numpy/audioop，
audioop 在 Python 3.13 已移除，云端 Python 版本不受我们控制）。

st.audio_input 返回 wav，但采样率/声道数随浏览器与设备而异（iPad Safari
常见 44.1k/48k），必须在服务端统一转码后再送评测。
"""
import io
import struct
import wave
from array import array


class WavError(Exception):
    pass


def wav_info(wav_bytes):
    """→ (声道数, 采样宽度bytes, 采样率, 时长秒)。非法 wav 抛 WavError。"""
    try:
        with wave.open(io.BytesIO(wav_bytes)) as w:
            nch, sw, rate, nframes = (w.getnchannels(), w.getsampwidth(),
                                      w.getframerate(), w.getnframes())
        return nch, sw, rate, (nframes / float(rate) if rate else 0.0)
    except Exception as e:
        raise WavError("无法解析 wav：%r" % e)


def to_pcm16k(wav_bytes, target_rate=16000):
    """→ (pcm bytes, 原始信息 dict)。流程：解析→统一16bit→混单声道→线性重采样。"""
    try:
        with wave.open(io.BytesIO(wav_bytes)) as w:
            nch, sw, rate = w.getnchannels(), w.getsampwidth(), w.getframerate()
            raw = w.readframes(w.getnframes())
    except Exception as e:
        raise WavError("无法解析 wav：%r" % e)
    if nch < 1 or rate <= 0:
        raise WavError("wav 头异常（声道=%s 采样率=%s）" % (nch, rate))

    # → 16bit 有符号样本序列
    if sw == 2:
        samples = array("h")
        samples.frombytes(raw[: len(raw) - (len(raw) % 2)])
    elif sw == 1:  # 8bit 无符号
        samples = array("h", ((b - 128) << 8 for b in raw))
    elif sw == 4:  # 32bit 有符号
        n = len(raw) // 4
        ints = struct.unpack("<%di" % n, raw[: n * 4])
        samples = array("h", (v >> 16 for v in ints))
    else:
        raise WavError("不支持的采样宽度：%d 字节" % sw)

    # 多声道 → 平均混成单声道
    if nch > 1:
        usable = len(samples) - (len(samples) % nch)
        mono = array("h", (sum(samples[i:i + nch]) // nch
                           for i in range(0, usable, nch)))
    else:
        mono = samples
    if not len(mono):
        raise WavError("音频为空")

    # 线性插值重采样 → target_rate
    if rate == target_rate:
        out = mono
    else:
        ratio = rate / float(target_rate)
        n_out = max(1, int(len(mono) / ratio))
        out = array("h", bytes(2 * n_out))
        last = len(mono) - 1
        for i in range(n_out):
            pos = i * ratio
            j = int(pos)
            if j >= last:
                out[i] = mono[last]
            else:
                frac = pos - j
                out[i] = int(mono[j] * (1 - frac) + mono[j + 1] * frac)

    info = {"channels": nch, "sampwidth": sw, "rate": rate,
            "duration": round(len(mono) / float(rate), 2)}
    return out.tobytes(), info
