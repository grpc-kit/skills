# grpc-kit skills submodule 同步说明

本仓通过 git submodule 管理技能库：

- 路径：`scripts/skills`
- 上游：`https://github.com/grpc-kit/skills.git`

## 首次拉取

```bash
git submodule update --init --recursive
```

## 从上游拉取最新技能（主仓更新指针）

```bash
git submodule update --remote --merge scripts/skills
git add scripts/skills
git commit -m "chore: update skills submodule pointer"
```

## 将本地变更同步到上游（双向同步）

1. 进入 submodule 仓并提交推送：

```bash
cd scripts/skills
git checkout main
git pull --rebase
git add .
git commit -m "docs: update skills"
git push origin main
```

2. 回到主仓提交 submodule 指针：

```bash
cd ../..
git add scripts/skills
git commit -m "chore: bump skills submodule"
```

## 冲突与协作建议

- 先拉取上游再修改，避免双向同步冲突。
- 若 submodule 出现分离头（detached HEAD），先切回 `main` 再提交。
- 主仓代码评审需同时关注：submodule 内变更 + 主仓指针变更。
