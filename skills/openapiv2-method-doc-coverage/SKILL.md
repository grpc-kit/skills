---
name: openapiv2-method-doc-coverage
description: 维护并补全 grpc openapiv2 method 文档覆盖与语义质量。用于处理 `api/*/*/*` 下 `*.proto` 与 `*.gateway.yaml` 到 `*.openapiv2.yaml` 的 method 映射、缺失补齐、骨架同步、语义约束和 CI 门禁输出；当用户提到 method 覆盖率、从 gateway 同步 openapiv2、tags/summary/description/examples 质量或高风险接口说明时应触发。
---

# OpenAPIv2 Method 文档重设计规范

用于将 `*.gateway.yaml` 与 `*.proto` 的接口定义，稳定映射到 `*.openapiv2.yaml` 的 `openapiOptions.method`，并保证文档语义可被前端与 API 使用方一致理解。

## 目标与边界

- 目标：补全并维护 `*.openapiv2.yaml` 中 `method` 文档覆盖与质量。
- 输入来源：同目录下的 `*.proto` 与 `*.gateway.yaml`。
- 输出对象：当前服务版本目录下的 `*.openapiv2.yaml`。
- 不负责内容：
  - 前端 `@api/...` 导入规范与别名配置
  - 前端 `src/api/**` 客户端生成与迁移
  - 以上由 [`frontend-api-layer`](../frontend-api-layer/SKILL.md) 负责

## 目录与输入约束

- 目录模式固定为：`api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}`
- 同目录三件套：
  1. `xxx.proto`
  2. `xxx.gateway.yaml`
  3. `xxx.openapiv2.yaml`
- 只处理同一个 `${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}` 目录内的 method 文档，不跨版本、跨服务补写。

参数化目录、命令参数矩阵与多仓接入细节见 [README.md](README.md)。

## 适用场景

- 新增或变更了 `api/*/*/*/*.gateway.yaml`
- `openapiv2` 的 method 文档覆盖不足
- 需要先按 `gateway` 批量同步缺失 method，再人工补齐语义文案
- 需要统一 `tags / summary / description / responses.200.examples` 风格
- 需要补充语义约束（分页、`update_mask`、高风险接口说明）

## 标准执行流程（流水线）

1. 抽取覆盖清单
   - 从 gateway 读取 `- selector: ...KnownXxx.Method`
   - 从 openapiv2 读取 `- method: ...KnownXxx.Method`
   - 计算差集，得到缺失 method

2. 缺失 method 先做 preserve-and-fill 同步
  - 运行 `scripts/sync_openapiv2_methods.py`
  - 已存在的 method block 原样保留
  - gateway 中缺失的 method 生成 skeleton block，避免手工对齐顺序和 selector

3. 建立 method 模板并批量补齐
   - 每个 method 至少包含：
   - `tags`
   - `summary`
   - `description`（必须包含接口路径）
   - `responses.200.examples`

4. 按接口类型补语义描述
   - 列表接口：补分页语义（`page_token` / `offset` 二选一）
   - 更新接口：补 `update_mask` 行为
   - 删除/绑定类接口：空响应示例统一为 `{}`
   - 路径中带 `{parent}` 或 `{x.id}`：补参数语义，避免调用方误传

5. 编写并校验 examples
   - 示例 JSON 必须可解析
   - 枚举值按对应消息定义填写，不跨资源域复用
   - `int64` 标识符优先用字符串，规避前端精度风险
   - 涉及敏感信息的字段写脱敏示例

6. 交付并输出差异报告
   - 输出 method 覆盖率与差集结果
   - 输出新增/更新 method 数量
   - 输出高风险接口说明覆盖情况与建议项告警

## 执行模式（增量与全量）

- 增量模式（默认）：仅检查本次变更涉及的服务目录，用于 PR 快速反馈。
- 全量模式：检查 `API_ROOT` 下全部符合模式的服务目录，用于夜间任务或基线刷新。
- 若增量模式发现失败，必须允许切换到全量模式进行二次确认。

### 增量/全量切换决策规则

1. 默认使用增量模式（`--service-glob` 指向本次改动目录）。
2. 出现以下任一情况，升级为全量模式复核：
   - 同一 PR 同时改动多个服务目录
   - 涉及规则升级、脚本升级或 ignore 规则批量调整
   - 增量结果出现 `missing_methods` 或 `high_risk_violations`
3. 全量复核通过后，才能将失败判定归因为“局部数据噪声”而非规则问题。

## Method 文档模板规范（必备字段）

每个 method 至少包含以下结构：

- `tags`：按资源域归类，避免混域
- `summary`：统一动词风格（创建/获取/更新/删除/列表/绑定）
- `description`：必须包含“接口路径”和关键约束
- `responses.200.examples`：提供最小可读、合法 JSON 示例

## 同步模式约定

- 默认模式：preserve-and-fill
  - 保留已有 method 的人工 `tags/summary/description/examples`
  - 仅对 gateway 中缺失的 method 生成 skeleton block
- skeleton block 目标：先满足 `missing_methods == 0` 与四要素齐备，再进入人工补写语义阶段
- 不建议首次就 force-rebuild 全量重写 `openapiOptions.method`，除非当前文档已经整体失真或无法保留人工内容

