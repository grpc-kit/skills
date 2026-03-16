# openapiv2-method-doc-coverage 快速接入指南

本指南用于把 `openapiv2` 文档门禁快速接入任意仓库，目标是校验：

- `gateway selector` 与 `openapiv2 method` 覆盖一致
- method 四要素完整（`tags/summary/description/responses.200.examples`）
- 高风险接口具备约束性描述

对应检查脚本：

- `scripts/check_openapiv2_method_coverage.py`

---

## 3 步快速接入

### 第 1 步：准备脚本与豁免模板

你可以任选一种方式：

- 方式 A（推荐，统一维护）：在 CI 中直接调用技能库脚本  
  `skills/openapiv2-method-doc-coverage/scripts/check_openapiv2_method_coverage.py`
- 方式 B（仓内自治）：把脚本与模板复制到目标仓，例如：
  - `tools/openapiv2/check_openapiv2_method_coverage.py`
  - `tools/openapiv2/ignore-rules.yaml`（可从 `templates/ignore-rules.example.yaml` 初始化）

---

### 第 2 步：本地执行一次基线检查

在目标仓根目录执行（按实际目录调整参数）：

```bash
python tools/openapiv2/check_openapiv2_method_coverage.py \
  --api-root api \
  --service-glob "*/*/*" \
  --ignore-file tools/openapiv2/ignore-rules.yaml \
  --output-json /tmp/openapiv2-report.json
```

关键参数说明：

- `--api-root`：接口定义根目录（默认 `api`）
- `--service-glob`：服务目录模式（如 `oneops/netdev/v1` 或 `*/*/*`）
- `--ignore-file`：临时豁免规则文件（可选）
- `--output-json`：机器可读报告输出路径（CI 建议必填）

退出码约定：

- `0`：通过
- `1`：Fail-fast 失败（存在必须修复项）
- `2`：执行错误（脚本异常或输入错误）

---

## 参数矩阵（默认值与覆盖方式）

- `--api-root`：默认 `api`
- `--service-glob`：默认 `*/*/*`
- `--ignore-file`：默认空（不启用豁免）
- `--output-json`：默认空（建议 CI 始终输出）

当仓库目录结构与默认值不一致时，必须显式覆盖参数，避免漏检。

---

### 第 3 步：接入 CI（PR 阻断）

可直接参考模板：

- `templates/ci-github-actions.example.yml`

接入后建议策略：

- PR 触发：仅当 `api/**/*.proto|*.gateway.yaml|*.openapiv2.yaml` 变更时运行
- `fail-fast` 直接阻断合并
- `warning` 仅提示并上传 JSON 报告作为构建产物

---

## 多仓接入建议

- **统一规则版本**：在仓内固定 `RULESET_VERSION`，避免不同仓门禁漂移。
- **先增量后全量**：PR 用增量目录，夜间任务跑全量 `*/*/*`。
- **豁免可审计**：`ignore-rules.yaml` 必须包含 `reason/owner/expires_at`，过期自动收敛。

---

## 规则版本化建议

- 当前脚本内置 `RULESET_VERSION = "v1"`。
- 规则升级时建议同步记录：
  - 新增规则/破坏性变化
  - 迁移窗口和回滚策略
  - baseline 刷新方式
- 同一仓库建议一次仅升级一个主版本，避免门禁震荡。

---

## JSON 报告字段约定

报告建议重点关注以下字段：

- `ruleset_version`
- `services[].service`
- `services[].gateway_selector_count`
- `services[].openapi_method_count`
- `services[].missing_methods`
- `services[].extra_methods`
- `services[].missing_fields`
- `services[].high_risk_violations`
- `services[].warnings`
- `summary.fail_count`
- `summary.warning_count`
- `exit_code`

可用于 CI 阻断、看板聚合和趋势跟踪。

---

## 命令模板（增量/全量/豁免）

增量检查（单服务）：

```bash
python tools/openapiv2/check_openapiv2_method_coverage.py \
  --api-root api \
  --service-glob oneops/netdev/v1 \
  --output-json /tmp/openapiv2-report.json
```

全量检查：

```bash
python tools/openapiv2/check_openapiv2_method_coverage.py \
  --api-root api \
  --service-glob "*/*/*" \
  --output-json /tmp/openapiv2-report.json
```

携带豁免规则：

```bash
python tools/openapiv2/check_openapiv2_method_coverage.py \
  --api-root api \
  --service-glob "*/*/*" \
  --ignore-file tools/openapiv2/ignore-rules.yaml \
  --output-json /tmp/openapiv2-report.json
```

---

## 常见问题

- `responses.200.examples` 缺失太多怎么办？  
  先按业务域分批补齐（如 backup/admin/firewall），避免一次性大改。

- 某些接口只返回 `204` 是否必须有 `200` 示例？  
  建议补 `200` 示例；若暂不调整，使用 `ignore-rules.yaml` 临时豁免并设置过期时间。

- 如何对单个服务快速验证？  
  用 `--service-glob oneops/netdev/v1` 仅检查指定目录。
