# SKMGR - AI Coding Tool Skill Manager

## Project Overview

跨 AI 编码工具（Claude Code、OpenCode、Codex 等）的技能统一管理工具。核心解决：中央仓库统一存储 + 按项目按需引用，避免技能重复拷贝和全局加载浪费 token。

## Architecture

```
~/.skills-registry/          # 全局中央仓库（路径可通过 ~/.skrc.json 自定义）
  ├── registry.json          # 技能元数据索引
  └── <skill-name>/          # 各技能目录

~/.skills-archive/           # 技能存档目录（路径可通过 ~/.skrc.json 自定义）
  └── <skill-name>/          # 归档的技能

项目/.skills.json            # 项目技能引用清单
项目/.claude/skills/         # Claude Code 技能目录（junction 链接或本地文件）
项目/.agents/skills/         # OpenCode/Codex 技能目录（junction 链接或本地文件）
```

### 三种技能类型

- **global**（`skm use`）：从全局仓库创建 Windows junction 链接，`skm sync` 会重建
- **local**（`skm add`）：从社区直接下载到项目目录，记录到 `.skills.json` 但 `skm sync` 跳过
- **temp**（`skm mark --temp`）：临时技能，可通过 `skm archive` 归档

### 目标目录自动检测

根据项目中是否存在 `.claude/` / `CLAUDE.md` 或 `.agents/` / `AGENTS.md` 自动判断技能安装到哪个目录，两个都存在则都链接。

## Project Structure

```
skmgr/
├── pyproject.toml       # 入口点: skm = skmgr.cli:main
├── skm.cmd              # Windows 直接调用脚本
├── skm.sh               # Linux/Mac 直接调用脚本
└── src/
    ├── __init__.py
    ├── cli.py           # argparse CLI 入口，子命令分发
    ├── config.py        # 全局配置 (~/.skrc.json) 读写
    ├── github.py        # GitHub URL 解析、仓库克隆、技能识别
    ├── linker.py        # Windows junction / symlink 操作
    ├── project.py       # 项目级操作 (init/use/unuse/add/sync/status/mark/archive/restore)
    └── registry.py      # 全局仓库操作 (install/update/list)
```

## Commands

| 命令 | 说明 |
|------|------|
| `skm init` | 扫描项目已有技能，初始化 `.skills.json` |
| `skm install <url>` | 从 GitHub 安装技能到全局仓库 |
| `skm update [name]` | 更新全局仓库中的技能 |
| `skm list` | 列出全局仓库所有技能 |
| `skm use <name>` | 全局仓库 → 项目（junction 链接，type: global） |
| `skm unuse <name>` | 移除项目中的链接 |
| `skm add <url>` | 社区 → 项目（直接下载，type: local） |
| `skm sync` | 重建所有 global 链接，跳过 local 和 temp |
| `skm status` | 查看当前项目技能状态 |
| `skm mark <name> --temp/--local` | 标记技能类型 |
| `skm archive <name>` | 归档技能到存档目录 |
| `skm archive --all-temp` | 一键归档所有 temp 技能 |
| `skm archive --list` | 列出已归档技能 |
| `skm restore <name>` | 从存档恢复技能到项目 |
| `skm config registry <path>` | 自定义全局仓库路径 |
| `skm config archive <path>` | 自定义存档目录路径 |

## Key Design Decisions

- Windows 使用 directory junction（`mklink /J`），不需要管理员权限
- `.git` 目录删除需要先 `os.chmod` 处理只读文件（`_force_rmtree`）
- GitHub URL 支持三种格式：`github:owner/repo`、完整 URL、带 tree/branch/path 的子目录 URL
- 技能识别规则：目录中包含 `.md` 文件即视为一个技能

## Development

```bash
# 方式一：pip 安装
pip install -e .
skm --help

# 方式二：直接运行脚本（无需安装，将目录加入 PATH 即可）
# Windows
skm.cmd --help
# Linux/Mac
./skm.sh --help
```