## 语义一致性规范（与消费侧对齐）

- 数值与时间：
  - `int64/uint64` 相关标识字段示例优先字符串
  - 时间字段示例格式保持一致（如 RFC3339 字符串）
- 分页与更新：
  - 列表接口说明 oneof 分页语义（`page_token` 与 `offset` 不同时使用）
  - 更新接口必须说明 `update_mask` 影响范围（局部更新/字段选择）
- 高风险接口最小说明集（认证、密码、授权变更）：
  - 调用前置条件
  - 关键参数约束
  - 安全或审计相关注意事项

## 质量门禁（平衡分层）

### 必需项（Fail-fast）

- Gate 1: `missing_methods == 0`（或明确排除并说明）
- Gate 2: 每个 method 均具备四要素
- Gate 3: 每个 example 为合法 JSON
- Gate 4: 高风险接口 description 明确说明关键约束

### 建议项（Warning）

- Gate W1: `summary/description` 用词风格一致、可读性稳定
- Gate W2: 枚举值不跨资源域复用
- Gate W3: 示例具备最小可运行语义（字段命名、类型与 proto 一致）

## 排除规则治理（ignore）

- 允许对个别 method 设置豁免，但必须使用可审计文件（建议 `ignore-rules.yaml`）。
- 每条豁免至少包含：
  - `method`：完整方法名
  - `rule`：被豁免的规则（如 `responses.200.examples`）
  - `reason`：业务原因
  - `owner`：责任人
  - `expires_at`：过期时间（RFC3339）
- 过期豁免视为失败项，必须在 CI 中阻断。

规则版本化、JSON 报告字段与命令模板统一维护在 [README.md](README.md)。

## 与前端技能协作边界

- `@api/...` 导入路径、深链导入禁止、别名配置校验，不属于本技能范围。
- 本技能只保证“`gateway/proto` 到 `openapiv2 method` 的文档覆盖与语义一致性”。
- 前端 API 生成与迁移请使用 [`frontend-api-layer`](../frontend-api-layer/SKILL.md)。

## 交付产物模板

- 服务版本：`${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}`
- gateway selector 总数：`N`
- openapiv2 method 总数：`N`
- 缺失 method 数：`N`
- 新增 method 数：`N`
- 更新 method 数：`N`
- 高风险接口说明覆盖数：`N`
- 建议项告警数：`N`

## 输出格式（固定回传模板）

执行后按以下结构回传，保证不同会话输出一致：

```markdown
### openapiv2 method 检查结果
- 服务版本：`${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}` 或 `multi-services`
- 执行模式：`incremental|full`
- ruleset_version：`v1`
- gateway_selector_count：`N`
- openapi_method_count：`N`
- missing_methods：`N`（列出 TOP 5）
- extra_methods：`N`（列出 TOP 5）
- missing_fields：`N`（按字段聚合）
- high_risk_violations：`N`
- warnings：`N`
- 结论：`PASS|FAIL`

### 建议修复顺序
1. 先补 `missing_methods`
2. 再补四要素缺失（`tags/summary/description/responses.200.examples`）
3. 最后处理高风险约束与 warning 风格项
```

## 失败后的回退与修复顺序

- 若结果为 FAIL，先输出 `missing_methods` 与 `missing_fields` 的 TOP 列表，再给“最小修复批次”建议（每批不超过 10 个 method）。
- 若增量 FAIL 且涉及规则变更，立即切换全量复核，避免误判为局部问题。
- 若高风险约束失败，优先修复高风险 method 的 `description` 约束说明，再处理普通 method 的风格项。
- 若需临时豁免，必须写入 `ignore-rules.yaml` 并带 `reason/owner/expires_at`，不得口头豁免。

## 常见错误

- 把 gateway 注释中的临时接口误当成 selector
- 用脚本全量覆盖已有 method 文案，导致手写 examples 与业务约束丢失
- `description` 未写接口路径
- `update_mask` 接口未说明“局部更新/全量更新”差异
- 空响应接口写入了不存在的业务字段
- 把前端 `@api` 别名/导入问题误归因到 openapiv2 文档

## Test Prompts（最小验证集）

### Prompt 1：增量检查

- 输入：请只检查 `api/oneops/netdev/v1` 的 openapiv2 method 覆盖，并输出 JSON 报告路径与失败原因摘要。
- 预期：使用增量模式；给出 `missing_methods/missing_fields/high_risk_violations` 统计与结论。

### Prompt 2：全量复核

- 输入：本次升级了检查规则，请对 `api` 下全部服务做全量检查并给修复优先级建议。
- 预期：切换全量模式；输出多服务汇总与“先 missing 再语义”的修复顺序。

### Prompt 3：ignore 过期场景

- 输入：检查 `ignore-rules.yaml` 是否有过期豁免，并确认过期项是否触发 fail-fast。
- 预期：识别过期项不再豁免；报告中体现失败并给出清理建议。

## 参考示例

- Admin 场景实操见 [admin-example.md](admin-example.md)
- oneops/netdev/v1 场景实操见 [netdev-microservice-example.md](netdev-microservice-example.md)
