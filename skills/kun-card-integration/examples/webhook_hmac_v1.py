#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Webhook HMAC-SHA256 v1 验签工具（与平台出站签名一致）。

规则：
  signing_string = "{timestamp}.{rawBody}"
  signature      = lowercase_hex( HMAC_SHA256(secret_utf8, signing_string_utf8) )

请求头：
  X-Webhook-Timestamp  — epoch 秒
  X-Webhook-Signature  — 纯 hex，或 "v1=<hex>"

要点：rawBody 必须是 HTTP 请求体原文（UTF-8），不要 JSON 重排 / 再序列化。
密钥：技术参数「签名密钥」或 webhook-sign-key-config 配置的 signKey（UTF-8 字符串，常用 Base64）。
"""
from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Callable, Optional


HEADER_TIMESTAMP = "X-Webhook-Timestamp"
HEADER_SIGNATURE = "X-Webhook-Signature"
HEADER_WEBHOOK_TYPE = "X-Webhook-Type"


@dataclass(frozen=True)
class VerifyResult:
    ok: bool
    reason: str

    def to_dict(self) -> dict:
        return {"ok": self.ok, "reason": self.reason}


def sign_v1_hex(secret: str, timestamp_seconds: int, raw_body: str) -> str:
    """计算 v1 签名（小写 hex）。raw_body 不做 JSON 重排。"""
    if secret is None:
        raise ValueError("secret is required")
    if raw_body is None:
        raise ValueError("raw_body is required")
    signing_string = f"{timestamp_seconds}.{raw_body}"
    return hmac.new(
        secret.encode("utf-8"),
        signing_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _normalize_signature(signature_header_value: str) -> str:
    s = (signature_header_value or "").strip()
    if not s:
        return ""
    if "=" in s:
        prefix, val = s.split("=", 1)
        if prefix.strip().lower() != "v1":
            return ""
        s = val.strip()
    return s.replace(" ", "").lower()


def verify_v1_hex(
    secret: str,
    timestamp_seconds: int,
    raw_body: str,
    signature_header_value: str,
    tolerance_seconds: int = 300,
    event_id: Optional[str] = None,
    is_event_id_fresh: Optional[Callable[[str], bool]] = None,
) -> VerifyResult:
    """验签。支持纯 hex 或 v1=<hex>。建议 tolerance=300。"""
    if not secret:
        return VerifyResult(False, "missing_secret")
    if raw_body is None:
        return VerifyResult(False, "missing_body")
    if not signature_header_value:
        return VerifyResult(False, "missing_signature")
    if tolerance_seconds <= 0:
        tolerance_seconds = 300

    now = int(time.time())
    if abs(now - int(timestamp_seconds)) > tolerance_seconds:
        return VerifyResult(False, "timestamp_out_of_range")

    if is_event_id_fresh is not None:
        if not event_id:
            return VerifyResult(False, "missing_event_id")
        try:
            fresh = is_event_id_fresh(event_id)
        except Exception as e:  # noqa: BLE001 — 面客样例：捕获后映射 reason
            return VerifyResult(False, f"event_id_check_error:{type(e).__name__}")
        if not fresh:
            return VerifyResult(False, "duplicate_event_id")

    provided = _normalize_signature(signature_header_value)
    if not provided:
        return VerifyResult(False, "bad_signature_format")

    expected = sign_v1_hex(secret, int(timestamp_seconds), raw_body)
    if not hmac.compare_digest(expected, provided):
        return VerifyResult(False, "signature_mismatch")
    return VerifyResult(True, "ok")


def verify_from_headers(
    secret: str,
    headers: dict,
    raw_body: str | bytes,
    tolerance_seconds: int = 300,
    event_id: Optional[str] = None,
    is_event_id_fresh: Optional[Callable[[str], bool]] = None,
) -> VerifyResult:
    """从请求头字典验签。headers 的 key 大小写不敏感。"""
    lower = {str(k).lower(): v for k, v in (headers or {}).items()}
    ts_raw = lower.get(HEADER_TIMESTAMP.lower())
    sig = lower.get(HEADER_SIGNATURE.lower())
    if ts_raw is None or ts_raw == "":
        return VerifyResult(False, "missing_timestamp")
    try:
        ts = int(str(ts_raw).strip())
    except (TypeError, ValueError):
        return VerifyResult(False, "bad_timestamp")
    body = raw_body.decode("utf-8") if isinstance(raw_body, (bytes, bytearray)) else raw_body
    return verify_v1_hex(
        secret,
        ts,
        body,
        str(sig) if sig is not None else "",
        tolerance_seconds=tolerance_seconds,
        event_id=event_id,
        is_event_id_fresh=is_event_id_fresh,
    )


if __name__ == "__main__":
    # 自测：签名 → 验签 → 篡改应失败
    demo_secret = "G3Lkhz8BukEoCRky2zQIzSuE9iRh8e/68iJWWinOAu0="
    demo_ts = int(time.time())
    demo_body = '{"requestNo":"demo-1","webhookType":"AUTH_WEBHOOK","transactionId":"tx-1"}'
    sig = sign_v1_hex(demo_secret, demo_ts, demo_body)
    print("signature:", sig)
    print("verify ok:", verify_v1_hex(demo_secret, demo_ts, demo_body, sig, 300).to_dict())
    print(
        "verify tampered:",
        verify_v1_hex(demo_secret, demo_ts, demo_body.replace("tx-1", "tx-2"), sig, 300).to_dict(),
    )
    print(
        "verify headers:",
        verify_from_headers(
            demo_secret,
            {HEADER_TIMESTAMP: str(demo_ts), HEADER_SIGNATURE: sig},
            demo_body,
        ).to_dict(),
    )
