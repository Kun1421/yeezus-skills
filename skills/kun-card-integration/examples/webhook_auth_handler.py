#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""授权 Webhook 可落地表样（Flask）。

职责：验签（按你配置的 webhook 签名密钥实现）→ 幂等 → 返回 authResult=A/D。
生产请替换内存幂等为 DB 唯一约束；验签算法以开放文档「结果通知/Webhook」为准。
"""
from __future__ import annotations

import hashlib
import hmac
import os
from flask import Flask, jsonify, request

app = Flask(__name__)

# 演示用：生产用 Redis/DB
_DECISION_STORE: dict[str, str] = {}

WEBHOOK_SIGN_KEY = os.getenv("KUN_WEBHOOK_SIGN_KEY", "YOUR_WEBHOOK_SIGN_KEY")


def verify_signature(raw_body: bytes, signature: str | None) -> bool:
    """占位验签：请按 opendocs 结果通知章节替换为平台约定算法。"""
    if not signature:
        return False
    digest = hmac.new(WEBHOOK_SIGN_KEY.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)


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
    raw = request.get_data()
    sig = request.headers.get("Sign") or request.headers.get("sign")
    if not verify_signature(raw, sig):
        return jsonify({"code": "SIGN_ERROR", "message": "invalid signature"}), 401

    payload = request.get_json(force=True, silent=True) or {}
    webhook_type = payload.get("webhookType") or ""
    tx_id = payload.get("transactionId") or ""
    if not tx_id:
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
    app.run(host="0.0.0.0", port=8088)
