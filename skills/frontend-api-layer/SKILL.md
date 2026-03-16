---
name: frontend-api-layer
description: 通用前端 API 层技能。用于将 api 定义稳定映射到前端 src/api，并统一业务侧 @api 引用、迁移规则与验收门禁。只要用户提到“新增/变更 gateway 或 proto”“生成或修复 src/api 下 client/types/index”“把页面引用迁移到 @api/... 统一入口”“排查 @api 别名或深链导入问题”，即使用户没明确说“请使用 frontend-api-layer”，也应优先触发本技能。
---

# 前端 API 层（src/api）通用规范

## 目标

将接口定义目录 `api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}` 一一映射到前端目录 `${FRONTEND_ROOT}/src/api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}`，并统一业务代码仅通过 `@api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}` 引用。

## 适用场景

- 新增或变更 `api/*/*/*` 服务版本定义（proto/gateway）
- 需要生成或校验 `client.ts`、`types.ts`、`index.ts`
- 迁移历史页面引用到统一 `@api/...` 路径
- 排查 `@api` 别名不生效或深链引用（`/client`、`/types`）问题

## 触发信号（用于判断应触发本技能）

- 用户说“帮我根据 gateway/proto 生成前端 API 层代码”
- 用户说“`src/api` 下这组接口要补齐 `client.ts/types.ts/index.ts`”
- 用户说“把页面里旧 API 引用迁到 `@api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}`”
- 用户说“为什么 `@api` 别名不生效/为什么有人在深链导 `@api/.../client`”
- 用户说“我要做 API 版本升级（如 `v1 -> v2`）并校验引用是否干净”

## 术语与输入输出边界

- `${PRODUCT_CODE}`：产品/命名空间（如 `known`、`oneops`）
- `${SHORT_NAME}`：服务简称（如 `admin`、`netdev`）
- `${API_VERSION}`：接口版本（如 `v1`）
- `${FRONTEND_ROOT}`：前端项目根目录（如 `web/admin`、`adm/vite-antd`）
- 输入源：`api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}` 下的 `*.gateway.yaml`、`*.proto`
- 固定输出：`${FRONTEND_ROOT}/src/api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}`
- 输出文件仅限：`client.ts`、`types.ts`、`index.ts`
- 禁止在 `src/api/**` 放置业务编排、鉴权逻辑、页面状态处理

## 前端 API 生成最小规范（必遵守）

1. 目录必须一一对应：`api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}` -> `${FRONTEND_ROOT}/src/api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}`。
2. 有 `*.gateway.yaml` 必生成 `client.ts`；有 `*.proto` 必生成 `types.ts`；`index.ts` 统一导出。
3. `index.ts` 固定为自动生成文件：`// AUTO-GENERATED. DO NOT EDIT.`，仅导出 `./client` 与/或 `./types`。
4. 业务代码统一从 `@api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}` 引入，不深链 `client.ts/types.ts`。
5. `client.ts` 必须逐条覆盖 gateway 规则：method/path/path 参数/query/body 映射一致。
6. `additional_bindings` 必须生成独立函数，不可省略。
7. `body: "*"` 传整个对象；`body: "field"` 仅传该字段值。
8. 生成函数命名保持稳定且可读（推荐：`{product}{service}API{RpcName}`）。
9. `types.ts` 由同目录所有 proto 聚合生成，禁止手写业务类型混入。
10. `int64/uint64` 统一映射 `number | string`（建议别名 `Int64Like`）。
11. `google.protobuf.Timestamp` 统一映射 `string`（建议别名 `TimestampLike`）。
12. 外部 proto 类型优先复用现有 `@api/...`，缺失时允许占位并标注 TODO。
13. `src/api/**` 只放接口与类型；加密、token、业务编排放页面或 `src/services/**`。
14. 迁移期可加兼容别名，但需设退场条件；旧 API 文件删除前必须全局 0 引用。
15. 验收至少包含：selector 覆盖（含 additional_bindings）、引用切换完成、无新增本次改动相关类型错误。

## 核心规则的 why（避免机械套规则）

- 规则 3（`index.ts` 自动生成头 + 仅导出）是为了让入口稳定可预测，减少人工改动造成的导出漂移。
- 规则 4（业务统一从 `@api/...` 引入）是为了把调用面收敛到单入口，后续版本迁移和批量替换才可控。
- 规则 6（`additional_bindings` 独立函数）是为了保证 gateway 暴露的每条可达路由都可独立调用和回归。
- 规则 10/11（`int64/uint64`、`Timestamp` 映射约束）是为了减少前端运行时精度/序列化歧义。
- 规则 14（兼容别名必须有退场条件）是为了避免“临时兼容”长期固化成隐性技术债。

## Import 迁移规约（重点）

### 允许写法

- `@api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}`

### 禁止写法

- 深链导入：`@api/.../client`、`@api/.../types`
- 迁移完成后继续新增旧平铺 API 文件引用（如 `src/api/*.ts`、`src/api/*.tsx`）

