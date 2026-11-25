"""
Bytecode Disassembler for Mini-PVM.
Provides human-readable formatted dumps of compiled bytecode instructions.
"""

from typing import List
from pvm.opcodes import Opcode, Instruction

def disassemble(instructions: List[Instruction]) -> str:
    """Formats a list of Instructions into a human-readable bytecode listing."""
    lines = []
    lines.append("ADDR   OPCODE                ARGUMENT / TARGET")
    lines.append("-" * 55)

    for idx, instr in enumerate(instructions):
        op_name = instr.opcode.value
        arg_str = ""

        if instr.arg is not None:
            if instr.opcode in (Opcode.POP_JUMP_IF_FALSE, Opcode.POP_JUMP_IF_TRUE, Opcode.JUMP_ABSOLUTE):
                arg_str = f"to {instr.arg:04d}"
            elif instr.opcode == Opcode.CALL_BUILTIN:
                func_name, count = instr.arg
                arg_str = f"{func_name}() with {count} arg(s)"
            else:
                arg_str = repr(instr.arg)

        lines.append(f"{idx:04d}   {op_name:<20}  {arg_str}")

    return "\n".join(lines)


def disassemble_source(source_code: str) -> str:
    """Helper to compile source code and return its disassembled bytecode representation."""
    from pvm.compiler import compile_source
    bytecode = compile_source(source_code)
    return disassemble(bytecode)

