import base64
import json
import math
import os
from typing import Any, Dict, List
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

app = FastAPI(title="Adaptive API Gateway", version="3.0")


# ---------- 辅助工具函数 ----------

def safe_int(val: Any, default: int = 0) -> int:
    """安全转换为 int，兼容 "120" 或 120.0"""
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def safe_float(val: Any, default: float = 0.0) -> float:
    """安全转换为 float"""
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def calculate_p95(latencies: List[int]) -> int:
    """
    兼顾 Nearest-Rank 与 Percentile 边界的 P95 计算
    """
    n = len(latencies)
    if n == 0:
        return 0
    if n == 1:
        return latencies[0]

    # 排序
    sorted_lat = sorted(latencies)
    
    # 标准 Nearest-Rank 公式: rank = ceil(0.95 * N)
    # 映射到 0-based index: index = ceil(0.95 * N) - 1
    idx = math.ceil(0.95 * n) - 1
    clamped_idx = max(0, min(idx, n - 1))
    
    return sorted_lat[clamped_idx]


# ---------- 核心业务处理 ----------

def process_adapt_input(adapt_input: Any) -> Dict[str, Any]:
    if not isinstance(adapt_input, dict):
        adapt_input = {}

    user = adapt_input.get("user")
    if not isinstance(user, dict):
        user = {}

    metadata = adapt_input.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    # 1. Action 处理: 强制转小写，若缺失则为空字符串
    raw_action = adapt_input.get("action")
    action_str = str(raw_action).strip().lower() if raw_action is not None else ""

    # 2. Priority 映射: HIGH->3, MEDIUM->2, LOW->1, 其他->0
    priority_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    raw_priority = str(metadata.get("priority", "")).strip().upper()
    priority_val = priority_map.get(raw_priority, 0)

    # 3. User 字段提取: 保证键存在，缺失则为 None (对应 JSON null)
    user_id = user.get("id")
    full_name = user.get("fullName")

    return {
        "id": str(user_id) if user_id is not None else None,
        "name": str(full_name) if full_name is not None else None,
        "action": action_str,
        "priority": priority_val
    }


def process_slo_output(heartbeats: Any, slo_query: Any) -> Dict[str, Any]:
    if not isinstance(slo_query, dict):
        slo_query = {}
    if not isinstance(heartbeats, list):
        heartbeats = []

    target_service = str(slo_query.get("service", "")).strip()
    since_ts = safe_float(slo_query.get("since", 0))

    # 过滤符合条件的心跳包
    relevant = []
    for hb in heartbeats:
        if isinstance(hb, dict):
            hb_service = str(hb.get("service", "")).strip()
            # 只有 service 匹配且 timestamp >= since 才纳入统计
            if hb_service == target_service:
                hb_ts = safe_float(hb.get("timestamp", 0))
                if hb_ts >= since_ts:
                    relevant.append(hb)

    total = len(relevant)
    if total == 0:
        return {
            "availability": 0.0,
            "p95LatencyMs": 0
        }

    # 计算 Availability 与 提取 Latency
    ok_count = 0
    latencies = []
    for hb in relevant:
        status_str = str(hb.get("status", "")).strip().upper()
        if status_str == "OK":
            ok_count += 1
        latencies.append(safe_int(hb.get("latencyMs", 0)))

    # 可用率计算
    availability = ok_count / total
    
    # P95 延迟计算
    p95_val = calculate_p95(latencies)

    return {
        "availability": round(availability, 4),
        "p95LatencyMs": p95_val
    }


# ---------- API 路由 (全手动防御) ----------

@app.post("/solve")
async def solve(request: Request):
    try:
        # 1. 尝试解析请求体 JSON
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid JSON body"}
            )

        if not isinstance(body, dict) or "payload" not in body:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Missing payload field"}
            )

        raw_payload = body.get("payload")
        if not isinstance(raw_payload, str):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Payload must be a string"}
            )

        # 2. 清洗 Base64 字符串（去除换行、空格）
        clean_payload = raw_payload.strip().replace("\n", "").replace("\r", "").replace(" ", "")

        # 3. 自动补齐 Base64 Padding
        missing_padding = len(clean_payload) % 4
        if missing_padding:
            clean_payload += "=" * (4 - missing_padding)

        # 4. Base64 解码 & JSON 解析
        try:
            decoded_bytes = base64.b64decode(clean_payload)
            decoded_str = decoded_bytes.decode("utf-8")
            payload_json = json.loads(decoded_str)
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Malformed base64 or internal JSON"}
            )

        if not isinstance(payload_json, dict):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Decoded payload is not a JSON object"}
            )

        # 5. 执行核心逻辑
        adapt_input = payload_json.get("adaptInput")
        heartbeats = payload_json.get("heartbeats")
        slo_query = payload_json.get("sloQuery")

        adapt_out = process_adapt_input(adapt_input)
        slo_out = process_slo_output(heartbeats, slo_query)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "adaptOutput": adapt_out,
                "sloOutput": slo_out
            }
        )

    except Exception as e:
        # 捕获所有未知的兜底异常，绝不崩溃返回 500
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Unhandled request processing error"}
        )


# ---------- Root & Health Check Endpoints ----------

@app.get("/")
async def root():
    return {"message": "Adaptive API Gateway is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
