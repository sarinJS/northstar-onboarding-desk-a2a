"""Northstar Onboarding Desk -- minimal A2A 0.3 JSON-RPC service.

Fictional, read-only workshop example. No employees, hires or provisioning is changed.
Implements message/send and tasks/get over A2A 0.3 JSON-RPC (non-streaming).
"""
from __future__ import annotations

import hmac
import os
import re
import uuid
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route

CARD_NAME = "Northstar Onboarding Desk (Shared A2A)"
TASKS: OrderedDict[str, dict[str, Any]] = OrderedDict()
MAX_TASKS = 500


def base_url(request: Request) -> str:
    configured = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
    if configured:
        return configured
    hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
    if hostname:
        return "https://" + hostname
    return str(request.base_url).rstrip("/")


def agent_card(request: Request) -> dict[str, Any]:
    endpoint = base_url(request) + "/a2a"
    return {
        "protocolVersion": "0.3.0",
        "name": CARD_NAME,
        "description": (
            "Fictional Northstar Enterprises onboarding specialist for Project Orion. "
            "Builds a six-control checklist for proposed Java developer hires, identifies "
            "responsible teams and dependencies, and clearly separates recommendations "
            "from executed actions. No external HR systems are connected."
        ),
        "url": endpoint,
        "preferredTransport": "JSONRPC",
        "additionalInterfaces": [{"url": endpoint, "transport": "JSONRPC"}],
        "version": "1.0.0",
        "provider": {"organization": "Northstar Enterprises (fictional workshop example)", "url": base_url(request)},
        "capabilities": {"streaming": False, "pushNotifications": False, "stateTransitionHistory": False},
        "defaultInputModes": ["text/plain"],
        "defaultOutputModes": ["text/plain"],
        "skills": [
            {
                "id": "project_orion_onboarding",
                "name": "Project Orion onboarding planning",
                "description": "Generate a six-control onboarding plan for 1-20 proposed Project Orion Java developers with owners, dependencies and no real-world execution.",
                "tags": ["onboarding", "HR", "Java", "Project Orion", "new hires", "checklist"],
                "examples": [
                    "Prepare an onboarding checklist for two Java developers joining Project Orion.",
                    "What should HR, IT, Security, and the manager complete before Project Orion onboarding?",
                ],
            }
        ],
        "securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer"}},
        "security": [{"bearerAuth": []}],
        "supportsAuthenticatedExtendedCard": False,
    }


def developer_count(message: str) -> int:
    text = message.lower()
    match = re.search(r"\b(\d{1,2})\s+(?:new\s+|proposed\s+|additional\s+)?(?:java\s+)?developers?\b", text)
    if match:
        return max(1, min(20, int(match.group(1))))
    for word, value in {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}.items():
        if re.search(rf"\b{word}\s+(?:new\s+|proposed\s+|additional\s+)?(?:java\s+)?developers?\b", text):
            return value
    return 2


def answer(text: str) -> str:
    count = developer_count(text)
    if re.search(r"\b(germany|remote work|annual leave|vacation|leave days)\b", text.lower()):
        return (
            "Northstar Onboarding Desk handles onboarding planning, not employee policy decisions. "
            "Ask the Northstar People Policy specialist for the applicable policy and citation. "
            "No request has been approved or submitted."
        )
    checklist = [
        ("1", "Hiring authorization", "HR / Talent Acquisition", "Confirm authorized role, headcount and start dates"),
        ("2", "Right-to-work verification", "HR / Compliance", "Complete required identity and eligibility checks before access"),
        ("3", "Security training", "Security / HR", "Schedule and verify induction plus acceptable-use acknowledgement"),
        ("4", "Access governance", "Hiring manager / IT", "Define role-based least-privilege access and approvals"),
        ("5", "Device provisioning", "IT Service Desk", "Prepare managed laptop, MFA and standard baseline"),
        ("6", "Manager sign-off", "Hiring manager", "Verify prerequisites, first-week plan and ownership"),
    ]
    lines = [
        "NORTHSTAR ONBOARDING DESK — PROJECT ORION (FICTIONAL LAB DATA)",
        f"Scope: {count} proposed Java developer(s); planning only.",
        "Six required onboarding controls:",
    ]
    for number, item, owner, dependency in checklist:
        lines.append(f"{number}. {item} | Owner: {owner} | Dependency: {dependency}")
    lines.extend([
        "Suggested first-week sequence: Day 1 HR eligibility and manager kickoff; Day 2 IT and least-privilege access; "
        "Day 3 security induction; Day 4 repository/tooling access checks; Day 5 manager validation and remaining blockers.",
        "Evidence boundary: these are proposed tasks. No offer, hire, access grant, "
        "device order, approval or HR record was created or changed.",
        "Escalation: unresolved employment or policy questions go to HR; access exceptions go to Security and the hiring manager.",
    ])
    return "\n".join(lines)


