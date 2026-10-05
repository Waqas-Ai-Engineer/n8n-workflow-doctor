"""Lint rules. Each rule: fn(workflow) -> list[Finding dict]."""
import re

SECRET_KEYS = re.compile(r"(api[_-]?key|token|secret|password|authorization|bearer)", re.I)
SECRET_VALUE = re.compile(r"(sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|xox[bp]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|Bearer\s+[A-Za-z0-9._-]{16,})")
DEFAULT_NAME = re.compile(r"^(HTTP Request|Code|Set|If|Switch|Edit Fields|Merge|Function)\d*$")
HTTP_TYPES = {"n8n-nodes-base.httpRequest"}
TRIGGERS = {"n8n-nodes-base.webhook", "n8n-nodes-base.scheduleTrigger", "n8n-nodes-base.cron",
            "n8n-nodes-base.manualTrigger", "n8n-nodes-base.emailReadImap"}

def _f(rule, sev, node, msg, fix):
    return {"rule": rule, "severity": sev, "node": node, "message": msg, "fix": fix}

def _walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")
    else:
        yield path, obj

def hardcoded_secrets(wf):
    out = []
    for n in wf.get("nodes", []):
        for path, val in _walk(n.get("parameters", {})):
            if not isinstance(val, str) or val.startswith("="):
                continue
            leaf = path.split(".")[-1]
            if SECRET_VALUE.search(val) or (SECRET_KEYS.search(leaf) and len(val) >= 12 and " " not in val):
                out.append(_f("hardcoded-secret", "error", n.get("name"),
                    f"Possible hardcoded secret at parameters.{path}",
                    "Move it into an n8n Credential and reference that instead."))
    return out

def no_error_handling(wf):
    has_err_trigger = any(n.get("type") == "n8n-nodes-base.errorTrigger" for n in wf.get("nodes", []))
    has_err_wf = bool(wf.get("settings", {}).get("errorWorkflow"))
    if has_err_trigger or has_err_wf:
        return []
    return [_f("no-error-workflow", "warning", None,
        "No error workflow configured: failures will go unnoticed.",
        "Set Settings > Error Workflow to a workflow that alerts you (Slack/email).")]

def http_without_retry(wf):
    out = []
    for n in wf.get("nodes", []):
        if n.get("type") in HTTP_TYPES and not n.get("retryOnFail") and not n.get("continueOnFail") \
           and n.get("onError") not in ("continueRegularOutput", "continueErrorOutput"):
            out.append(_f("http-no-retry", "warning", n.get("name"),
                "HTTP Request has no retry or error output; one flaky API call kills the run.",
                "Enable Retry On Fail (3 tries) or route the error output."))
    return out

def default_names(wf):
    return [_f("default-node-name", "info", n.get("name"),
               "Node still has a default name; hard to debug in execution logs.",
               "Rename to describe intent, e.g. 'Fetch lead from CRM'.")
            for n in wf.get("nodes", []) if DEFAULT_NAME.match(n.get("name") or "")]

def disabled_nodes(wf):
    return [_f("disabled-node", "info", n.get("name"),
               "Node is disabled but left in the workflow.", "Delete dead nodes before shipping.")
            for n in wf.get("nodes", []) if n.get("disabled")]

def orphan_nodes(wf):
    connected = set(wf.get("connections", {}).keys())
    for outs in wf.get("connections", {}).values():
        for branch in outs.values():
            for group in branch:
                for c in group or []:
                    connected.add(c.get("node"))
    return [_f("orphan-node", "warning", n.get("name"),
               "Node is not connected to anything.", "Connect or delete it.")
            for n in wf.get("nodes", [])
            if n.get("name") not in connected and n.get("type") not in TRIGGERS
            and "sticky" not in (n.get("type") or "").lower()]

def no_trigger(wf):
    if any("trigger" in (n.get("type") or "").lower() or n.get("type") in TRIGGERS for n in wf.get("nodes", [])):
        return []
    return [_f("no-trigger", "warning", None, "Workflow has no trigger node.", "Add a Webhook/Schedule trigger.")]

def webhook_unauthenticated(wf):
    return [_f("open-webhook", "warning", n.get("name"),
               "Webhook has no authentication; anyone with the URL can fire it.",
               "Set Authentication (Header/Basic) on the Webhook node.")
            for n in wf.get("nodes", [])
            if n.get("type") == "n8n-nodes-base.webhook"
            and n.get("parameters", {}).get("authentication", "none") == "none"]

def code_node_size(wf):
    out = []
    for n in wf.get("nodes", []):
        if n.get("type") == "n8n-nodes-base.code":
            code = n.get("parameters", {}).get("jsCode", "") or n.get("parameters", {}).get("pythonCode", "")
            if code.count("\n") > 60:
                out.append(_f("big-code-node", "info", n.get("name"),
                    "Code node exceeds 60 lines.", "Split into smaller nodes or a sub-workflow."))
    return out

RULES = [hardcoded_secrets, no_error_handling, http_without_retry, default_names,
         disabled_nodes, orphan_nodes, no_trigger, webhook_unauthenticated, code_node_size]
