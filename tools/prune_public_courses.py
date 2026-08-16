# -*- coding: utf-8 -*-
"""Prune reproducible public course assets while preserving learner evidence."""
import argparse
import json
import os
import re
import shutil


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COURSE_RE = re.compile(r"^(W|S)01D(\d{2})$")
MIN_KEEP = 39


def _inside(path, parent):
    path = os.path.realpath(path)
    parent = os.path.realpath(parent)
    return os.path.commonpath([path, parent]) == parent


def _course_number(name, prefix):
    stem = os.path.splitext(name)[0]
    match = COURSE_RE.match(stem)
    if not match or match.group(1) != prefix:
        return None
    return int(match.group(2))


def collect_targets():
    targets = []
    roots = (
        (os.path.join(ROOT, "content", "listening"), "W", "file"),
        (os.path.join(ROOT, "content", "speaking"), "S", "file"),
        (os.path.join(ROOT, "static", "audio", "listening"), "W", "dir"),
        (os.path.join(ROOT, "static", "audio", "speaking"), "S", "dir"),
    )
    for parent, prefix, kind in roots:
        for name in sorted(os.listdir(parent)):
            number = _course_number(name, prefix)
            if number is not None and number < MIN_KEEP:
                path = os.path.join(parent, name)
                if not _inside(path, parent):
                    raise RuntimeError("unsafe prune target: %s" % path)
                if kind == "file" and os.path.isfile(path):
                    targets.append((kind, path))
                elif kind == "dir" and os.path.isdir(path):
                    targets.append((kind, path))
    for module in ("listening", "speaking"):
        parent = os.path.join(ROOT, "static", "audio", module)
        path = os.path.join(parent, "fragments")
        if os.path.isdir(path):
            if not _inside(path, parent):
                raise RuntimeError("unsafe fragment target: %s" % path)
            targets.append(("dir", path))
    return targets


def prune_manifest(module, apply_changes):
    path = os.path.join(ROOT, "static", "audio", module, "manifest.json")
    with open(path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    prefix = "W" if module == "listening" else "S"
    kept = {}
    for course_id, entry in manifest.get("courses", {}).items():
        number = _course_number(course_id, prefix)
        if number is not None and number >= MIN_KEEP:
            kept[course_id] = entry
    print("manifest %-9s courses %d -> %d; fragment cache -> 0"
          % (module, len(manifest.get("courses", {})), len(kept)))
    if apply_changes:
        manifest["courses"] = kept
        manifest["fragments"] = {}
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=1)
            fh.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    targets = collect_targets()
    print("mode:", "APPLY" if args.apply else "DRY RUN")
    print("public targets:", len(targets))
    for kind, path in targets:
        print("  %s %s" % (kind, os.path.relpath(path, ROOT)))
    prune_manifest("listening", args.apply)
    prune_manifest("speaking", args.apply)
    if not args.apply:
        print("dry run only; pass --apply to prune")
        return
    for kind, path in targets:
        if kind == "file":
            os.remove(path)
        else:
            shutil.rmtree(path)
    print("prune complete; learner results and recordings were not accessed")


if __name__ == "__main__":
    main()
