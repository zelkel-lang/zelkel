import argparse
import shutil
import subprocess
from pathlib import Path

from src.zelkelbt.build import build_package
from src.zelkelbt.config import get_config


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="zk",
        description="Zelkel Build Tools (zk)",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=True,
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="zk 1.0.0",
        help="Print version info",
    )

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

    clean_parser = subparsers.add_parser("clean", help="Remove the 'target/' directory")

    run_parser = subparsers.add_parser(
        "run", aliases=["r"], help="Compile and run the current package"
    )
    run_parser.add_argument(
        "--debug-info",
        action="store_true",
        help="Enable debug output while running the package",
    )
    run_group = run_parser.add_mutually_exclusive_group()
    run_group.add_argument(
        "--debug",
        dest="run_mode",
        action="store_const",
        const="debug",
        default="debug",
        help="Enable debug run mode",
    )
    run_group.add_argument(
        "--release",
        dest="run_mode",
        action="store_const",
        const="release",
        help="Enable release run mode",
    )

    parser.usage = "zk [COMMAND] [OPTIONS]"

    args = parser.parse_args()

    if args.command in ["build", "b"]:
        config = get_config()
        build_package(args.build_mode, config, args.debug_info)
    elif args.command == "clean":
        get_config()

        target_dir = Path("target")
        if target_dir.exists():
            shutil.rmtree(target_dir)
    elif args.command in ["run", "r"]:
        config = get_config()
        build_package(args.run_mode, config, args.debug_info)
        subprocess.run([f"./target/debug/{config['package']['name']}"], check=True)
    else:
        parser.print_help()