### 兼容别名策略

- 迁移期允许在 `client.ts` 末尾集中放置 `compatibility aliases`。
- 每个兼容别名必须可追踪真实 API 函数，并记录退场条件：
  - 页面完成迁移
  - 全局 0 引用
  - 删除兼容别名

## 别名配置校验（仓内）

- `${FRONTEND_ROOT}/tsconfig.json` 与 `${FRONTEND_ROOT}/tsconfig.app.json` 包含：
  - `"@api/*": ["./src/api/*"]`
- `${FRONTEND_ROOT}/vite.config.ts`（或同类构建配置）包含：
  - `@api -> ./src/api`

## 标准执行步骤

1. 定位输入定义：`api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}`。
2. 在 `${FRONTEND_ROOT}/src/api` 创建或更新同路径目录。
3. 按规则生成或校验 `client.ts`、`types.ts`、`index.ts`。
4. 扫描并迁移业务引用到统一入口 `@api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}`。
5. 保留必要兼容别名并登记退场条件。
6. 输出本次迁移差异报告。

## 质量门禁（必须通过）

- Gate 1: `gateway selector` 与 `client.ts` 函数覆盖一一对应，`additional_bindings` 不缺失。
- Gate 2: `types.ts` 覆盖同目录全部 proto，且无手写业务类型混入。
- Gate 3: `index.ts` 仅自动导出，包含 `AUTO-GENERATED` 头。
- Gate 4: 别名配置一致（构建配置 + tsconfig）。
- Gate 5: 业务页零深链，不再出现 `@api/.../types|client`。
- Gate 6: 无新增本次改动相关类型错误。

## Gate 通过/失败最小示例

- Gate 1（selector 覆盖）
  - 通过：`foo.gateway.yaml` 有 3 条规则（含 1 条 `additional_bindings`），`client.ts` 有 3 个对应函数。
  - 失败：gateway 有 `additional_bindings`，但 `client.ts` 只生成主规则函数。
- Gate 2（types 聚合）
  - 通过：同目录 2 个 proto 的消息类型都在 `types.ts` 可见。
  - 失败：`types.ts` 手写了页面专用类型或漏了某个 proto 的导出。
- Gate 3（index 自动导出）
  - 通过：`index.ts` 含 `// AUTO-GENERATED. DO NOT EDIT.` 且仅导出 `./client`/`./types`。
  - 失败：`index.ts` 出现手写业务函数或缺少自动生成头。
- Gate 4（别名配置）
  - 通过：`tsconfig*.json` 与 `vite.config.ts` 同时存在 `@api -> ./src/api` 映射。
  - 失败：仅 tsconfig 有 `@api`，构建配置未声明导致运行时报错。
- Gate 5（零深链）
  - 通过：业务代码仅 `import {...} from '@api/.../v1'`。
  - 失败：仍存在 `@api/.../client` 或 `@api/.../types` 引用。
- Gate 6（类型健康）
  - 通过：改动后无新增本次 API 迁移相关 TS 类型错误。
  - 失败：新增 `response_body` 相关类型不兼容且未修复。

## 异常与回退策略

- 场景 1：只有 gateway、缺失 proto
  - 处理：先生成 `client.ts`，`types.ts` 仅保留可确定类型 + TODO；记录缺失来源并阻塞“完成态”验收。
- 场景 2：只有 proto、缺失 gateway
  - 处理：先生成 `types.ts`，`client.ts` 不伪造；在差异报告中标注待补 selector。
- 场景 3：跨仓读取到多个冲突版本定义
  - 处理：以目标 `api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}` 为唯一输入边界，冲突项落 TODO 并提示人工确认。
- 场景 4：`@api` 别名配置冲突（tsconfig 与构建配置不一致）
  - 处理：先统一别名，再执行引用迁移；避免“编译通过但运行失败”的假阳性。
- 场景 5：迁移后仍有旧文件引用
  - 处理：先保留兼容别名并统计残余引用，达到全局 0 引用后再删除旧文件。

## 快速检查命令（按仓调整前端根路径）

- 深链扫描：
  - `rg "@api/.*/(types|client)" ${FRONTEND_ROOT}/src/pages`
- `@api` 使用面扫描：
  - `rg "@api/" ${FRONTEND_ROOT}/src/pages`
- 别名配置扫描：
  - `rg "\"@api/\\*\"\\s*:\\s*\\[\"\\./src/api/\\*\"\\]" ${FRONTEND_ROOT}/tsconfig*.json`
  - `rg "@api\\s*.*src/api|find:\\s*\"@api\"" ${FRONTEND_ROOT}/vite.config.ts`

## 端到端示例（输入 -> 输出）

- 输入服务版本：`known/admin/v1`
- 输入目录：
  - `api/known/admin/v1/admin.gateway.yaml`
  - `api/known/admin/v1/admin.proto`
