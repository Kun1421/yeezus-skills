#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""商务卡 · 预付虚拟卡 · 可落地流程示例。

覆盖：签名调用、平台 code 校验、开卡业务状态判断、PENDING 查单、异常分类。
请将 YOUR_* 换成沙箱凭证；上生产前接入真实 DB 幂等与定时补偿。
"""
from __future__ import annotations

import os
import sys
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# 复用 skill 内联调客户端
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from kun_client import call_api  # noqa: E402


class LocalOpenCardState(str, Enum):
    CREATED = "CREATED"
    ACCEPTING = "ACCEPTING"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


TERMINAL = {LocalOpenCardState.SUCCESS, LocalOpenCardState.FAIL}


@dataclass
class Config:
    env: str = os.getenv("KUN_ENV", "sandbox")
    app_key: str = os.getenv("KUN_APP_KEY", "YOUR_APP_KEY")
    customer_no: str = os.getenv("KUN_CUSTOMER_NO", "YOUR_CUSTOMER_NO")
    secret_key: str = os.getenv("KUN_SECRET_KEY", "YOUR_SECRET_KEY")
    private_key: str = os.getenv("KUN_PRIVATE_KEY", "./keys/merchant_private.pem")
    card_product_code: str = os.getenv("KUN_CARD_PRODUCT_CODE", "")  # 空则先 cardBins


class KunApiError(Exception):
    """平台层失败（签名、参数、HTTP 等）。"""

    def __init__(self, message: str, *, code: str | None = None, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class BusinessPending(Exception):
    """业务处理中，应查单而非重开。"""

    def __init__(self, order_id: str | None, status: str):
        super().__init__(f"business pending: {status}")
        self.order_id = order_id
        self.status = status


def new_request_no(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:24]}"


def post(cfg: Config, path: str, body: dict[str, Any]) -> dict[str, Any]:
    """发送请求：区分超时未知 vs 明确失败。"""
    try:
        resp = call_api(
            env=cfg.env,
            app_key=cfg.app_key,
            customer_no=cfg.customer_no,
            private_key_path=cfg.private_key,
            path=path,
            body=body,
        )
    except Exception as e:  # 网络超时等
        raise KunApiError(f"transport error: {e}", retryable=True) from e

    if resp.status_code >= 500:
        raise KunApiError(f"HTTP {resp.status_code}", retryable=True)
    if resp.status_code >= 400:
        raise KunApiError(f"HTTP {resp.status_code}: {resp.text[:200]}", retryable=False)

    try:
        payload = resp.json()
    except Exception as e:
        raise KunApiError(f"invalid json: {e}", retryable=True) from e

    # 建议生产启用响应验签（见鉴权文档）；此处略
    code = str(payload.get("code", ""))
    if code and code not in ("0000", "0", "SUCCESS"):
        # 明确业务/平台拒绝：不可用同 requestNo 盲重试写操作
        raise KunApiError(
            f"platform code={code} message={payload.get('message')}",
            code=code,
            retryable=False,
        )
    return payload


def map_open_card_status(raw: Optional[str]) -> LocalOpenCardState:
    if raw is None:
        return LocalOpenCardState.UNKNOWN
    u = raw.upper()
    if u == "SUCCESS":
        return LocalOpenCardState.SUCCESS
    if u == "FAIL":
        return LocalOpenCardState.FAIL
    if u == "PENDING":
        return LocalOpenCardState.PENDING
    return LocalOpenCardState.UNKNOWN


def list_commercial_virtual_products(cfg: Config) -> list[dict[str, Any]]:
    body = {
        "requestNo": new_request_no("bins"),
        "secretKey": cfg.secret_key,
        "ip": "127.0.0.1",
    }
    data = post(cfg, "/rest/v2.0/api/common/cardBins", body).get("data") or []
    out = []
    for p in data:
        if p.get("cardScene") != "COMMERCIAL":
            continue
        types = (p.get("supportedCardTypes") or "V").upper()
        if "V" not in types:
            continue
        out.append(p)
    return out


def add_cardholder(cfg: Config, *, first_name: str, last_name: str, email: str) -> str:
    body = {
        "requestNo": new_request_no("ch"),
        "secretKey": cfg.secret_key,
        "firstName": first_name,
        "lastName": last_name,
        "email": email.strip().lower(),
    }
    data = post(cfg, "/rest/v2.0/caas/customer/commercial/add-cardholder", body).get("data") or {}
    customer_id = data.get("customerId")
    if not customer_id:
        raise KunApiError("missing customerId in response", retryable=False)
    return customer_id


def open_card_prepaid_virtual(
    cfg: Config, *, customer_id: str, card_product_code: str
) -> tuple[LocalOpenCardState, dict[str, Any]]:
    request_no = new_request_no("open")
    body = {
        "requestNo": request_no,
        "secretKey": cfg.secret_key,
        "ip": "127.0.0.1",
        "customerId": customer_id,
        "cardProductCode": card_product_code,
        "cardType": "V",
        "accountMode": 1,
    }
    # 生产：先 INSERT 本地单 CREATED(request_no) 再调用
    try:
        payload = post(cfg, "/rest/v2.0/api/common/openCard", body)
    except KunApiError as e:
        if e.retryable:
            # 未知：进入查单，不要直接再 open
            return LocalOpenCardState.UNKNOWN, {"requestNo": request_no, "error": str(e)}
        return LocalOpenCardState.FAIL, {"requestNo": request_no, "error": str(e), "code": e.code}

    data = payload.get("data") or {}
    state = map_open_card_status(data.get("openCardStatus"))
    data["requestNo"] = request_no
    return state, data


def query_open_card(cfg: Config, *, original_request_no: str) -> tuple[LocalOpenCardState, dict[str, Any]]:
    """开卡状态查询：必填 originalRequestNo（开卡时的 requestNo）。"""
    body: dict[str, Any] = {
        "requestNo": new_request_no("oq"),
        "secretKey": cfg.secret_key,
        "ip": "127.0.0.1",
        "originalRequestNo": original_request_no,
    }
    payload = post(cfg, "/rest/v2.0/api/common/openCardQuery", body)
    data = payload.get("data") or {}
    if isinstance(data, list) and data:
        data = data[0]
    status = data.get("openCardStatus") or data.get("status")
    return map_open_card_status(status), data


def wait_open_card_terminal(
    cfg: Config,
    *,
    original_request_no: str,
    max_attempts: int = 10,
    base_sleep: float = 2.0,
) -> tuple[LocalOpenCardState, dict[str, Any]]:
    """指数退避查单直到终态或次数用尽。"""
    last: dict[str, Any] = {}
    sleep = base_sleep
    for _ in range(max_attempts):
        state, last = query_open_card(cfg, original_request_no=original_request_no)
        if state in TERMINAL:
            return state, last
        time.sleep(sleep)
        sleep = min(sleep * 1.8, 30.0)
    return LocalOpenCardState.PENDING, last


def run_demo() -> None:
    cfg = Config()
    product_code = cfg.card_product_code
    if not product_code:
        products = list_commercial_virtual_products(cfg)
        if not products:
            raise SystemExit("no COMMERCIAL+V product; set KUN_CARD_PRODUCT_CODE")
        product_code = products[0]["cardProductCode"]
        print("picked product:", product_code, "modes:", products[0].get("supportedCardModes"))

    customer_id = add_cardholder(
        cfg, first_name="San", last_name="Zhang", email="demo.holder@example.com"
    )
    print("customerId:", customer_id)

    state, data = open_card_prepaid_virtual(
        cfg, customer_id=customer_id, card_product_code=product_code
    )
    print("open sync state:", state, "data keys:", list(data.keys()))

    if state in (LocalOpenCardState.PENDING, LocalOpenCardState.UNKNOWN):
        req_no = data.get("requestNo")
        if not req_no:
            raise SystemExit("missing requestNo for query")
        state, data = wait_open_card_terminal(cfg, original_request_no=req_no)
        print("after poll:", state)

    if state == LocalOpenCardState.SUCCESS:
        print("DONE cardId=", data.get("cardId"), "accountNo=", data.get("accountNo"))
    elif state == LocalOpenCardState.FAIL:
        print("FAIL — fix params then retry with NEW requestNo; do not reuse")
        raise SystemExit(2)
    else:
        print("STILL PENDING — schedule job to keep querying; do not re-open")
        raise SystemExit(3)


if __name__ == "__main__":
    run_demo()
