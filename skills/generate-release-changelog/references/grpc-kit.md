# grpc-kit 发布约定

仅在目标为 grpc-kit 工作区、grpc-kit CLI 生成的微服务，或仓库存在明确的 `pkg/api/cli` 布局时读取本文件。

## grpc-kit 多仓工作区

- 工作区根目录可能不是 Git 仓库；`pkg`、`api`、`cli` 分别是独立 Git 仓库。
- 变更日志通常位于 `cli/CHANGELOG/CHANGELOG-0.x.md`，按 `grpc-kit/pkg 模块`、`grpc-kit/api 模块`、`grpc-kit/cli 模块` 分组。
- 以 `pkg` 的目标版本 tag 作为主发布边界。先确认上一个和目标 tag 的日期及提交范围。
- `api` 或 `cli` 缺少同名 tag 时，以主发布窗口筛选候选提交，并逐项核对提交日期、具体 diff、生成代码和 `pkg` 中内嵌 API 的同步情况。不得仅凭日期自动纳入。
- 对各独立仓库分别执行 `git status`、`git log` 和 `git diff`。

重点检查：

- `api/**/*.proto`、`*.gateway.yaml`、`*.openapiv2.yaml` 与 Swagger 变化。
- `pkg/api/**` 生成代码是否与 `api` 契约同步。
- `pkg/admin`、`pkg/auth`、`pkg/cfg`、`pkg/rpc` 和 `pkg/mcp` 的用户可见行为与安全边界。
- `cli/template/service/**` 对新生成微服务的 Go 版本、依赖、生成流程和扩展点影响。

## grpc-kit CLI 生成的微服务

- 将服务根目录视为单一 Git 仓库，除非项目另有独立 submodule 需要纳入发布。
- 默认变更日志为根目录 `CHANGELOG.md`，版本线索来自根目录 `VERSION`、Git tag 和 `scripts/env`。
- `VERSION` 或 `scripts/env` 中的版本不等于已发布；目标 tag 不存在时默认更新 `Unreleased`。
- API 契约位于 `api/${PRODUCT_CODE}/${SHORT_NAME}/${API_VERSION}`；同时检查 handler、modeler、config、deploy、web 和文档变更。
- `scripts/skills` 是共享技能 submodule，不应把技能库自身的更新逐项写入微服务发布日志；仅记录技能更新对服务交付流程造成的用户可见变化。

## 分类提示

- Proto/RPC 新增通常归入 `Added`。
- RPC/字段重命名、删除和行为变化归入 `Changed` 或 `Removed`，并写迁移动作。
- 认证、授权、MFA、Token、凭证和越权边界变化归入 `Security`；同一事项不必在多个分类重复描述。
- CLI 模板中的依赖升级、Go 版本调整和生成命令变化归入 `Changed`。
