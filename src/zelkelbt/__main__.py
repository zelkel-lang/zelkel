import argparse
import subprocess
import sys

from src.zelkelbt.build import build_package
from src.zelkelbt.config import get_config


def print_help():
    print("""Zelkel Build Tools (zk)

Usage: zk [OPTIONS] [COMMAND]

Options:
    -V, --version           Print version info
    --help                  Print help

Commands:
    build, b    Compile the current package
    clean       Remove the build/ directory
    run, r      Compile and run the current package""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="zk",
        description="Zelkel Build Tools (zk)",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False,
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="zk 1.0.0",
        help="Print version info",
    )
    parser.add_argument("--help", action="help", help="Print help")

    subparsers = parser.add_subparsers(dest="command", metavar="[COMMAND]")

    build_parser = subparsers.add_parser(
        "build", aliases=["b"], help="Compile the current package"
    )
    build_parser.add_argument(
        "--debug-info",
        action="store_true",
        help="Enable debug output while building the package",
    )
    build_group = build_parser.add_mutually_exclusive_group()
    build_group.add_argument(
        "--debug",
        dest="build_mode",
        action="store_const",
        const="debug",
        default="debug",
        help="Enable debug build mode",
    )
    build_group.add_argument(
        "--release",
        dest="build_mode",
        action="store_const",
        const="release",
        help="Enable release build mode",
    )

    clean_parser = subparsers.add_parser("clean", help="Remove the build/ directory")

    run_parser = subparsers.add_parser(
        "run", aliases=["r"], help="Compile and run the current package"
    )
    run_parser.add_argument(
        "--debug-info",
        action="store_true",
        help="Enable debug output while running the package",
    )

    parser.usage = "zk [OPTIONS] [COMMAND]"

    args = parser.parse_args()

    if args.command in ["build", "b"]:
        config = get_config()
        build_package(args.build_mode, config, args.debug_info)
    elif args.command == "clean":
        print("TODO: implement clean command")
        sys.exit(1)
    elif args.command in ["run", "r"]:
        config = get_config()
        build_package("debug", config, args.debug_info)
        subprocess.run([f"./target/debug/{config['package']['name']}"], check=True)
    else:
        parser.print_help()