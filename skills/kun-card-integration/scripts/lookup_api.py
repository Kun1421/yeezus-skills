#!/usr/bin/env python3
"""从本地卡中心 OpenAPI 查询 path 或 schema 字段摘要。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPENAPI = ROOT / "references" / "openapi" / "卡中心.openapi.json"


def load() -> dict:
    if not OPENAPI.exists():
        sys.exit(f"OpenAPI not found: {OPENAPI}")
    return json.loads(OPENAPI.read_text(encoding="utf-8"))


def resolve(schemas: dict, schema: dict) -> dict:
    if "$ref" in schema:
        return schemas.get(schema["$ref"].split("/")[-1], {})
    return schema


def print_schema(schemas: dict, name: str, depth: int = 0) -> None:
    schema = schemas.get(name)
    if not schema:
        print(f"schema not found: {name}")
        return
    req = set(schema.get("required") or [])
    props = schema.get("properties") or {}
    print(f"schema: {name}  (required marked *)")
    for k, v in props.items():
        v = resolve(schemas, v) if "$ref" in v else v
        mark = "*" if k in req else " "
        typ = v.get("type") or (
            "ref:" + v["$ref"].split("/")[-1] if "$ref" in v else "object"
        )
        if "$ref" in (schema.get("properties") or {}).get(k, {}):
            typ = "ref:" + schema["properties"][k]["$ref"].split("/")[-1]
        desc = (v.get("description") or "").replace("\n", " ")[:100]
        print(f"  {mark} {k}: {typ} — {desc}")


def print_path(data: dict, path: str) -> None:
    item = data.get("paths", {}).get(path)
    if not item:
        # fuzzy
        hits = [p for p in data.get("paths", {}) if path in p]
        if not hits:
            sys.exit(f"path not found: {path}")
        print("fuzzy matches:")
        for h in hits:
            print(" ", h)
        return
    for method, spec in item.items():
        if method.startswith("x-"):
            continue
        print(f"{method.upper()} {path}")
        print(f"  summary: {spec.get('summary')}")
        print(f"  tags: {spec.get('tags')}")
        desc = (spec.get("description") or "").strip()
        if desc:
            print(f"  description: {desc[:300]}")
        rb = (spec.get("requestBody") or {}).get("content") or {}
        for ct, body in rb.items():
            sch = body.get("schema") or {}
            if "$ref" in sch:
                name = sch["$ref"].split("/")[-1]
                print(f"  request ({ct}): {name}")
                print_schema(data.get("components", {}).get("schemas", {}), name)
            else:
                print(f"  request ({ct}): inline")
        codes = list((spec.get("responses") or {}).keys())
        print(f"  responses: {codes}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--path", help="API path, e.g. /rest/v2.0/api/common/openCard")
    ap.add_argument("--schema", help="components.schemas name")
    ap.add_argument("--list-paths", action="store_true")
    args = ap.parse_args()
    data = load()
    if args.list_paths:
        for p in sorted(data.get("paths", {})):
            print(p)
        return
    if args.path:
        print_path(data, args.path)
        return
    if args.schema:
        print_schema(data.get("components", {}).get("schemas", {}), args.schema)
        return
    ap.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
