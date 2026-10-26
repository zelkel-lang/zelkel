# Zelkel

TODO: tomorrow, implement more macro stuff
```zk
val test: i64 = 1 + 2*3 + 3*4

#llvm(
  "%call = call i32 (ptr, ...) @printf(ptr @int.fmt, i64 %{:irname})",
  test // Test variable's irname is inputted inplace or {:irname} in the llvm ir
)
```

## Goals 
- [ ] Self-hosted
- [ ] Reference-counting garbage collector
- [ ] Same-thread assync functions

## TODO
- [x] Scope checking and stuff in parser
- [ ] Parser should generate all names (unique), struct indexes, etc for codegen, this should also be in the scope
    - [x] Multi pass parser: first scope/symbol collection (what i've been doing now), then check if it makes sense :)
- [ ] Functions may kind of have same name but different arguments, but the scope stuff is using a dict[str, Value] so it is not tracked, the resolve_function() should work for this though, so scope stuff needs work.
- [ ] Need to know the value type of an expression in codegen, i think adding this in the validator to the ast is the right move...
- Types:
  - With no * or & before type it will be "dynamic", the compiler figures out if it's the pointer or the value that is being used
  - explicit value with * or explicit pointer with &. You can also use & and * on a "dynamic" type to get both, "dynamic" types are both at the same time, but in reality they are probably the pointer and then you know both 

## Planning code + ideas + sketch, ... etc ([see also](https://github.com/zelkel-lang/zelkel-syntax-demo))
```kotlin
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
  
  val parser_manually: &Parser = mem.alloc(mem.sizeof(Parser)) // will not be tracked by reference counter, the pointer address is not added to the GC's pointer track list. GC only counts addresses in it's list
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
