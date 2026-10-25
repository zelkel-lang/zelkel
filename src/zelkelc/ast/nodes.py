from __future__ import annotations

from dataclasses import dataclass
import src.zelkelc.ast.values as values

@dataclass
class ClassDeclaration:
    name: str
    members: list[ValueDeclaration]
    methods: list[FunctionDeclaration]
    irname: str

@dataclass
class StructDeclaration:
    name: str
    members: list[MemberDeclaration]
    irname: str

@dataclass
class MemberDeclaration:
    name: str
    mutable: bool
    typ: values.Value
    real_idx: int

@dataclass
class ValueDeclaration:
    name: str
    mutable: bool
    typ: values.Value
    expr: Expression
    irname: str
    
@dataclass
class FunctionDeclaration:
    name: str
    typ: values.Value
    args: dict[str, values.Value]
    body: list[Node]
    irname: str
    
@dataclass
class ReturnStatement:
    expr: Expression | None

Node = ClassDeclaration | ValueDeclaration | FunctionDeclaration | StructDeclaration

@dataclass
class BinaryExpression:
    left: Expression
    right: Expression
    op: str

@dataclass
class UnaryExpression:
    expr: Expression
    sign: str

@dataclass
class PrimaryExpression:
    value: values.Value

Expression = BinaryExpression | UnaryExpression | PrimaryExpression