def rpc_error(request_id: Any, code: int, message: str, status: int = 200) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}, status_code=status)


def authorized(request: Request) -> bool:
    secret = os.environ.get("A2A_BEARER_TOKEN", "")
    if not secret:
        return False  # Fail closed when misconfigured.
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    return scheme.lower() == "bearer" and hmac.compare_digest(token, secret)


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "northstar-onboarding-desk", "a2a_version": "0.3.0"})


async def card(request: Request) -> JSONResponse:
    return JSONResponse(agent_card(request))


async def landing(request: Request) -> PlainTextResponse:
    return PlainTextResponse("Northstar Onboarding Desk A2A 0.3.0. See /.well-known/agent-card.json; POST to /a2a with Bearer token.")


async def rpc(request: Request) -> JSONResponse:
    if not authorized(request):
        return JSONResponse({"error": "unauthorized", "message": "A2A_BEARER_TOKEN is required"}, status_code=401,
                            headers={"WWW-Authenticate": 'Bearer realm="northstar-a2a"'})
    try:
        if int(request.headers.get("content-length", "0")) > 100_000:
            return rpc_error(None, -32600, "Request too large", 413)
        data = await request.json()
    except (ValueError, TypeError):
        return rpc_error(None, -32700, "Invalid JSON")
    if not isinstance(data, dict):
        return rpc_error(None, -32600, "Invalid JSON-RPC request")
    rid = data.get("id")
    if data.get("jsonrpc") != "2.0" or not isinstance(data.get("method"), str):
        return rpc_error(rid, -32600, "Invalid JSON-RPC request")
    params = data.get("params") or {}
    if not isinstance(params, dict):
        return rpc_error(rid, -32602, "params must be an object")
    method = data["method"]
    if method == "message/send":
        msg = params.get("message") or {}
        if not isinstance(msg, dict) or msg.get("role") != "user":
            return rpc_error(rid, -32602, "Expected a user message")
        parts = msg.get("parts") or []
        if not isinstance(parts, list):
            return rpc_error(rid, -32602, "parts must be a list")
        text_parts = [part.get("text", "") for part in parts if isinstance(part, dict) and part.get("kind") == "text"]
        question = "\n".join(t for t in text_parts if isinstance(t, str)).strip()
        if not question or len(question) > 12000:
            return rpc_error(rid, -32602, "A nonempty text message of at most 12000 characters is required")
        task_id = str(uuid.uuid4())
        context_id = msg.get("contextId") or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        output = answer(question)
        task = {
            "kind": "task",
            "id": task_id,
            "contextId": context_id,
            "status": {"state": "completed", "timestamp": now},
            "artifacts": [{"artifactId": str(uuid.uuid4()), "name": "Project Orion onboarding plan", "parts": [{"kind": "text", "text": output}]}],
        }
        TASKS[task_id] = task
        while len(TASKS) > MAX_TASKS:
            TASKS.popitem(last=False)
        return JSONResponse({"jsonrpc": "2.0", "id": rid, "result": task})
    if method == "tasks/get":
        task_id = params.get("id")
        if not isinstance(task_id, str) or not task_id:
            return rpc_error(rid, -32602, "Task id is required")
        if task_id not in TASKS:
            return rpc_error(rid, -32001, "Task not found")
        return JSONResponse({"jsonrpc": "2.0", "id": rid, "result": TASKS[task_id]})
    if method == "tasks/cancel":
        return rpc_error(rid, -32002, "Completed tasks cannot be cancelled")
    return rpc_error(rid, -32601, f"A2A method not supported: {method}")


app = Starlette(routes=[
    Route("/health", health, methods=["GET"]),
    Route("/.well-known/agent-card.json", card, methods=["GET"]),
    Route("/.well-known/agent.json", card, methods=["GET"]),  # discovery alias for older clients
    Route("/", landing, methods=["GET"]),
    Route("/", rpc, methods=["POST"]),
    Route("/a2a", rpc, methods=["POST"]),
])
