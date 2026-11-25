"""
Opcode definitions and instruction representation for Mini-PVM.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional

class Opcode(Enum):
    # Stack / Memory
    LOAD_CONST = "LOAD_CONST"          # Push constant value onto stack
    LOAD_NAME = "LOAD_NAME"            # Load variable value from environment
    STORE_NAME = "STORE_NAME"          # Pop top of stack and store in environment

    # Arithmetic Operations (pop 2, compute, push 1)
    BINARY_ADD = "BINARY_ADD"
    BINARY_SUB = "BINARY_SUB"
    BINARY_MUL = "BINARY_MUL"
    BINARY_DIV = "BINARY_DIV"
    BINARY_MOD = "BINARY_MOD"

    # Comparison Operatiopythns (pop 2, compare, push bool)
    COMPARE_OP = "COMPARE_OP"          # arg is operator string: '<', '>', '==', etc.

    # Control Flow
    POP_JUMP_IF_FALSE = "POP_JUMP_IF_FALSE"  # Pop top; if falsey, jump to target_ip
    POP_JUMP_IF_TRUE = "POP_JUMP_IF_TRUE"    # Pop top; if truthy, jump to target_ip
    JUMP_ABSOLUTE = "JUMP_ABSOLUTE"          # Unconditionally jump to target_ip

    # Output & Built-ins
    PRINT_VALUE = "PRINT_VALUE"        # Pop top of stack and print it
    CALL_BUILTIN = "CALL_BUILTIN"      # arg: (func_name, arg_count) - calls built-in helper

    # VM State
    HALT = "HALT"                      # Terminate execution


@dataclass
class Instruction:
    opcode: Opcode
    arg: Optional[Any] = None
    line_num: int = 1

    def __repr__(self) -> str:
        if self.arg is not None:
            return f"{self.opcode.value} {self.arg!r}"
        return self.opcode.value
