#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KUN 开放平台轻量客户端（RSA SHA256withRSA）。

用途：沙箱/联调快速发已签名请求，帮助商户几分钟内跑通卡接口。
签名规则见：references/平台文档/鉴权认证机制.md

示例：
  python kun_client.py gen-key --out-dir ./keys
  python kun_client.py call --env sandbox \\
    --app-key APP_xxx --customer-no 100xxx \\
    --private-key ./keys/merchant_private.pem \\
    --path /rest/v2.0/api/common/cardBins \\
    --body '{"requestNo":"r1","secretKey":"sk","ip":"127.0.0.1"}'
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

GATEWAYS = {
    "sandbox": "https://sandbox.kun.global",
    "production": "https://openapi.kun.global",
}


def load_private_key(pem_path: str):
    raw = Path(pem_path).read_bytes()
    return serialization.load_pem_private_key(raw, password=None)


def value_for_sign(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def build_sign_string(params: dict[str, Any]) -> str:
    """顶级字段 + customerNo/timestamp；key 小写 ASCII 排序。"""
    items = []
    for k, v in params.items():
        if k is None or str(k).lower() == "sign":
            continue
        items.append((str(k).lower(), value_for_sign(v)))
    items.sort(key=lambda x: x[0])
    # 文档示例含 URL encode；对简单 ASCII 值 encode 后与原文一致
    return "&".join(f"{k}={quote(v, safe='')}" for k, v in items)


def sign_sha256_rsa(private_key, sign_string: str) -> str:
    sig = private_key.sign(
        sign_string.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(sig).decode("ascii")


def call_api(
    *,
    env: str,
    app_key: str,
    customer_no: str,
    private_key_path: str,
    path: str,
    body: dict[str, Any],
    api_version: str = "2",
    timeout: int = 30,
) -> requests.Response:
    if not path.startswith("/"):
        path = "/" + path
    base = GATEWAYS[env]
    url = base + path
    timestamp = str(int(time.time() * 1000))
    sign_params = dict(body)
    sign_params["customerNo"] = customer_no
    sign_params["timestamp"] = timestamp
    sign_string = build_sign_string(sign_params)
    private_key = load_private_key(private_key_path)
    signature = sign_sha256_rsa(private_key, sign_string)
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "App-Key": app_key,
        "Api-Version": api_version,
        "Customer-No": customer_no,
        "Timestamp": timestamp,
        "Sign": signature,
    }
    return requests.post(url, headers=headers, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), timeout=timeout)


def cmd_gen_key(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    (out_dir / "merchant_private.pem").write_bytes(priv)
    (out_dir / "merchant_public.pem").write_bytes(pub)
    print(f"wrote {out_dir / 'merchant_private.pem'}")
    print(f"wrote {out_dir / 'merchant_public.pem'}")
    print("请将公钥配置到开放平台应用；私钥仅本机使用，勿粘贴到聊天。")


def cmd_sign_string(body: dict, customer_no: str, timestamp: str | None) -> None:
    ts = timestamp or str(int(time.time() * 1000))
    params = dict(body)
    params["customerNo"] = customer_no
    params["timestamp"] = ts
    s = build_sign_string(params)
    print("timestamp:", ts)
    print("signString:")
    print(s)


def cmd_call(args: argparse.Namespace) -> int:
    body = json.loads(args.body) if args.body.startswith("{") else json.loads(Path(args.body).read_text(encoding="utf-8"))
    if args.dry_run:
        ts = str(int(time.time() * 1000))
        params = dict(body)
        params["customerNo"] = args.customer_no
        params["timestamp"] = ts
        print("dry-run signString:\n", build_sign_string(params))
        print("url:", GATEWAYS[args.env] + args.path)
        return 0
    resp = call_api(
        env=args.env,
        app_key=args.app_key,
        customer_no=args.customer_no,
        private_key_path=args.private_key,
        path=args.path,
        body=body,
        api_version=args.api_version,
    )
    print("HTTP", resp.status_code)
    for h in ("sign", "timestamp", "Sign", "Timestamp"):
        if h in resp.headers:
            print(f"resp-header {h}: {resp.headers[h]}")
    try:
        print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
    except Exception:
        print(resp.text)
    return 0 if resp.status_code < 500 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gen-key", help="生成联调用 RSA2048 密钥对")
    g.add_argument("--out-dir", default="./keys")

    s = sub.add_parser("sign-string", help="仅打印待签字符串（不发请求）")
    s.add_argument("--customer-no", required=True)
    s.add_argument("--body", required=True, help="JSON 字符串或文件路径")
    s.add_argument("--timestamp", default=None)

    c = sub.add_parser("call", help="签名并 POST")
    c.add_argument("--env", choices=sorted(GATEWAYS), default="sandbox")
    c.add_argument("--app-key", required=True)
    c.add_argument("--customer-no", required=True)
    c.add_argument("--private-key", required=True)
    c.add_argument("--path", required=True)
    c.add_argument("--body", required=True, help="JSON 字符串或 .json 文件路径")
    c.add_argument("--api-version", default="2")
    c.add_argument("--dry-run", action="store_true", help="只打印签名串与 URL，不发请求")

    args = ap.parse_args()
    if args.cmd == "gen-key":
        cmd_gen_key(Path(args.out_dir))
        return 0
    if args.cmd == "sign-string":
        body = json.loads(args.body) if args.body.strip().startswith("{") else json.loads(Path(args.body).read_text(encoding="utf-8"))
        cmd_sign_string(body, args.customer_no, args.timestamp)
        return 0
    if args.cmd == "call":
        return cmd_call(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
