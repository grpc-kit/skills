#!/usr/bin/env python3
import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


HTTP_VERBS = ("get", "post", "put", "patch", "delete")
TAG_HINTS = (
    (("/auth/",), "认证鉴权"),
    (("/mfa/",), "MFA 多因素认证"),
    (("/local/config",), "本地配置"),
    (("/global/settings",), "全局设置"),
    (("/services",), "服务字典管理"),
    (("/menus",), "菜单管理"),
    (("/policies",), "策略管理"),
    (("/roles",), "角色管理"),
    (("/departments",), "部门管理"),
    (("/users",), "用户管理"),
    (("/groups",), "群组管理"),
    (("/credentials", "/oatuh2/"), "安全相关"),
    (("/database",), "数据库相关"),
)


def _read_text(path: Path) -> str:
	return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
	path.write_text(text, encoding="utf-8")


def parse_gateway_rules(text: str) -> List[Dict[str, str]]:
	rules: List[Dict[str, str]] = []
	current: Dict[str, str] = {}

	for line in text.splitlines():
		selector_match = re.match(r"^\s*-\s*selector:\s*(\S+)\s*$", line)
		if selector_match:
			if current:
				rules.append(current)
			current = {"selector": selector_match.group(1)}
			continue

		if not current:
			continue

		for verb in HTTP_VERBS:
			verb_match = re.match(rf'^\s*{verb}:\s*"([^"]+)"\s*$', line)
			if verb_match:
				current["http_method"] = verb.upper()
				current["path"] = verb_match.group(1)
				break

		body_match = re.match(r'^\s*body:\s*"([^"]*)"\s*$', line)
		if body_match:
			current["body"] = body_match.group(1)

	if current:
		rules.append(current)

	return rules


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

	flush_current()
	return blocks


def extract_method_blocks(text: str) -> Tuple[str, Dict[str, str], str]:
	lines = text.splitlines()
	method_header_index = None
	for index, line in enumerate(lines):
		if re.match(r"^\s*method:\s*$", line):
			method_header_index = index
			break
	if method_header_index is None:
		raise ValueError("openapiv2 document missing method section")

	suffix_start = len(lines)
	block_starts: List[int] = []
	for index in range(method_header_index + 1, len(lines)):
		line = lines[index]
		if re.match(r"^\s*message:\s*$", line):
			suffix_start = index
			break
		if re.match(r"^\s*-\s*method:\s*(\S+)\s*$", line):
			block_starts.append(index)

	prefix = "\n".join(lines[: method_header_index + 1]) + "\n"
	suffix = ""
	if suffix_start < len(lines):
		suffix = "\n" + "\n".join(lines[suffix_start:])
		if text.endswith("\n"):
			suffix += "\n"

	blocks: Dict[str, str] = {}
	for block_index, start in enumerate(block_starts):
		end = suffix_start
		if block_index + 1 < len(block_starts):
			end = block_starts[block_index + 1]
		block_text = "\n".join(lines[start:end]).rstrip() + "\n"
		method_match = re.match(r"^\s*-\s*method:\s*(\S+)\s*$", lines[start])
		if method_match:
			blocks[method_match.group(1)] = block_text

	return prefix, blocks, suffix


def derive_tag(rule: Dict[str, str]) -> str:
	path = rule.get("path", "")
	for hints, tag in TAG_HINTS:
		if any(hint in path for hint in hints):
			return tag
	return "待补充"


def render_placeholder_block(rule: Dict[str, str]) -> str:
	selector = rule["selector"]
	rpc_name = selector.rsplit(".", 1)[-1]
	http_method = rule.get("http_method", "GET")
	path = rule.get("path", "")
	tag = derive_tag(rule)
	return (
		f"    - method: {selector}\n"
		"      option:\n"
		"        tags:\n"
		f"          - \"{tag}\"\n"
		f"        summary: \"TODO: 补充 {rpc_name} 摘要\"\n"
		f"        description: \"接口格式：{http_method} {path}。前置条件与业务约束待补充。\"\n"
		"        responses:\n"
		"          \"200\":\n"
		"            examples:\n"
		"              \"application/json\": \"{}\"\n"
	)


def sync_openapi_methods(gateway_text: str, openapi_text: str) -> str:
	rules = parse_gateway_rules(gateway_text)
	prefix, existing_blocks, suffix = extract_method_blocks(openapi_text)
	ordered_blocks: List[str] = []
	seen_selectors = set()

	for rule in rules:
		selector = rule["selector"]
		seen_selectors.add(selector)
		if selector in existing_blocks:
			ordered_blocks.append(existing_blocks[selector])
			continue
		ordered_blocks.append(render_placeholder_block(rule))

	for selector, block_text in existing_blocks.items():
		if selector in seen_selectors:
			continue
		ordered_blocks.append(block_text)

	body = "".join(ordered_blocks)
	return prefix + body + suffix


def main(argv: Optional[Sequence[str]] = None) -> int:
	parser = argparse.ArgumentParser(description="Sync openapiv2 method blocks from gateway selectors.")
	parser.add_argument("--gateway-file", required=True)
	parser.add_argument("--openapi-file", required=True)
	args = parser.parse_args(argv)

	try:
		gateway_path = Path(args.gateway_file)
		openapi_path = Path(args.openapi_file)
		synced = sync_openapi_methods(_read_text(gateway_path), _read_text(openapi_path))
		_write_text(openapi_path, synced)
		return 0
	except Exception:
		return 2


if __name__ == "__main__":
	raise SystemExit(main())