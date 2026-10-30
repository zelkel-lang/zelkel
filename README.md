# Zelkel
Compiled object-oriented programming language

## Compilation pipeline
Lexer --> Preprocessor (unimplemented) --> Parser --> Expander --> Validator --> Codegen [--> Optimizer (LLVM's opt)]

## Goals
- [ ] Self-hosted
- [ ] Reference-counting garbage collector
- [ ] Same-thread assync functions

## TODO
- [x] Macros
  - [x] Macro definition
  - [x] Macro calling and inline llvm
- Types:
  - With no * or & before type it will be "dynamic", the compiler figures out if it's the pointer or the value that is being used
  - explicit value with * or explicit pointer with &. You can also use & and * on a "dynamic" type to get both, "dynamic" types are both at the same time, but in reality they are probably the pointer and then you know both 

## Planning code + ideas + sketch, ... etc ([see also](https://github.com/zelkel-lang/zelkel-syntax-demo))
### Macros
```rust
#fn name($x: expr, $y: ident) {
    ... template tokens ...
}
```

### Just a bunch of stuff
```rust
class Parser {
  val tokens: Arr<Token>
  val cursor: Int

  // :: for constructor?, under the hood so vert denne funksjonen kjørt av ein anna der self har blitt laga, allocated, idk, noko sånn. Den hook constructor funksjonen har alle members av classen og returner pointer til objektet i minne
  fn::new(self, tokens: Arr<Token>) {
    self.tokens = tokens
    self.cursor = Int::from(0)
  }
}

fn main() -> i64 {
  val parser: Parser = Parser::new(etcetc...) // with hooked constructor, also puts reference counting
  
  val parser_manually: Parser = mem.alloc(mem.sizeof(Parser)) // will not be tracked by reference counter, the pointer address is not added to the GC's pointer track list. GC only counts addresses in it's list
  *parser_manually.tokens = ...
  *parser_manually.cursor = ...

  mem.free(parser_manually)

  // Kanskje noko sånn heller?
  val allocated: Result<&OtherClass> = mem.alloc(mem.sizeof(OtherClass))
  val allocated_real: &OtherClass = allocated.expect("yes!")

  mem.free(allocated_real)

  // Alternativ, meire generics?
  val allocated: Result<&OtherClass> = mem.alloc<OtherClass>()
  val allocated_real: &OtherClass = allocated.expect("Couldn't allocate memory")

  return 0
}
```
