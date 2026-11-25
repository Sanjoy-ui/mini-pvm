"""
Mini-PVM: Stack-Based Bytecode Virtual Machine.
Simulates a lightweight Python Virtual Machine (PVM) with an operand stack,
an instruction pointer, frame environment, and an evaluation loop.
"""

import sys
from typing import List, Dict, Any, Optional
from pvm.opcodes import Opcode, Instruction

class MiniPVM:
    def __init__(self, stdout=None):
        self.operand_stack: List[Any] = []
        self.environment: Dict[str, Any] = {}
        self.ip: int = 0
        self.instructions: List[Instruction] = []
        self.stdout = stdout if stdout is not None else sys.stdout

    def reset(self):
        self.operand_stack.clear()
        self.ip = 0

    def run(self, instructions: List[Instruction], environment: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes a sequence of bytecode instructions on the virtual machine stack.
        Returns the resulting environment namespace.
        """
        self.instructions = instructions
        self.ip = 0
        if environment is not None:
            self.environment = environment

        while self.ip < len(self.instructions):
            instr = self.instructions[self.ip]
            self.ip += 1

            op = instr.opcode
            arg = instr.arg

            if op == Opcode.LOAD_CONST:
                self.operand_stack.append(arg)

            elif op == Opcode.LOAD_NAME:
                if arg not in self.environment:
                    raise NameError(f"Name '{arg}' is not defined in PVM environment")
                self.operand_stack.append(self.environment[arg])

            elif op == Opcode.STORE_NAME:
                val = self.operand_stack.pop()
                self.environment[arg] = val

            elif op == Opcode.BINARY_ADD:
                b = self.operand_stack.pop()
                a = self.operand_stack.pop()
                self.operand_stack.append(a + b)

            elif op == Opcode.BINARY_SUB:
                b = self.operand_stack.pop()
                a = self.operand_stack.pop()
                self.operand_stack.append(a - b)

            elif op == Opcode.BINARY_MUL:
                b = self.operand_stack.pop()
                a = self.operand_stack.pop()
                self.operand_stack.append(a * b)

            elif op == Opcode.BINARY_DIV:
                b = self.operand_stack.pop()
                a = self.operand_stack.pop()
                # If both are int and divisible, perform integer division; otherwise float
                if isinstance(a, int) and isinstance(b, int) and b != 0 and a % b == 0:
                    self.operand_stack.append(a // b)
                else:
                    self.operand_stack.append(a / b)

            elif op == Opcode.BINARY_MOD:
                b = self.operand_stack.pop()
                a = self.operand_stack.pop()
                self.operand_stack.append(a % b)

            elif op == Opcode.COMPARE_OP:
                b = self.operand_stack.pop()
                a = self.operand_stack.pop()
                if arg == "==":
                    res = (a == b)
                elif arg == "!=":
                    res = (a != b)
                elif arg == "<":
                    res = (a < b)
                elif arg == "<=":
                    res = (a <= b)
                elif arg == ">":
                    res = (a > b)
                elif arg == ">=":
                    res = (a >= b)
                else:
                    raise ValueError(f"Unknown comparison operator: {arg}")
                self.operand_stack.append(res)

            elif op == Opcode.POP_JUMP_IF_FALSE:
                cond = self.operand_stack.pop()
                if not cond:
                    self.ip = arg

            elif op == Opcode.POP_JUMP_IF_TRUE:
                cond = self.operand_stack.pop()
                if cond:
                    self.ip = arg

            elif op == Opcode.JUMP_ABSOLUTE:
                self.ip = arg

            elif op == Opcode.PRINT_VALUE:
                val = self.operand_stack.pop()
                print(val, file=self.stdout)

            elif op == Opcode.CALL_BUILTIN:
                func_name, arg_count = arg
                args = [self.operand_stack.pop() for _ in range(arg_count)]
                args.reverse()

                if func_name == "str":
                    res = str(args[0])
                elif func_name == "int":
                    res = int(args[0])
                elif func_name == "float":
                    res = float(args[0])
                elif func_name == "len":
                    res = len(args[0])
                elif func_name == "abs":
                    res = abs(args[0])
                else:
                    raise NameError(f"Built-in function '{func_name}' is not recognized by Mini-PVM")
                self.operand_stack.append(res)

            elif op == Opcode.HALT:
                break

            else:
                raise RuntimeError(f"Unknown opcode '{op}' encountered by Mini-PVM at IP={self.ip - 1}")

        return self.environment


def run_source(source_code: str, stdout=None, environment=None) -> Dict[str, Any]:
    """Compiles source code into bytecode and runs it on the Mini-PVM."""
    from pvm.compiler import compile_source
    bytecode = compile_source(source_code)
    vm = MiniPVM(stdout=stdout)
    return vm.run(bytecode, environment=environment)

