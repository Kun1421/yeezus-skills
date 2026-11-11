#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""授权 Webhook 可落地表样（Flask）。

职责：HMAC-SHA256 v1 验签 → 幂等 → 返回 authResult=A/D。
验签实现见同目录 webhook_hmac_v1.py；生产请将内存幂等替换为 DB 唯一约束。
"""
from __future__ import annotations

import os

from flask import Flask, jsonify, request

from webhook_hmac_v1 import HEADER_SIGNATURE, HEADER_TIMESTAMP, verify_from_headers

app = Flask(__name__)

# 演示用：生产用 Redis/DB
_DECISION_STORE: dict[str, str] = {}

WEBHOOK_SIGN_KEY = os.getenv("KUN_WEBHOOK_SIGN_KEY", "YOUR_WEBHOOK_SIGN_KEY")
# 未配置签名开关时平台可能不带头；生产若已开签建议保持 True
REQUIRE_SIGNATURE = os.getenv("KUN_WEBHOOK_REQUIRE_SIGNATURE", "1") not in ("0", "false", "False")


def decide(payload: dict) -> str:
    """业务决策：返回 A 或 D。此处示例：金额过大则拒绝。"""
    amount = payload.get("transactionAmount") or 0
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return "D"
    return "A" if amount <= 5000 else "D"


@app.post("/hooks/kun/auth")
def auth_webhook():
    raw = request.get_data()  # 原文 bytes，禁止先 get_json 再 dumps
    headers = {
        HEADER_TIMESTAMP: request.headers.get(HEADER_TIMESTAMP),
        HEADER_SIGNATURE: request.headers.get(HEADER_SIGNATURE),
    }

    has_sig_headers = bool(headers[HEADER_TIMESTAMP] and headers[HEADER_SIGNATURE])
    if REQUIRE_SIGNATURE or has_sig_headers:
        result = verify_from_headers(WEBHOOK_SIGN_KEY, headers, raw, tolerance_seconds=300)
        if not result.ok:
            return jsonify({"code": "SIGN_ERROR", "message": result.reason}), 401

    payload = request.get_json(force=True, silent=True) or {}
    webhook_type = payload.get("webhookType") or ""
    tx_id = payload.get("transactionId") or ""
    if not tx_id and webhook_type in ("", "AUTH_WEBHOOK"):
        return jsonify({"code": "BAD_REQUEST", "message": "missing transactionId"}), 400

    # 非授权类：异步通知可快速 200 + 异步处理
    if webhook_type and webhook_type != "AUTH_WEBHOOK":
        # TODO: 入队处理清算/OTP/卡状态等
        return jsonify({"code": "0000", "message": "ok"})

    # 幂等：已决策则原样返回
    if tx_id in _DECISION_STORE:
        auth_result = _DECISION_STORE[tx_id]
    else:
        auth_result = decide(payload)
        _DECISION_STORE[tx_id] = auth_result

    return jsonify(
        {
            "requestNo": payload.get("requestNo"),
            "code": "0000",
            "message": "ok",
            "authResult": auth_result,  # A 批准 / D 拒绝
            "declinedReason": None if auth_result == "A" else "LIMIT_EXCEEDED",
        }
    )


if __name__ == "__main__":
    # pip install flask
    # export KUN_WEBHOOK_SIGN_KEY='你的签名密钥'
    app.run(host="0.0.0.0", port=8088)
