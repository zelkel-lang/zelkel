import subprocess
from pathlib import Path

import rich

from src.zelkelc.ast.parser import Parser
from src.zelkelc.codegen.codegen import Codegen
from src.zelkelc.lexer.tokenizer import lex
from src.zelkelc.validator.validator import Validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_project_root() -> Path:
    candidates = [Path.cwd(), PROJECT_ROOT]
    for candidate in candidates:
        if (candidate / "src" / "main.zk").exists():
            return candidate
        if (candidate / "main.zk").exists():
            return candidate
    return PROJECT_ROOT


def build_package(build_mode: str, config: dict[str, any], debug_info: bool):
    project_root = _resolve_project_root()
    source_path = None
    for base in (project_root, Path.cwd(), PROJECT_ROOT):
        for candidate in (base / "src" / "main.zk", base / "main.zk"):
            if candidate.exists():
                source_path = candidate
                break
        if source_path is not None:
            break

    if source_path is None:
        raise FileNotFoundError("Could not locate a source file for the project.")

    with open(source_path, "r", encoding="utf-8") as f:
        source = f.read()

    tokens = lex(source)
    if debug_info:
        print(tokens)
    parser = Parser(tokens, 0)
    ast = parser.parse()
    if debug_info:
        rich.print(ast)

    Validator(ast)

    codegen = Codegen(ast)
    ir = codegen.generate()
    if debug_info:
        print(ir)

    package_name = config["package"]["name"]
    build_dir = (
        project_root
        / "target"
        / ("release" if build_mode == "release" else "debug")
        / "build"
    )
    output_path = build_dir / f"{package_name}.ll"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ir)

    if build_mode == "release":
        opt_output = build_dir / f"{package_name}.opt.ll"
        subprocess.run(
            ["opt", "-S", "-O3", str(output_path), "-o", str(opt_output)], check=True
        )
        subprocess.run(
            [
                "clang",
                str(opt_output),
                "-o",
                str(project_root / "target" / "release" / package_name),
            ],
            check=True,
        )
    else:
        subprocess.run(
            [
                "clang",
                str(output_path),
                "-o",
                str(project_root / "target" / "debug" / package_name),
            ],
            check=True,
        )
