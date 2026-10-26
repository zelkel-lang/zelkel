from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

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
    typ: Value
    real_idx: int

@dataclass
class ValueDeclaration:
    name: str
    mutable: bool
    typ: Value
    expr: Expression
    irname: str
    
@dataclass
class FunctionDeclaration:
    name: str
    typ: Value
    args: dict[str, Value]
    body: list[Node]
    irname: str
    
@dataclass
class ReturnStatement:
    expr: Optional[Expression]
    
@dataclass
class MacroCall:
    body: str

Node = ClassDeclaration | ValueDeclaration | FunctionDeclaration | StructDeclaration | MacroCall

@dataclass
class BinaryExpression:
    left: Expression
    right: Expression
    op: str
    typ: Value

@dataclass
class UnaryExpression:
    expr: Expression
    sign: str
    typ: Value

@dataclass
class PrimaryExpression:
    value: Value
    typ: Value

Expression = BinaryExpression | UnaryExpression | PrimaryExpression

@dataclass
class Integer64:
    value: int
    
    def to_llvm() -> str:
        return "i64"
    
    def __eq__(self, other):
        if not isinstance(other, Integer64):
            return False
        return self.value == other.value
    
@dataclass
class Float64:
    value: int
    
    def to_llvm() -> str:
        return "f64"
    
    def __eq__(self, other):
        if not isinstance(other, Float64):
            return False
        return self.value == other.value

@dataclass
class String:
    value: str
    
    def to_llvm() -> str:
        print("Cannot convert String to llvm ir")
        exit(1)

@dataclass
class Void:
    pass

    def to_llvm() -> str:
        return "void"

@dataclass
class VariableRef:
    name: str
    irname: str
    typ: Value
    
    def to_llvm() -> str:
        print("Cannot convert Variable to llvm ir")
        exit(1)

@dataclass
class FunctionCall:
    name: str
    irname: str
    args: list[Expression]

@dataclass
class Ptr[T]:
    pass

@dataclass
class Val[T]:
    pass

Value = Integer64 | Float64 | String | Void | VariableRef | FunctionCall