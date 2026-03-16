#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


RULESET_VERSION = "v1"
HIGH_RISK_HINTS = (
    "switchadmin",
    "bastion",
    "graphstore",
    "auth",
    "token",
    "password",
    "credential",
    "secret",
)
CONSTRAINT_HINTS = ("仅允许", "脱敏", "审计", "禁止", "最小权限", "前置条件")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_gateway_selectors(text: str) -> List[str]:
    selectors = []
    for line in text.splitlines():
        m = re.match(r"^\s*-\s*selector:\s*(\S+)\s*$", line)
        if m:
            selectors.append(m.group(1))
    return selectors


def parse_method_blocks(text: str) -> List[Dict[str, object]]:
    lines = text.splitlines()
    blocks: List[Dict[str, object]] = []
    current: Dict[str, object] = {}
    in_method_section = False
    in_option = False
    in_responses = False
    in_response_200 = False
    has_examples_200 = False
    tags: List[str] = []
    description = ""
    summary = ""

    def flush_current() -> None:
        nonlocal current, has_examples_200, tags, description, summary
        if current:
            current["has_tags"] = len(tags) > 0
            current["has_summary"] = bool(summary.strip())
            current["has_description"] = bool(description.strip())
            current["has_examples_200"] = has_examples_200
            current["tags"] = tags[:]
            current["summary"] = summary
            current["description"] = description
            blocks.append(current)
        current = {}
        has_examples_200 = False
        tags = []
        description = ""
        summary = ""

    for line in lines:
        if re.match(r"^\s*method:\s*$", line):
            in_method_section = True
            continue
        if in_method_section and re.match(r"^\s*message:\s*$", line):
            flush_current()
            break
        if not in_method_section:
            continue

        method_match = re.match(r"^\s*-\s*method:\s*(\S+)\s*$", line)
        if method_match:
            flush_current()
            current = {"method": method_match.group(1)}
            in_option = False
            in_responses = False
            in_response_200 = False
            continue

        if not current:
            continue

        if re.match(r"^\s*option:\s*$", line):
            in_option = True
            continue

        if not in_option:
            continue

        if re.match(r"^\s*tags:\s*$", line):
            continue
        tag_match = re.match(r'^\s*-\s*"?(.*?)"?\s*$', line)
        if tag_match and "method:" not in line and re.search(r'^\s{8,}-\s*', line):
            tag = tag_match.group(1).strip()
            if tag and tag not in ("selector",):
                tags.append(tag)

        summary_match = re.match(r'^\s*summary:\s*"(.*)"\s*$', line)
        if summary_match:
            summary = summary_match.group(1)
            continue

        desc_match = re.match(r'^\s*description:\s*(.+?)\s*$', line)
        if desc_match:
            value = desc_match.group(1).strip()
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            description = value
            continue

        if re.match(r"^\s*responses:\s*$", line):
            in_responses = True
            in_response_200 = False
            continue

        if in_responses and re.match(r'^\s*"200":\s*$', line):
            in_response_200 = True
            continue

        if in_response_200 and re.match(r'^\s*examples:\s*$', line):
            has_examples_200 = True
            continue

        if in_responses and re.match(r'^\s*"[0-9]{3}":\s*$', line) and not re.match(r'^\s*"200":\s*$', line):
            in_response_200 = False

    return blocks


def parse_ignore_rules(path: Path) -> Set[Tuple[str, str]]:
    if not path.exists():
        return set()
    ignored: Set[Tuple[str, str]] = set()
    current: Dict[str, str] = {}
    now = dt.datetime.now(dt.timezone.utc)
    for raw in _read_text(path).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            if current:
                method = current.get("method", "")
                rule = current.get("rule", "")
                expires = current.get("expires_at", "")
                if method and rule:
                    try:
                        expire_time = dt.datetime.fromisoformat(expires.replace("Z", "+00:00"))
                        if expire_time >= now:
                            ignored.add((method, rule))
                    except Exception:
                        pass
            current = {}
            line = line[2:]
        if ":" in line:
            k, v = line.split(":", 1)
            current[k.strip()] = v.strip().strip('"').strip("'")
    if current:
        method = current.get("method", "")
        rule = current.get("rule", "")
        expires = current.get("expires_at", "")
        if method and rule:
            try:
                expire_time = dt.datetime.fromisoformat(expires.replace("Z", "+00:00"))
                if expire_time >= now:
                    ignored.add((method, rule))
            except Exception:
                pass
    return ignored


