from dataclasses import dataclass

@dataclass
class Identifier:
    value: str

@dataclass
class String:
    value: str

@dataclass
class Integer:
    value: int
    
@dataclass
class Float:
    value: float

@dataclass
class Pound:
    pass

@dataclass
class LParen:
    pass

@dataclass
class RParen:
    pass

@dataclass
class LBrace:
    pass

@dataclass
class RBrace:
    pass

@dataclass
class Period:
    pass

@dataclass
class Comma:
    pass

@dataclass
class Arrow:
    pass

@dataclass
class Colon:
    pass

@dataclass
class Equals:
    pass

@dataclass
class Operator:
    value: str

Token = Identifier | String | Integer | Float | LParen | RParen | LBrace | RBrace | Period | Comma | Arrow | Colon | Equals | Operator