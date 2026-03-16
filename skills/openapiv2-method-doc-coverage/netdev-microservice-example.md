# oneops/netdev/v1 场景示例（microservice）

## 目标

将以下文件对齐到同一口径：

- `api/oneops/netdev/v1/microservice.proto`
- `api/oneops/netdev/v1/microservice.gateway.yaml`
- `api/oneops/netdev/v1/microservice.openapiv2.yaml`

## 推荐流程

1. 统计覆盖差异
   - gateway selector 总数
   - openapiv2 method 总数
   - `missing_methods` / `extra_methods` 列表

2. 按资源域补文档
   - backup、admin、manage、display、topology、audit、firewall
   - 优先补齐高频调用与高风险方法

3. 统一文档格式
   - `tags` 与资源域一致
   - `summary` 使用统一动词风格（创建/获取/更新/删除/列表/查询）
   - `description` 包含接口路径与关键约束
   - `responses.200.examples` 提供最小可读示例

4. 执行脚本复核
   - 增量检查示例：`python scripts/check_openapiv2_method_coverage.py --api-root api --service-glob oneops/netdev/v1 --output-json /tmp/openapiv2-report.json`

## netdev 特殊注意点

- `Demo` 同时存在 `200` 与 `204` 响应语义，建议保留 `200` 示例用于统一门禁校验。
- admin/bastion/graphstore 相关方法在 `description` 中应包含约束词（如：仅允许、脱敏、审计、禁止明文日志）。
- `display/*` 与 `firewall/*` 方法建议统一描述模板：执行命令 -> 返回字段 -> 约束条件。
- backup 相关方法示例优先体现 `successes/errors` 双分支，便于前端消费侧稳定解析。
- 示例 JSON 中涉及敏感字段（密码、令牌、密钥）必须脱敏展示。

## 验收清单

- [ ] gateway selector 与 openapiv2 method 全量对应（`missing_methods == 0` 且 `extra_methods == 0`）
- [ ] 每个 method 都有 `tags/summary/description/responses.200.examples`
- [ ] example JSON 合法且字段命名与 proto 一致
- [ ] 高风险接口（admin/bastion/graphstore）描述包含关键约束
- [ ] Warning 项可控（可读性、跨资源域一致性、示例最小可运行）
