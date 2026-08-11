---
name: generate-release-changelog
description: 根据单仓库、Monorepo 或多个 Git 模块在两个版本引用之间的实际代码变更，生成或更新 Markdown 发布变更日志。用于整理版本发布说明、更新 CHANGELOG、汇总上次发布至当前版本的变更，以及标明破坏性 API 迁移和安全影响。
---

# 生成发布变更日志

## 输入与发现

按以下顺序确定输入，能够从仓库可靠发现时不要询问用户：

1. `REPO_ROOT`：用户指定目录，否则使用当前 Git 仓库根目录。
2. `CHANGELOG_FILE`：用户指定文件优先；否则依次检查根目录 `CHANGELOG.md`、`CHANGELOG/` 和项目文档约定。
3. `FROM_REF`：用户指定引用优先；否则使用目标版本之前最近的稳定 SemVer tag。
4. `TO_REF`：用户指定引用或已存在的目标版本 tag；尚未打 tag 时使用 `HEAD`。
5. `RELEASE_MODE`：目标 tag 已存在或用户明确要求发布版本时为 `release`，否则为 `unreleased`。
6. `COMPONENTS`：仅在用户指定或仓库确有多个可独立描述的组件时设置。

读取仓库内适用的 `AGENTS.md`、现有 CHANGELOG、`VERSION` 和发布脚本。`VERSION` 可作为目标版本线索，但不能单独证明该版本已发布。

## 工作流

### 1. 确认仓库拓扑

- 使用 `git rev-parse --show-toplevel` 判断当前目录所属仓库。
- 默认按单仓库处理；只有组件存在独立 `.git` 边界时才按多仓库处理。
- Monorepo 内共享同一 Git 历史的组件使用同一版本范围，并通过路径过滤收集变更。
- 多个独立仓库分别确定可验证的起止引用。不要假定它们具有同名 tag 或同步的 `HEAD`。
- 检测到 grpc-kit 工作区、grpc-kit CLI 生成的微服务或 `pkg/api/cli` 布局时，读取 [references/grpc-kit.md](references/grpc-kit.md)。

### 2. 确认版本范围和日期

- 优先使用明确的 `<FROM_REF>..<TO_REF>`，并确认两个引用属于对应仓库。
- 目标 tag 不存在时，将结果保留在 `Unreleased`；不要伪造正式发布日期。
- 正式版本日期使用目标 tag 的 tagger/commit 日期或明确的发布提交日期。
- 独立协同仓库缺少对应 tag 时，使用主发布窗口筛选候选提交，再检查具体 diff 和依赖引用以确认是否属于本次发布；在无法建立可靠边界时向用户说明不确定性。
- 排除目标版本之后的提交、未获授权的工作区改动和其他未发布分支内容。

### 3. 收集证据

- 先检查每个仓库的 `git status --short`，保留用户已有改动。
- 使用 `git log --no-merges` 收集提交主题，必要时检查 merge commit 和 Conventional Commits 的 `!` / `BREAKING CHANGE`。
- 使用 `git diff --stat` 建立变更面，再按关键路径查看具体 diff。
- 检查接口契约、配置、数据库迁移、命令行、运行时行为、部署清单、依赖、文档和生成模板等用户可见表面。
- 以代码 diff、测试和文档相互印证；不要只根据提交标题生成结论。

### 4. 提炼发布记录

- 遵循现有 CHANGELOG 的语言、标题层级和分类；没有约定时使用 `Added`、`Changed`、`Deprecated`、`Removed`、`Fixed`、`Security`。
- 记录用户、调用方和运维人员可感知的行为；合并纯重构、测试补充、生成代码和版本号提交。
- 单仓微服务直接按分类列项。只有多个组件对理解变更确有帮助时才增加组件标题。
- 对新增或调整的 API，写明方法或字段、适用主体与主要能力。
- 对破坏性改动，明确旧接口、替代接口和迁移动作；不要用“优化”掩盖删除、重命名或行为收紧。
- 将认证、授权、凭证、敏感数据暴露和越权修复归入 `Security`；普通稳定性问题归入 `Fixed`。
- 只描述证据可以证明的事实，不输出密钥、令牌、密码或其他敏感内容。

### 5. 写入和验证

- `release` 模式：在 `Unreleased` 后、上一版本前插入 `## [x.y.z] - YYYY-MM-DD`，保持版本倒序。
- `unreleased` 模式：更新现有 `Unreleased` 内容，不创建带日期的正式版本。
- 不重写历史版本，不覆盖用户已有的无关改动。
- 执行 `git diff --check -- <CHANGELOG_FILE>`，复核新增内容与确定的版本范围一致。
- 交付时报告 CHANGELOG 路径、版本范围、仓库拓扑、验证结果和必须执行的迁移动作。

## 推荐检查命令

```sh
git -C "${REPO_ROOT}" rev-parse --show-toplevel
git -C "${REPO_ROOT}" status --short
git -C "${REPO_ROOT}" tag --list --sort=version:refname
git -C "${REPO_ROOT}" log --no-merges --oneline "${FROM_REF}..${TO_REF}"
git -C "${REPO_ROOT}" diff --stat "${FROM_REF}..${TO_REF}"
git -C "${REPO_ROOT}" diff "${FROM_REF}..${TO_REF}" -- path/to/important/file
git -C "${REPO_ROOT}" diff --check -- "${CHANGELOG_FILE}"
```

## 最小输出示例

单仓微服务：

```markdown
## [0.4.3] - 2026-08-11

### Added

- 新增用户资料查询接口。

### Changed

- 访问令牌参数由 `appid` 调整为 `client_id`；调用方需要迁移请求字段。

### Fixed

- 修复服务关闭时会话未正确释放的问题。
```

多组件项目可在分类下增加组件标题，但不要创建空分类或空组件。

## 常见错误

- 将单仓微服务误判为多个独立 Git 仓库。
- 将不同仓库的 `HEAD` 一律当作同一次发布。
- 目标 tag 不存在时仍生成带日期的正式版本。
- 只依据提交主题，遗漏接口契约、配置、迁移或模板中的兼容性变化。
- 将破坏性改动和权限收紧写成笼统的“优化”。
- 将测试、生成代码或版本号提交逐条写入用户变更日志。
- 覆盖 `Unreleased`、历史版本或用户已有的无关改动。