- 预期输出目录：`${FRONTEND_ROOT}/src/api/known/admin/v1`
- 预期输出文件：
  - `client.ts`：包含 `knownAdminAPIListUsers`（主规则）与 `knownAdminAPIListUsersByOrg`（来自 `additional_bindings`）等函数
  - `types.ts`：聚合 `admin.proto` 中 `ListUsersRequest/ListUsersResponse` 等类型
  - `index.ts`：仅自动导出 `./client` 与 `./types`
- 业务侧迁移：
  - 迁移前：`import { knownAdminAPIListUsers } from '@api/known/admin/v1/client'`
  - 迁移后：`import { knownAdminAPIListUsers } from '@api/known/admin/v1'`

## Test Cases（最小回归集）

### Case 1：新增服务版本生成

- Prompt：新增 `api/known/admin/v1` 的 gateway/proto，请生成 `src/api/known/admin/v1` 三件套并给出验收差异报告。
- 预期产物：
  - 生成 `client.ts/types.ts/index.ts`
  - `additional_bindings` 有独立函数
  - 差异报告含新增函数数、bindings 覆盖数

### Case 2：存量引用迁移

- Prompt：把 `web/admin/src/pages` 中 `@api/.../client|types` 深链导入迁到统一 `@api/.../v1`，保留必要兼容别名并给退场条件。
- 预期产物：
  - 页面侧深链归零
  - 兼容别名集中在 `client.ts` 末尾并带退场说明
  - 输出残余引用统计

### Case 3：别名排障

- Prompt：`@api` 在 IDE 能跳转但 Vite 运行时报错，请检查并修复 tsconfig 与构建配置别名一致性，同时复核业务引用是否规范。
- 预期产物：
  - `tsconfig*.json` 与 `vite.config.ts` 别名一致
  - 无新增 `@api/.../client|types` 深链
  - 无新增本次改动相关类型错误

## Description Optimization（触发描述优化）

### 触发评估模板（最小集）

```json
[
  {
    "query": "我们刚在 api/known/admin/v1 加了 gateway 和 proto，帮我把 web/admin 里的 src/api 产物补齐并检查 additional_bindings 有没有漏。",
    "should_trigger": true
  },
  {
    "query": "把页面里所有 @api/known/admin/v1/client 的导入改成统一入口，并给我迁移完成后的残余深链统计。",
    "should_trigger": true
  },
  {
    "query": "为什么 @api 别名在 tsconfig 里有，但 vite 跑不起来？顺便检查业务代码有没有深链 @api/.../types。",
    "should_trigger": true
  },
  {
    "query": "admin 服务从 v1 升到 v2，要求 API 层目录映射、引用迁移和门禁检查一次完成。",
    "should_trigger": true
  },
  {
    "query": "帮我写一个 React 表单页面并接入现有接口。",
    "should_trigger": false
  },
  {
    "query": "把这个页面的按钮样式改成主题色，顺便优化布局。",
    "should_trigger": false
  },
  {
    "query": "给我排查登录 token 为什么过期，不需要改 src/api。",
    "should_trigger": false
  },
  {
    "query": "写一个 Node 脚本批量压缩图片资源。",
    "should_trigger": false
  }
]
```

### 使用方式

1. 每次修改 `description` 后，至少用上述 8 条查询回放一轮触发判断。
2. 若 should-trigger 命中不足，优先补充触发语句中的“任务动作词”（生成/迁移/校验/排障）。
3. 若 should-not-trigger 误触发，收紧描述中与页面业务开发重叠的措辞，明确仅聚焦 `src/api` 生成与迁移。

## 补充落地规范

1. `any` 使用约束：仅在外部依赖未接入或无法可靠推导时允许 `any`/`Record<string, any>`/`as any`，并标注 `TODO(来源 proto/gateway)`；禁止无注释放宽类型。
2. 字段可选性统一：同一服务版本内必须采用统一字段策略（建议默认可选）；不得为适配单页临时改成局部特例。
3. `response_body/body:field` 推导：优先推导到具体字段类型；无法推导时降级 `unknown`，避免直接 `any`。
4. 兼容别名治理：统一放在 `client.ts` 末尾 `// compatibility aliases` 区块，记录迁移目标与退场条件。
5. 跨仓输入边界：允许跨仓读取接口定义，但输出路径必须固定在当前仓 `${FRONTEND_ROOT}/src/api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}`。
6. 验收差异报告：每次生成后补充简要统计（新增/变更函数数、`additional_bindings` 覆盖数、兼容别名数、删除旧 API 文件清单）。

## 验收产物模板（每次生成/迁移后补充）

- 服务版本：`${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}`
- 新增函数数：`N`
- 变更函数数：`N`
- `additional_bindings` 覆盖数：`N`
- 兼容别名数：`N`
- 深链引用剩余数（`@api/.../types|client`）：`N`
- 待删除旧 API 文件清单：`[]`
