"""
Unit Test Suite for Mini-PVM (Stack-Based Virtual Machine).
"""

import unittest
import io
import sys
from pvm.lexer import tokenize_source
from pvm.parser import parse_source, AssignStmt, IfStmt, WhileStmt
from pvm.compiler import compile_source
from pvm.opcodes import Opcode
from pvm.vm import MiniPVM, run_source
from pvm.disassembler import disassemble_source

class TestMiniPVM(unittest.TestCase):

    def test_lexer_tokenization(self):
        code = "x = 10\nagar x > 5:\n    likho(x)"
        tokens = tokenize_source(code)
        types = [t.type for t in tokens if t.type not in ("NEWLINE", "EOF")]
        self.assertIn("KEYWORD", types)
        self.assertIn("IDENT", types)
        self.assertIn("NUMBER", types)

    def test_parser_ast(self):
        code = "x = 42\nagar x == 42:\n    likho('Sahi')\nwarna:\n    likho('Galat')"
        ast = parse_source(code)
        self.assertEqual(len(ast.statements), 2)
        self.assertIsInstance(ast.statements[0], AssignStmt)
        self.assertIsInstance(ast.statements[1], IfStmt)

    def test_compiler_bytecode_and_backpatching(self):
        code = "agar x > 0:\n    likho(1)\nwarna:\n    likho(0)"
        bytecode = compile_source(code)
        opcodes = [instr.opcode for instr in bytecode]

        self.assertIn(Opcode.POP_JUMP_IF_FALSE, opcodes)
        self.assertIn(Opcode.JUMP_ABSOLUTE, opcodes)
        self.assertEqual(bytecode[-1].opcode, Opcode.HALT)

        # Check jump target addresses are positive and within bounds
        for instr in bytecode:
            if instr.opcode in (Opcode.POP_JUMP_IF_FALSE, Opcode.JUMP_ABSOLUTE):
                self.assertGreater(instr.arg, 0)
                self.assertLessEqual(instr.arg, len(bytecode))

    def test_arithmetic_execution(self):
        code = """
a = 15
b = 4
jod = a + b
ghatana = a - b
guna = a * b
shesh = a % b
"""
        env = run_source(code)
        self.assertEqual(env["jod"], 19)
        self.assertEqual(env["ghatana"], 11)
        self.assertEqual(env["guna"], 60)
        self.assertEqual(env["shesh"], 3)

    def test_while_loop_execution(self):
        code = """
counter = 1
total = 0
jabtak counter <= 5:
    total = total + counter
    counter = counter + 1
"""
        env = run_source(code)
        self.assertEqual(env["counter"], 6)
        self.assertEqual(env["total"], 15)

    def test_if_elif_else_execution(self):
        code = """
score = 80
agar score > 85:
    res = 'A'
warna_agar score > 75:
    res = 'B'
warna:
    res = 'C'
"""
        env = run_source(code)
        self.assertEqual(env["res"], "B")

    def test_stdout_capture(self):
        code = """
likho("PVM Output")
"""
        buf = io.StringIO()
        run_source(code, stdout=buf)
        self.assertEqual(buf.getvalue().strip(), "PVM Output")

    def test_genz_dialect_on_pvm(self):
        code = """
score = 90
lowkey score > 50:
    spill("Lit")
deadass:
    spill("Cooked")
"""
        buf = io.StringIO()
        run_source(code, stdout=buf)
        self.assertEqual(buf.getvalue().strip(), "Lit")

    def test_disassembler_formatting(self):
        code = "x = 10\nlikho(x)"
        dis_output = disassemble_source(code)
        self.assertIn("LOAD_CONST", dis_output)
        self.assertIn("STORE_NAME", dis_output)
        self.assertIn("PRINT_VALUE", dis_output)
        self.assertIn("HALT", dis_output)


if __name__ == "__main__":
    unittest.main()

