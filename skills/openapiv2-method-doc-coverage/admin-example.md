# Admin 场景示例（known/admin/v1）

## 目标

将以下文件对齐到同一口径：

- `api/known/admin/v1/admin.proto`
- `api/known/admin/v1/admin.gateway.yaml`
- `api/known/admin/v1/admin.openapiv2.yaml`

## 推荐流程

1. 统计覆盖差异
   - gateway selector 总数
   - openapiv2 method 总数
   - missing method 列表

2. 按资源域补文档
   - 本地配置、认证鉴权、资源管理、作用域管理、策略管理、权限管理
   - 角色管理、部门管理、用户管理、群组管理、安全相关、数据库相关

3. 统一文档格式
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
