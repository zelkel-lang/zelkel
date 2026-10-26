declare i32 @printf(ptr, ...)
@int.fmt = private unnamed_addr constant [5 x i8] c"%ldA"




define void @zkmain() {
entry:
%0 = add i64 2, 0
%1 = add i64 2, 0
%2 = add i64 3, 0
%3 = mul i64 %1, %2
%4 = add i64 %0, %3
%v_27_test = add i64 %4, 0
%call = call i32 (ptr, ...) @printf(ptr @int.fmt, i64 %v_27_test)
}

define i32 @main() {
entry:
call void @zkmain()
ret i32 0
}
