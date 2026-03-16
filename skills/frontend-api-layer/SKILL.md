---
name: frontend-api-layer
description: 通用前端 API 层技能。用于将 api 定义稳定映射到前端 src/api，并统一业务侧 @api 引用、迁移规则与验收门禁。
---

# 前端 API 层（src/api）通用规范

## 目标

将接口定义目录 `api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}` 一一映射到前端目录 `${FRONTEND_ROOT}/src/api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}`，并统一业务代码仅通过 `@api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}` 引用。

## 适用场景

- 新增或变更 `api/*/*/*` 服务版本定义（proto/gateway）
- 需要生成或校验 `client.ts`、`types.ts`、`index.ts`
- 迁移历史页面引用到统一 `@api/...` 路径
- 排查 `@api` 别名不生效或深链引用（`/client`、`/types`）问题

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

## 快速检查命令（按仓调整前端根路径）

- 深链扫描：
  - `rg "@api/.*/(types|client)" ${FRONTEND_ROOT}/src/pages`
- `@api` 使用面扫描：
  - `rg "@api/" ${FRONTEND_ROOT}/src/pages`
- 别名配置扫描：
  - `rg "\"@api/\\*\"\\s*:\\s*\\[\"\\./src/api/\\*\"\\]" ${FRONTEND_ROOT}/tsconfig*.json`
  - `rg "@api\\s*.*src/api|find:\\s*\"@api\"" ${FRONTEND_ROOT}/vite.config.ts`

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
