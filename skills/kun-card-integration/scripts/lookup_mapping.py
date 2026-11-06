#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按旧 VCC path / 关键字查询新旧接口对照（references/迁移/vcc/mapping.yaml）。

不查询 CAAS。旧 /rest/v1.0/caas/* 见 references/迁移/caas/迁移总览.md。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("need PyYAML: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "references" / "迁移" / "vcc" / "mapping.yaml"


def load_entries():
    data = yaml.safe_load(MAPPING.read_text(encoding="utf-8"))
    return data.get("entries") or []


def match(entry: dict, q: str) -> bool:
    q = q.lower().strip()
    if entry.get("id", "").lower() == q:
        return True
    old = entry.get("old") or {}
    new = entry.get("new") or {}
    blob = " ".join(
        [
            entry.get("id", ""),
            str(old.get("path") or ""),
            str(new.get("path") or ""),
            " ".join(entry.get("notes") or []),
        ]
    ).lower()
    return q in blob


def fmt(entry: dict) -> str:
    old = entry.get("old")
    new = entry.get("new")
    lines = [
        f"id: {entry.get('id')}",
        f"domain: {entry.get('domain')}",
        f"status: {entry.get('status')}",
    ]
    if old:
        lines.append(f"old: {old.get('method')} {old.get('path')}")
    else:
        lines.append("old: (none)")
    if entry.get("status") == "split":
        for s in entry.get("split_to") or []:
            lines.append(f"new[{s.get('use')}]: {s.get('method')} {s.get('path')}")
    elif new:
        if new.get("kind") == "webhook":
            lines.append(f"new: webhook → {new.get('ref')}")
        else:
            lines.append(f"new: {new.get('method')} {new.get('path')}")
    else:
        lines.append("new: (pending / none)")
    for n in entry.get("notes") or []:
        lines.append(f"note: {n}")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(description="Lookup legacy VCC → new API mapping (not CAAS)")
    p.add_argument("query", nargs="?", help="old path fragment / id / keyword")
    p.add_argument(
        "--list-pending",
        action="store_true",
        help="list pending_add / split / partial / gap / new_only",
    )
    args = p.parse_args()
    entries = load_entries()
    if args.list_pending:
        for e in entries:
            if e.get("status") in ("pending_add", "split", "partial", "gap", "new_only"):
                print(fmt(e))
                print("---")
        return
    if not args.query:
        p.print_help()
        sys.exit(2)
    hits = [e for e in entries if match(e, args.query)]
    if not hits:
        print("no match")
        sys.exit(1)
    for e in hits:
        print(fmt(e))
        print("---")


if __name__ == "__main__":
    main()
