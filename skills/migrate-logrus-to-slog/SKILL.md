---
name: migrate-logrus-to-slog
description: 将早期 grpc-kit CLI 生成的 Go 微单体从 logrus 迁移到标准库 log/slog，并完成日志相关的 context 与 pkg API 适配。用于升级存量服务源码；不用于普通日志功能开发或重写第三方生成代码。
---

# 迁移 logrus 到 slog

在目标微单体的 Git 根目录执行迁移。目标是消除项目源码对 logrus 的直接依赖，保留日志级别和控制流语义，并用项目现有验证入口证明迁移结果。

## 开始前

1. 完整读取目标仓库的 `AGENTS.md`、`scripts/env`、`go.mod` 和 `Makefile`；从这些文件确认生成 CLI 版本、目标 pkg 版本、Go 版本和标准验证命令。
2. 检查 `git status --short`。保留无关的已有改动；若已有改动与日志迁移重叠且无法可靠区分，停止并请用户提供 clean worktree 或确认处理方式。
3. 如果当前环境已有兼容的 `grpc-kit-cli`，先运行 `grpc-kit-cli project migrate <root>` 预览。它负责托管文件迁移和 ManualAction 清单；不要为了使用本技能擅自下载、升级 CLI 或直接执行 `--apply`。
4. 读取 [迁移映射](references/mappings.md)。目标依赖属于 `github.com/grpc-kit/pkg v0.5.x` 时，再读取 [pkg v0.5 日志契约](references/grpc-kit-pkg-v0.5.md)。其他版本以目标项目实际依赖源码和正式版本 API 为准。

## 文件所有权

显式请求使用本技能，即授权修改迁移所需的用户管理 Go 源码、测试以及直接依赖声明；不要求这些文件带有 grpc-kit-cli marker。

- 首行带 grpc-kit-cli `DO NOT EDIT` marker、且已进入 `project migrate` Change Plan 的文件，由 CLI 迁移，不重复手工编辑。
- marker 文件未被 CLI 覆盖但确实包含必要迁移时，可以纳入源码迁移；必须在交付报告中列出，并提醒它仍可能被后续模板迁移整体覆盖。
- 不直接修改 protobuf、gRPC、grpc-gateway、OpenAPI、Ent、mock 等第三方生成产物。修改其输入或配置后走项目生成命令。
- `DO NOT EDIT` 不是允许任意生成文件写入的通行证；它只帮助区分所有权和后续覆盖风险。

## 工作流

### 1. 建立清单

扫描非 vendor Go 源码、测试和 `go.mod`，至少识别：

- logrus import、别名和 direct requirement；
- `*logrus.Entry`、`*logrus.Logger`、`FieldLogger` 及跨 package 签名传播；
- package 级 logrus 调用、`WithField(s)`、`WithError`、`Entry.Data`；
- `Debugf`、`Infof`、`Warnf`、`Errorf`、`Fatalf`、`Panicf`、`Tracef`；
- Hook、Formatter、自定义 Level 和第三方 API 对 logrus 类型的要求；
- 日志调用所在作用域是否已有可用的 `context.Context`。

结合 `project migrate` 诊断去重，但不能仅依赖文本命中判断接收者类型。修改前按 package 列出可直接迁移项和需要设计的非等价项。

### 2. 按 package 迁移

从 logger 的创建和注入边界开始，再迁移字段、构造函数、调用方和测试，避免仓库长期停留在两套 logger 类型混用状态。

- 使用 `*slog.Logger` 传播依赖，不为绕过编译而引入 `any` 或临时适配接口。
- 作用域已有请求或生命周期 ctx 时使用 `DebugContext`、`InfoContext`、`WarnContext`、`ErrorContext`；没有真实 ctx 时使用非 Context 方法，不在业务路径中伪造 `context.Background()`。
- 优先把 printf 参数改为稳定的结构化属性。无法可靠推断字段语义时，可以先用 `fmt.Sprintf` 保持输出，但要把该项列入交付报告，不能宣称已经完成高质量结构化迁移。
- 保持 logger 的注入和派生关系；不要把实例 logger 无条件改为 `slog.Default()`。只有旧代码本来使用 package 全局 logger，且项目没有更合适的注入入口时才考虑标准默认 logger。
- 不用全局正则批量替换。每批修改后运行格式化和至少目标 package 的测试或编译检查。

### 3. 处理非等价能力

遇到 Hook、Formatter、动态 `Fields`、`Entry.Data`、自定义 Level、`FieldLogger`、`Fatal`、`Panic`、`Trace` 或第三方 logrus API 时，先确定运行时语义和替代方案。不能证明等价时停止该项并报告，不得静默降级日志、退出或 panic 行为。

日志迁移需要传播 ctx 或适配 `errs.Status.WithLogger` 时可一并修改；其他与日志无关的 pkg v0.5 ManualAction 保持在本技能范围之外，除非用户同时授权更广的项目兼容迁移。

### 4. 清理依赖

确认项目源码、测试、工具代码和受版本控制的生成输入都没有直接 logrus 引用后，才删除 `go.mod` 的 direct requirement 并运行项目约定的 `go mod tidy`。logrus 仍作为第三方模块的传递依赖时，不为追求 `go.sum` 零命中而改写依赖图。

### 5. 验证完成条件

按目标仓库约定执行格式化、生成、测试和构建；grpc-kit 服务通常依次使用：

```sh
gofmt -w <changed-go-files>
make generate
make test
make build
```

仅运行仓库实际存在且与改动相关的目标。生成或测试命令可能修改额外文件时，先检查 Makefile 行为和当前工作区，不能覆盖用户改动。

最后复核：

- 非 vendor、非第三方生成源码中没有直接 logrus import 或标识符；
- `go.mod` 不再直接要求 logrus，或保留原因已经说明；
- 没有意外修改生成文件、文件模式或不相关代码；
- 日志级别、退出/panic 行为和关键字段没有无说明变化；
- 目标 pkg 正式版本下的生成、测试和构建结果明确；
- 再次运行 `project migrate` preview 时，剩余 ManualAction 与报告一致。

## 交付报告

报告迁移 package、logger 构造与注入变化、结构化字段策略、依赖变化、验证命令及结果。单独列出：直接编辑的 marker 文件、仍使用 `fmt.Sprintf` 的兼容日志、未解决的非等价 logrus 能力，以及与本次迁移无关的失败。
