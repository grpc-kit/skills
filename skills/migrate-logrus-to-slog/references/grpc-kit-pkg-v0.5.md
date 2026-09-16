# grpc-kit/pkg v0.5 日志契约

本参考用于目标依赖属于 `github.com/grpc-kit/pkg v0.5.x` 的 grpc-kit 微单体。以项目锁定的正式模块版本为准；未来补丁或新目标族不能只凭版本号推断 API 完全一致。

## 已确认的 v0.5.0 基线

- `go.mod` 的 Go 基线为 `1.25.13`。
- `cfg.LocalConfig.GetLogger()` 返回 `*slog.Logger`。
- `errs.Status.WithLogger` 签名为：

```go
func (s *Status) WithLogger(
	ctx context.Context,
	logger *slog.Logger,
	format string,
	err error,
) *Status
```

- RPC、service discovery、auth、audit 等公开 logger 注入点使用 `*slog.Logger`。
- context 是初始化、注册、注销、服务启动和日志链路的一部分；优先传播已有生命周期或请求 ctx。

## 与 project migrate 的分工

`grpc-kit-cli project migrate` 只更新符合所有权规则的托管文件，并报告用户源码中的 logrus、context 和 pkg API ManualAction。本技能处理其中与日志迁移相关的用户源码；两者不能同时改写同一个计划内文件。

建议顺序：

1. preview 并审阅 CLI 的托管文件 Change Plan；
2. 在 clean worktree 使用正式稳定版 CLI 应用托管文件变更；
3. 使用本技能迁移用户源码和测试；
4. 更新 Go/pkg 版本和依赖；
5. 执行生成、测试与构建；
6. 再次 preview，确认剩余 ManualAction 已解释。

CLI 不可用或 apply 条件不满足时，不要伪造 marker 版本。可以继续迁移用户源码，但必须把尚未应用的托管文件变更作为完成阻塞项报告。

## 常见调用迁移

旧调用：

```go
status.WithLogger(logger, "operation failed: %v", err)
```

v0.5.0：

```go
status.WithLogger(ctx, logger, "operation failed: %v", err)
```

ctx 应来自当前请求或生命周期调用链。不要仅为满足签名在 handler、注册或关闭链路中引入 `context.Background()`。

如果 `project migrate` 还报告 `NewMicroservice`、`Init`、`HTTPHandlerFrontend`、`sd.Register`、`Deregister` 或 `StartBackground` 的 context 问题，这些属于更广的 pkg v0.5 兼容迁移；除非用户已授权，否则不要借日志迁移顺带扩展范围。
