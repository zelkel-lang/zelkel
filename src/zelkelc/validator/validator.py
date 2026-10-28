from __future__ import annotations

from src.zelkelc.ast import types
from src.zelkelc.validator import scope


class SemanticCheckFailed(Exception):
    pass


def validate_ast(tree: list[types.Node]) -> scope.Scope:
    checker = scope.ScopeChecker()
    global_scope, errors = checker.check(tree)

    if len(errors) > 0:
        pretty_errors = "\n".join(f"- {err.message}" for err in errors)
        raise SemanticCheckFailed(f"AST semantic validation failed:\n{pretty_errors}")

    return global_scope


class Validator:
    scope: scope.Scope

    def __init__(self, tree: list[types.Node]):
        self.scope = validate_ast(tree)
