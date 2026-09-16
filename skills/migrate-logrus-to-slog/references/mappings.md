# logrus → slog 迁移映射

这些映射是起点，不是无条件文本替换规则。先确认接收者类型、ctx 来源和控制流语义。

## 类型与创建

| logrus | slog | 注意事项 |
|---|---|---|
| `*logrus.Entry` | `*slog.Logger` | 同步修改字段、参数、返回值和测试夹具 |
| `*logrus.Logger` | `*slog.Logger` | 先迁移 formatter/hook/output/level 配置 |
| `logrus.NewEntry(logrus.New())` | 项目 logger 工厂或 `slog.New(handler)` | 不要默认丢失输出、级别和格式配置 |
| package 全局 logger | `slog.Default()` | 仅用于旧代码本来就是全局 logger 的情况 |

logger 允许为 nil 时，先查项目是否已有 fallback helper；不要假设 slog 方法能在 nil receiver 上工作。

## 字段和派生 logger

```go
// before
logger.WithError(err).WithField("request_id", id).Error("request failed")

// after
logger.Error("request failed",
	slog.String("request_id", id),
	slog.Any("error", err),
)
```

需要复用字段时派生 logger：

```go
logger = logger.With(
	slog.String("component", component),
	slog.String("request_id", id),
)
```

- 静态 `logrus.Fields` 展开为 slog attributes 或交替的 key/value 参数。
- 动态 map、重复键和非字符串键需要逐项确认顺序与覆盖语义。
- `Entry.Data` 没有直接等价公开字段；显式维护属性或重新设计封装。

## 日志调用

| logrus | 有 ctx | 无 ctx |
|---|---|---|
| `Debug` / `Debugf` | `DebugContext` | `Debug` |
| `Info` / `Infof` | `InfoContext` | `Info` |
| `Warn` / `Warnf` | `WarnContext` | `Warn` |
| `Error` / `Errorf` | `ErrorContext` | `Error` |

优先将：

```go
logger.Errorf("request %s failed: %v", id, err)
```

迁移为：

```go
logger.ErrorContext(ctx, "request failed",
	slog.String("request_id", id),
	slog.Any("error", err),
)
```

如果字段名称或格式化行为不能可靠判断，先保持文本兼容：

```go
logger.ErrorContext(ctx, fmt.Sprintf("request %s failed: %v", id, err))
```

这种结果已经移除 logrus，但仍需在交付报告中标记为非结构化兼容日志。

## 无直接等价的行为

- `Fatal*`：logrus 通常记录后调用 `os.Exit(1)`；slog 没有 Fatal API。必须显式设计由谁退出及如何测试。
- `Panic*`：必须保留 panic 值和日志顺序，不能只替换成 `Error`。
- `Trace*`：slog 没有内置 Trace level；使用项目自定义 level 前确认 handler 是否启用和如何展示。
- Hook：评估迁移到 `slog.Handler` 包装、日志管道或独立副作用组件。
- Formatter：迁移到 `TextHandler`、`JSONHandler` 或项目自定义 Handler，并核对时间、level、source 和属性编码。
- `FieldLogger`：改为具体 `*slog.Logger` 或项目自己的最小接口，不能假设两者方法集兼容。
- `WithContext`：slog 的 logger 不保存 ctx；在每次 Context 日志调用时显式传递。

## 检查重点

迁移后特别检查错误是否作为结构化值保留、敏感字段是否仍被过滤、派生 logger 是否丢失公共属性，以及测试是否错误地依赖 logrus 的文本格式。
