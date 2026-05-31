# Admin 场景示例（known/admin/v1）

## 目标

将以下文件对齐到同一口径：

- `api/known/admin/v1/admin.proto`
- `api/known/admin/v1/admin.gateway.yaml`
- `api/known/admin/v1/admin.openapiv2.yaml`

## 推荐流程

1. 先执行 preserve-and-fill 同步
   - `python skills/openapiv2-method-doc-coverage/scripts/sync_openapiv2_methods.py --gateway-file api/known/admin/v1/admin.gateway.yaml --openapi-file api/known/admin/v1/admin.openapiv2.yaml`
   - 目标：先把 gateway 中缺失的 method skeleton 补齐，同时保留已有人工文案

2. 统计覆盖差异
   - gateway selector 总数
   - openapiv2 method 总数
   - missing method 列表

3. 按资源域补文档
   - 本地配置、认证鉴权、资源管理、作用域管理、策略管理、权限管理
   - 角色管理、部门管理、用户管理、群组管理、安全相关、数据库相关

4. 统一文档格式
   - `tags` 与资源域一致
   - `summary` 使用统一动词风格（创建/获取/更新/删除/列表/绑定）
   - `description` 含“接口格式：<path>”和关键约束
   - `responses.200.examples` 提供最小可读示例

## Admin 特殊注意点

- OAuth2 相关路由当前为 `oatuh2`（历史拼写），文档需显式提示，避免误调用 `oauth2`。
- 多个更新接口使用 `{resource.id}`、`{role.id}` 等点号参数，路径与请求体 ID 需一致。
- 列表接口需说明分页 oneof 语义：`page_token` 与 `offset` 不同时使用。
- 删除与部分绑定接口返回空响应，示例保持 `{}`。

## 验收清单

- [ ] gateway selector 与 openapiv2 method 全量对应
- [ ] 每个 method 都有 `tags/summary/description/examples`
- [ ] example JSON 合法且字段命名与 proto 一致
- [ ] 认证、密码、授权变更接口描述完整
- [ ] 无跨资源域枚举值混用

## 当前 admin 样本验证

- 2026-05-31 首次用同步脚本验证：admin 已达到 `gateway_selector_count = 74`、`openapi_method_count = 74`、`missing_methods = 0`
- 补齐高风险接口约束说明后，`high_risk_violations = 0`，当前 admin 样本已满足覆盖率与高风险说明门禁
