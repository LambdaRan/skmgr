"""CLI entry point for sk command."""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="skm",
        description="AI coding tool skill manager",
    )
    sub = parser.add_subparsers(dest="command")

    # skm init
    sub.add_parser("init", help="Scan existing skills and initialize .skills.json")

    # skm install <url>
    p_install = sub.add_parser("install", help="Install skills from GitHub to global registry")
    p_install.add_argument("url", help="GitHub URL (e.g. github:owner/repo or https://github.com/owner/repo)")

    # sk update [skill]
    p_update = sub.add_parser("update", help="Update skills in global registry")
    p_update.add_argument("skill", nargs="?", default=None, help="Skill name (omit to update all)")

    # sk list
    sub.add_parser("list", help="List all skills in global registry")

    # sk use <skill>
    p_use = sub.add_parser("use", help="Link a skill from registry to current project")
    p_use.add_argument("skill", help="Skill name")

    # sk unuse <skill>
    p_unuse = sub.add_parser("unuse", help="Remove a skill link from current project")
    p_unuse.add_argument("skill", help="Skill name")

    # sk add <url>
    p_add = sub.add_parser("add", help="Install a skill directly into current project from GitHub")
    p_add.add_argument("url", help="GitHub URL")

    # sk sync
    sub.add_parser("sync", help="Rebuild global skill links from .skills.json")

    # sk status
    sub.add_parser("status", help="Show skills in current project")

    # skm mark <skill> --temp/--local
    p_mark = sub.add_parser("mark", help="Mark a skill's type (temp or local)")
    p_mark.add_argument("skill", help="Skill name")
    mark_group = p_mark.add_mutually_exclusive_group(required=True)
    mark_group.add_argument("--temp", action="store_true", help="Mark as temporary")
    mark_group.add_argument("--local", action="store_true", help="Mark as local")

    # skm archive <skill> / --all-temp
    p_archive = sub.add_parser("archive", help="Archive skills to archive directory")
    archive_group = p_archive.add_mutually_exclusive_group(required=True)
    archive_group.add_argument("skill", nargs="?", default=None, help="Skill name to archive")
    archive_group.add_argument("--all-temp", action="store_true", help="Archive all temp skills")
    archive_group.add_argument("--list", action="store_true", dest="list_archive", help="List archived skills")

    # skm restore <skill>
    p_restore = sub.add_parser("restore", help="Restore a skill from archive")
    p_restore.add_argument("skill", help="Skill name")

    # skm config <key> <value>
    p_config = sub.add_parser("config", help="Manage global configuration")
    p_config.add_argument("key", choices=["registry", "archive"], help="Config key")
    p_config.add_argument("value", help="Config value")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "init":
        from .project import init
        init()

    elif args.command == "install":
        from .registry import install
        install(args.url)

    elif args.command == "update":
        from .registry import update
        update(args.skill)

    elif args.command == "list":
        from .registry import list_skills
        list_skills()

    elif args.command == "use":
        from .project import use
        use(args.skill)

    elif args.command == "unuse":
        from .project import unuse
        unuse(args.skill)

    elif args.command == "add":
        from .project import add
        add(args.url)

    elif args.command == "sync":
        from .project import sync
        sync()

    elif args.command == "status":
        from .project import status
        status()

    elif args.command == "config":
        if args.key == "registry":
            from .config import set_registry_path
            set_registry_path(args.value)
        elif args.key == "archive":
            from .config import set_archive_path
            set_archive_path(args.value)

    elif args.command == "mark":
        from .project import mark
        mark(args.skill, "temp" if args.temp else "local")

    elif args.command == "archive":
        from .project import archive, archive_all_temp, list_archived
        if args.list_archive:
            list_archived()
        elif args.all_temp:
            archive_all_temp()
        else:
            archive(args.skill)

    elif args.command == "restore":
        from .project import restore
        restore(args.skill)


if __name__ == "__main__":
    main()
