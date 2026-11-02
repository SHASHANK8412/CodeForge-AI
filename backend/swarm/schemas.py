"""
Contract schemas (a JSON Schema subset compatible with FastAPI's OpenAPI output) and helpers.

  upgrade(endpoint)        a v1 endpoint (field-name lists) becomes v2: request/response JSON Schemas whose field
                           types are unknown ({}), required fields from the old lists, 200 + 422 responses
  model_schema(fields)     a Pydantic model's fields read from the AST -> JSON Schema (types, required, nullable)
  example(schema)          a value that satisfies a schema (for generated requests)
  validate(value, schema)  error messages from jsonschema (empty list = valid)
"""

from typing import Any, Dict, List, Optional

PY_TYPES = {"str": "string", "int": "integer", "float": "number", "bool": "boolean", "dict": "object", "Dict": "object",
            "list": "array", "List": "array", "datetime": "string", "date": "string", "EmailStr": "string"}


def model_schema(fields: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """{name: {"type": py_type, "required": bool, "nullable": bool, "items": py_type?}} -> JSON Schema object."""
    props = {}
    for name, f in fields.items():
        t = PY_TYPES.get(f.get("type") or "", None)
        s: Dict[str, Any] = {"type": t} if t else {}
        if t == "array" and PY_TYPES.get(f.get("items") or ""):
            s["items"] = {"type": PY_TYPES[f["items"]]}
        if f.get("nullable") and t:
            s["type"] = [t, "null"]
        props[name] = s
    return {"type": "object", "properties": props, "required": sorted(k for k, f in fields.items() if f.get("required"))}


def upgrade(e: Dict[str, Any]) -> Dict[str, Any]:
    """Fill v2 fields of a v1 endpoint dict (idempotent)."""
    out = dict(e)
    if out.get("request_schema") is None and out.get("request_fields") and out.get("method", "GET").upper() in ("POST", "PUT", "PATCH"):
        out["request_schema"] = {"type": "object", "properties": {f: {} for f in out["request_fields"]},
                                 "required": list(out["request_fields"])}
    if not out.get("responses"):
        body = {"type": "object", "properties": {f: {} for f in out.get("response_fields", [])},
                "required": list(out.get("response_fields", []))}
        out["responses"] = {"200": {"content_type": "application/json", "schema": body}}
        if out.get("request_schema"):
            out.setdefault("errors", {})
            out["errors"].setdefault("422", {"content_type": "application/json", "description": "invalid request body"})
    return out


def example(schema: Optional[Dict[str, Any]], name: str = "") -> Any:
    if not schema:
        return "example"
    t = schema.get("type")
    if isinstance(t, list):
        t = next((x for x in t if x != "null"), "string")
    if "enum" in schema:
        return schema["enum"][0]
    if t == "integer":
        return max(1, int(schema.get("minimum", 1)))
    if t == "number":
        return 1.5
    if t == "boolean":
        return True
    if t == "array":
        return [example(schema.get("items"))] if schema.get("items") else []
    if t == "object":
        return {k: example(v, k) for k, v in (schema.get("properties") or {}).items() if k in (schema.get("required") or [])
                or schema.get("properties")}
    return f"example-{name}" if name else "example"


def validate(value: Any, schema: Optional[Dict[str, Any]]) -> List[str]:
    if not schema:
        return []
    import jsonschema
    validator = jsonschema.Draft202012Validator(schema)
    return [f"{'/'.join(str(p) for p in err.absolute_path) or '(body)'}: {err.message}" for err in validator.iter_errors(value)][:20]


def schema_diff(declared: Dict[str, Any], contract: Dict[str, Any]) -> List[str]:
    """Differences between a component's declared object schema and the contract's (required fields and types)."""
    if not declared or not contract or contract.get("type") not in ("object", None):
        return []
    out = []
    cp, dp = contract.get("properties") or {}, declared.get("properties") or {}
    for f in contract.get("required") or []:
        if f not in dp:
            out.append(f"missing required field '{f}'")
    for f, s in cp.items():
        if f in dp and s.get("type") and dp[f].get("type"):
            want = s["type"] if isinstance(s["type"], list) else [s["type"]]
            got = dp[f]["type"] if isinstance(dp[f]["type"], list) else [dp[f]["type"]]
            if not set(got) & set(want):
                out.append(f"field '{f}' is {got} but the contract says {want}")
    return out
