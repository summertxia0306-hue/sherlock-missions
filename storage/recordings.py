# -*- coding: utf-8 -*-
"""口语录音箱接口占位（实现归 Codex 统一架构，本模块不实现）。

约定（见迁移指令 §4.2）：
- save_recording(student_id, course_id, wav_bytes) -> recording_id（随机名，不含真实姓名）
- list_pending() -> [{recording_id, course_id, created_at}]
- accept_and_delete(recording_id)  家长验收后立即删除
- purge_older_than(hours=24)       启动/家长打开录音箱时清理
- 录音只存运行目录，不进 GitHub；平台重启可能丢失，丢失仍算完成。
"""


def save_recording(student_id, course_id, wav_bytes):
    raise NotImplementedError("口语录音箱由统一架构（Codex）实现")


def list_pending():
    return []


def accept_and_delete(recording_id):
    raise NotImplementedError


def purge_older_than(hours=24):
    return 0
