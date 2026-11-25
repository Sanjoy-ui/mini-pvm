"""
Bytecode Compiler for Mini-PVM.
Translates an Abstract Syntax Tree (AST) into a linear sequence of bytecode instructions
with jump resolution (backpatching).
"""

from typing import List
from pvm.opcodes import Opcode, Instruction
from pvm.parser import (
    ASTNode,
    Program,
    AssignStmt,
    PrintStmt,
    IfStmt,
    WhileStmt,
    ForStmt,
    BinOpExpr,
    UnaryOpExpr,
    VarExpr,
    ConstExpr,
    CallExpr,
)

class Compiler:
    def __init__(self):
        self.instructions: List[Instruction] = []

    def emit(self, opcode: Opcode, arg=None) -> int:
        idx = len(self.instructions)
        self.instructions.append(Instruction(opcode, arg))
        return idx

    def compile(self, node: ASTNode) -> List[Instruction]:
        self.instructions.clear()
        self.visit(node)
        self.emit(Opcode.HALT)
        return self.instructions

    def visit(self, node: ASTNode):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode):
        raise NotImplementedError(f"No compiler visitor defined for {type(node).__name__}")

    def visit_Program(self, node: Program):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_AssignStmt(self, node: AssignStmt):
        # 1. Compile right-hand expression (leaves value on stack)
        self.visit(node.expr)
        # 2. Pop value from stack and store into environment variable
        self.emit(Opcode.STORE_NAME, node.target)

    def visit_PrintStmt(self, node: PrintStmt):
        # 1. Compile expression to print (leaves value on stack)
        self.visit(node.expr)
        # 2. Pop and print
        self.emit(Opcode.PRINT_VALUE)

    def visit_WhileStmt(self, node: WhileStmt):
        # 1. Loop start address
        loop_start = len(self.instructions)

        # 2. Compile condition expression
        self.visit(node.condition)

        # 3. Emit jump-if-false with placeholder address
        jump_exit_idx = self.emit(Opcode.POP_JUMP_IF_FALSE, -1)

        # 4. Compile loop body
        for stmt in node.body:
            self.visit(stmt)

        # 5. Jump back to condition check at loop_start
        self.emit(Opcode.JUMP_ABSOLUTE, loop_start)

        # 6. Backpatch the exit target address
        exit_target = len(self.instructions)
        self.instructions[jump_exit_idx].arg = exit_target

    def visit_ForStmt(self, node: ForStmt):
        # Handle range-based loops: har i mein ginte(start, stop):
        iter_name = f"__iter_{node.target}"
        stop_name = f"__stop_{node.target}"

        if isinstance(node.iterable, CallExpr) and node.iterable.func_name in ("ginte", "ginti", "count", "range"):
            args = node.iterable.args
            if len(args) == 1:
                self.emit(Opcode.LOAD_CONST, 0)
                self.emit(Opcode.STORE_NAME, iter_name)
                self.visit(args[0])
                self.emit(Opcode.STORE_NAME, stop_name)
            elif len(args) >= 2:
                self.visit(args[0])
                self.emit(Opcode.STORE_NAME, iter_name)
                self.visit(args[1])
                self.emit(Opcode.STORE_NAME, stop_name)
        else:
            raise NotImplementedError("For-in loop currently supports range generator: ginte(start, stop)")

        loop_start = len(self.instructions)

        # Condition check: iter_name < stop_name
        self.emit(Opcode.LOAD_NAME, iter_name)
        self.emit(Opcode.LOAD_NAME, stop_name)
        self.emit(Opcode.COMPARE_OP, "<")
        jump_exit_idx = self.emit(Opcode.POP_JUMP_IF_FALSE, -1)

        # Set user loop variable: node.target = iter_name
        self.emit(Opcode.LOAD_NAME, iter_name)
        self.emit(Opcode.STORE_NAME, node.target)

        # Compile body
        for stmt in node.body:
            self.visit(stmt)

        # Increment: iter_name = iter_name + 1
        self.emit(Opcode.LOAD_NAME, iter_name)
        self.emit(Opcode.LOAD_CONST, 1)
        self.emit(Opcode.BINARY_ADD)
        self.emit(Opcode.STORE_NAME, iter_name)

        # Jump back to loop start
        self.emit(Opcode.JUMP_ABSOLUTE, loop_start)

        # Backpatch loop exit
        self.instructions[jump_exit_idx].arg = len(self.instructions)

    def visit_IfStmt(self, node: IfStmt):
        jump_to_end_indices = []

        # 1. Compile main 'agar' condition
        self.visit(node.condition)
        jump_next_branch = self.emit(Opcode.POP_JUMP_IF_FALSE, -1)

        # 2. Compile then-body
        for stmt in node.then_body:
            self.visit(stmt)

        # Jump past all elif/else branches to end of IfStmt
        jump_to_end_indices.append(self.emit(Opcode.JUMP_ABSOLUTE, -1))

        # Backpatch main if's false jump to where next branch begins
        self.instructions[jump_next_branch].arg = len(self.instructions)

        # 3. Compile 'warna_agar' elif blocks
        for elif_cond, elif_body in node.elif_blocks:
            self.visit(elif_cond)
            jump_next_branch = self.emit(Opcode.POP_JUMP_IF_FALSE, -1)

            for stmt in elif_body:
                self.visit(stmt)

            jump_to_end_indices.append(self.emit(Opcode.JUMP_ABSOLUTE, -1))
            self.instructions[jump_next_branch].arg = len(self.instructions)

        # 4. Compile 'warna' else block if present
        if node.else_body:
            for stmt in node.else_body:
                self.visit(stmt)

        # 5. Backpatch all successful branch jumps to current end address
        end_target = len(self.instructions)
        for idx in jump_to_end_indices:
            self.instructions[idx].arg = end_target

    def visit_BinOpExpr(self, node: BinOpExpr):
        # Post-order: compile left, compile right, then emit operator
        self.visit(node.left)
        self.visit(node.right)

        op = node.op
        if op == "+":
            self.emit(Opcode.BINARY_ADD)
        elif op == "-":
            self.emit(Opcode.BINARY_SUB)
        elif op == "*":
            self.emit(Opcode.BINARY_MUL)
        elif op == "/":
            self.emit(Opcode.BINARY_DIV)
        elif op == "%":
            self.emit(Opcode.BINARY_MOD)
        elif op in ("==", "!=", "<", "<=", ">", ">="):
            self.emit(Opcode.COMPARE_OP, op)
        else:
            raise NotImplementedError(f"Unsupported binary operator: {op}")

    def visit_UnaryOpExpr(self, node: UnaryOpExpr):
        if node.op == "-":
            # 0 - expr
            self.emit(Opcode.LOAD_CONST, 0)
            self.visit(node.expr)
            self.emit(Opcode.BINARY_SUB)
        elif node.op == "+":
            self.visit(node.expr)
        else:
            raise NotImplementedError(f"Unsupported unary operator: {node.op}")

    def visit_ConstExpr(self, node: ConstExpr):
        self.emit(Opcode.LOAD_CONST, node.value)

    def visit_VarExpr(self, node: VarExpr):
        self.emit(Opcode.LOAD_NAME, node.name)

    def visit_CallExpr(self, node: CallExpr):
        # Compile all arguments first
        for arg in node.args:
            self.visit(arg)
        # Emit builtin call
        self.emit(Opcode.CALL_BUILTIN, (node.func_name, len(node.args)))


def compile_source(source_code: str) -> List[Instruction]:
    """Helper to tokenize, parse, and compile source code directly into bytecode."""
    from pvm.parser import parse_source
    ast = parse_source(source_code)
    compiler = Compiler()
    return compiler.compile(ast)
