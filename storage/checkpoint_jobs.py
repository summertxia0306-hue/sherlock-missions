"""One background private-draft writer per lesson, stable across app reruns.

The Streamlit entrypoint reloads storage.progress on every rerun. Keeping this
small queue in a separate module prevents that reload from losing in-flight
draft writes. It never calls Streamlit or touches formal results.
"""
import threading


_lock = threading.Lock()
local_lock = threading.Lock()
_jobs = {}


def submit(key, payload, writer):
    """Replace queued work with the latest snapshot; never block on network."""
    with _lock:
        job = _jobs.get(key)
        if job is None:
            job = {"payload": payload, "writer": writer,
                   "active": False, "status": "pending"}
            _jobs[key] = job
        else:
            job.update(payload=payload, writer=writer, status="pending")
        if job["active"]:
            return
        job["active"] = True
    threading.Thread(target=_run, args=(key,), daemon=True,
                     name="speaking-draft-sync").start()


def status(key):
    with _lock:
        job = _jobs.get(key)
        return job["status"] if job else None


def _run(key):
    while True:
        with _lock:
            job = _jobs[key]
            payload, writer = job["payload"], job["writer"]
        try:
            success = bool(writer(payload))
        except Exception:
            success = False
        with _lock:
            job = _jobs[key]
            if job["payload"] is payload:
                job["status"] = "synced" if success else "failed"
                job["active"] = False
                job["payload"] = None
                job["writer"] = None
                return
