@.str = private unnamed_addr constant [4 x i8] c"%d\0A\00", align 1

declare i32 @printf(ptr, ...)

define i32 @main() {
entry:
%0 = add i32 10, 0
%1 = add i32 5, 0
%2 = add i32 5, 0
%3 = mul i32 %1, %2
%4 = add i32 %0, %3
%v_19_test = add i32 %4, 0
%call = call i32 (ptr, ...) @printf(ptr @.str, i32 %v_19_test)

ret i32 0
}