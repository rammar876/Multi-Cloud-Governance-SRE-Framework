"""Provider-neutral policy validation and drift evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SEVERITY_WEIGHT = {"low": 1, "medium": 2, "high": 3, "critical": 4}
SUPPORTED_PROVIDERS = {"aws", "azure", "gcp"}


def load_json(path: str | Path) -> Any:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_catalog(catalog: dict[str, Any]) -> None:
    controls = catalog.get("controls")
    _assert(isinstance(controls, list) and controls, "catalog.controls must be a non-empty list")
    seen: set[str] = set()
    for control in controls:
        control_id = control.get("id")
        _assert(isinstance(control_id, str) and control_id, "each control requires an id")
        _assert(control_id not in seen, f"duplicate control id: {control_id}")
        seen.add(control_id)
        severity = control.get("severity")
        _assert(severity in SEVERITY_WEIGHT, f"{control_id}: unsupported severity {severity!r}")
        expected = control.get("expected", {})
        _assert(expected.get("operator") in {"eq", "gte", "lte", "contains"},
                f"{control_id}: unsupported operator")
        mappings = control.get("provider_mappings", {})
        _assert(isinstance(mappings, dict), f"{control_id}: provider_mappings must be an object")
        unknown = set(mappings) - SUPPORTED_PROVIDERS
        _assert(not unknown, f"{control_id}: unsupported providers: {', '.join(sorted(unknown))}")


def _matches(actual: Any, operator: str, expected: Any) -> bool:
    try:
        if operator == "eq":
            return actual == expected
        if operator == "gte":
            return actual >= expected
        if operator == "lte":
            return actual <= expected
        if operator == "contains":
            return expected in actual
    except TypeError:
        return False
    return False


def evaluate(catalog: dict[str, Any], observations: dict[str, Any]) -> dict[str, Any]:
    """Evaluate normalized provider observations against a control catalog."""
    validate_catalog(catalog)
    items = observations.get("observations")
    _assert(isinstance(items, list), "observations.observations must be a list")

    controls = {control["id"]: control for control in catalog["controls"]}
    results: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        provider = item.get("provider")
        control_id = item.get("control_id")
        _assert(provider in SUPPORTED_PROVIDERS, f"observation {index}: unsupported provider {provider!r}")
        _assert(control_id in controls, f"observation {index}: unknown control {control_id!r}")
        _assert(bool(item.get("resource_id")), f"observation {index}: resource_id is required")

        control = controls[control_id]
        expected = control["expected"]
        compliant = _matches(item.get("actual"), expected["operator"], expected.get("value"))
        results.append({
            "provider": provider,
            "resource_id": item["resource_id"],
            "control_id": control_id,
            "title": control["title"],
            "severity": control["severity"],
            "status": "compliant" if compliant else "drifted",
            "actual": item.get("actual"),
            "expected": expected,
            "native_policy": control.get("provider_mappings", {}).get(provider),
            "remediation": None if compliant else control.get("remediation"),
        })

    drifted = [result for result in results if result["status"] == "drifted"]
    total_weight = sum(SEVERITY_WEIGHT[result["severity"]] for result in results)
    drift_weight = sum(SEVERITY_WEIGHT[result["severity"]] for result in drifted)
    score = 100.0 if total_weight == 0 else round(100 * (1 - drift_weight / total_weight), 1)

    by_provider = {}
    for provider in sorted(SUPPORTED_PROVIDERS):
        provider_results = [result for result in results if result["provider"] == provider]
        if provider_results:
            by_provider[provider] = {
                "evaluated": len(provider_results),
                "drifted": sum(result["status"] == "drifted" for result in provider_results),
            }

    return {
        "framework": catalog.get("framework", "MCG-SRE"),
        "summary": {
            "evaluated": len(results),
            "compliant": len(results) - len(drifted),
            "drifted": len(drifted),
            "weighted_compliance_score": score,
            "by_provider": by_provider,
        },
        "results": results,
    }