def is_high_risk(method_name: str, tags: List[str], description: str) -> bool:
    text = f"{method_name} {' '.join(tags)} {description}".lower()
    return any(h in text for h in HIGH_RISK_HINTS)


def has_constraints(description: str) -> bool:
    return any(k in description for k in CONSTRAINT_HINTS)


def collect_service_dirs(api_root: Path, service_glob: str) -> List[Path]:
    return sorted([p for p in api_root.glob(service_glob) if p.is_dir()])


def main() -> int:
    parser = argparse.ArgumentParser(description="Check openapiv2 method coverage and quality.")
    parser.add_argument("--api-root", default="api")
    parser.add_argument("--service-glob", default="*/*/*")
    parser.add_argument("--ignore-file", default="")
    parser.add_argument("--output-json", default="")
    args = parser.parse_args()

    api_root = Path(args.api_root).resolve()
    service_dirs = collect_service_dirs(api_root, args.service_glob)
    ignored = parse_ignore_rules(Path(args.ignore_file).resolve()) if args.ignore_file else set()

    report = {
        "ruleset_version": RULESET_VERSION,
        "services": [],
        "summary": {
            "service_count": 0,
            "fail_count": 0,
            "warning_count": 0,
        },
        "exit_code": 0,
    }

    total_fail = 0
    total_warning = 0

    for service_dir in service_dirs:
        gateway_files = list(service_dir.glob("*.gateway.yaml"))
        openapi_files = list(service_dir.glob("*.openapiv2.yaml"))
        if not gateway_files or not openapi_files:
            continue
        gateway_text = _read_text(gateway_files[0])
        openapi_text = _read_text(openapi_files[0])

        selectors = parse_gateway_selectors(gateway_text)
        method_blocks = parse_method_blocks(openapi_text)
        methods = [m["method"] for m in method_blocks]

        selector_set = set(selectors)
        method_set = set(methods)
        missing_methods = sorted(selector_set - method_set)
        extra_methods = sorted(method_set - selector_set)

        missing_fields = []
        high_risk_violations = []
        warnings = []

        for block in method_blocks:
            method = str(block["method"])
            required_checks = [
                ("tags", bool(block["has_tags"])),
                ("summary", bool(block["has_summary"])),
                ("description", bool(block["has_description"])),
                ("responses.200.examples", bool(block["has_examples_200"])),
            ]
            for field_name, ok in required_checks:
                if ok:
                    continue
                if (method, field_name) in ignored:
                    continue
                missing_fields.append({"method": method, "field": field_name})

            if is_high_risk(method, list(block.get("tags", [])), str(block.get("description", ""))):
                if not has_constraints(str(block.get("description", ""))):
                    if (method, "high_risk_constraints") not in ignored:
                        high_risk_violations.append(method)

            if not str(block.get("summary", "")).strip():
                warnings.append({"method": method, "rule": "readability.summary"})

        fail_count = len(missing_methods) + len(extra_methods) + len(missing_fields) + len(high_risk_violations)
        warning_count = len(warnings)
        total_fail += fail_count
        total_warning += warning_count

        report["services"].append(
            {
                "service": str(service_dir),
                "gateway_selector_count": len(selectors),
                "openapi_method_count": len(methods),
                "missing_methods": missing_methods,
                "extra_methods": extra_methods,
                "missing_fields": missing_fields,
                "high_risk_violations": high_risk_violations,
                "warnings": warnings,
                "fail_count": fail_count,
                "warning_count": warning_count,
            }
        )

    report["summary"]["service_count"] = len(report["services"])
    report["summary"]["fail_count"] = total_fail
    report["summary"]["warning_count"] = total_warning

    if total_fail > 0:
        report["exit_code"] = 1
    else:
        report["exit_code"] = 0

    print(
        json.dumps(
            {
                "ruleset_version": report["ruleset_version"],
                "service_count": report["summary"]["service_count"],
                "fail_count": report["summary"]["fail_count"],
                "warning_count": report["summary"]["warning_count"],
                "exit_code": report["exit_code"],
            },
            ensure_ascii=False,
        )
    )

    if args.output_json:
        Path(args.output_json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return int(report["exit_code"])


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(2)
