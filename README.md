# skmgr

跨 AI 编码工具的技能统一管理器。支持 Claude Code、OpenCode、Codex 等工具，解决技能在多项目间的复用与管理问题。

## 解决什么问题

- 全局安装所有技能 → 每次会话加载过多，浪费 token
- 每个项目单独安装 → 同一技能多处拷贝，更新维护成本高

skmgr 提供：**中央仓库统一存储 + 按项目按需引用 + 临时技能归档**。

## 安装

```bash
# 方式一：pip 安装
cd skmgr
pip install -e .

# 方式二：直接运行脚本（将目录加入 PATH）
# Windows
skm.cmd --help
# Linux/Mac
./skm.sh --help
```

## 快速开始

```bash
# 1. 从 GitHub 安装技能到全局仓库
skm install https://github.com/anthropics/superpowers-skills

# 2. 查看全局仓库中的技能
skm list

# 3. 在项目中引用技能（自动检测 .claude/ 或 .agents/ 目录）
cd your-project
skm use tdd
skm use debugging

# 4. 查看项目技能状态
skm status
```

## 核心概念

### 三种技能类型

| 类型 | 来源 | `skm sync` 行为 | 说明 |
|------|------|-----------------|------|
| **global** | `skm use` | 重建链接 | 从全局仓库创建 junction 链接 |
| **local** | `skm add` | 跳过 | 从社区直接下载到项目目录 |
| **temp** | `skm mark --temp` | 跳过 | 临时技能，可归档 |

### 目标目录自动检测

根据项目中的标志文件自动判断技能安装到哪个目录：

| 标志 | 目标目录 |
|------|---------|
| `.claude/` 或 `CLAUDE.md` | `.claude/skills/` |
| `.agents/` 或 `AGENTS.md` | `.agents/skills/` |

两个都存在时，技能会同时链接到两个目录。

## 命令参考

### 全局仓库管理

```bash
skm install <url>          # 从 GitHub 安装技能到全局仓库
skm update [name]          # 更新全部或指定技能
skm list                   # 列出全局仓库所有技能
```

### 项目级操作

```bash
skm init                   # 扫描项目已有技能，初始化 .skills.json
skm use <name>             # 从全局仓库链接到项目（type: global）
skm unuse <name>           # 移除链接
skm add <url>              # 从社区直接下载到项目（type: local）
skm sync                   # 根据 .skills.json 重建所有 global 链接
skm status                 # 查看项目技能状态
```

### 技能标记与归档

```bash
skm mark <name> --temp     # 标记为临时技能
skm mark <name> --local    # 改回 local 类型
skm archive <name>         # 归档单个技能
skm archive --all-temp     # 一键归档所有 temp 技能
skm archive --list         # 查看已归档技能
skm restore <name>         # 从存档恢复到项目
```

### 配置

```bash
skm config registry <path>    # 自定义全局仓库路径（默认 ~/.skills-registry）
skm config archive <path>     # 自定义存档目录路径（默认 ~/.skills-archive）
```

## GitHub URL 格式

支持三种格式：

```bash
skm install github:owner/repo
skm install https://github.com/owner/repo
skm install https://github.com/owner/repo/tree/main/path/to/skills
```

## 配置文件

### 全局配置 `~/.skrc.json`

```jsonc
{
  "registry": "~/.skills-registry",
  "archive": "~/.skills-archive"
}
```

### 项目配置 `.skills.json`

```jsonc
{
  "skills": {
    "tdd":        { "type": "global" },
    "my-lib":     { "type": "local", "source": "github:someone/repo" },
    "quick-fix":  { "type": "temp", "created": "2026-04-15" }
  }
}
```

## 典型工作流

### 跨项目复用技能

```bash
# 一次安装到全局
skm install github:anthropics/superpowers-skills

# 不同项目按需引用
cd project-a && skm use tdd && skm use debugging
cd project-b && skm use tdd && skm use brainstorming
```

### 临时技能管理

```bash
# 手动创建临时技能
mkdir .claude/skills/quick-fix
vim .claude/skills/quick-fix/skill.md

# 标记为临时
skm mark quick-fix --temp

# 用完后归档
skm archive quick-fix

# 需要时恢复
skm restore quick-fix
```

### 已有项目初始化

```bash
# 项目中已有技能但没有 .skills.json
cd existing-project
skm init       # 自动扫描并生成 .skills.json
skm status     # 查看结果
```
