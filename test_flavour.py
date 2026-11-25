"""
Unit Tests for Flavour Python Transpiler and Runner.
"""

import unittest
import io
import sys
from flavour import transpile, run_code

class TestFlavourTranspiler(unittest.TestCase):

    def test_basic_hinglish_transpile(self):
        source = "agar x == 5:\n    likho('Haan')\nwarna:\n    likho('Nahi')"
        expected = "if x == 5:\n    print('Haan')\nelse:\n    print('Nahi')"
        result = transpile(source, dialect="hinglish")
        self.assertEqual(result, expected)

    def test_string_literals_preserved(self):
        # Keywords inside strings should NEVER be replaced
        source = 'msg = "agar tum mil jao, warna hum mar jayenge"'
        result = transpile(source, dialect="hinglish")
        self.assertEqual(result, source)

    def test_comments_preserved(self):
        # Keywords in comments should remain as comments
        source = "# agar this is a comment\nx = 10"
        result = transpile(source, dialect="hinglish")
        self.assertEqual(result, source)

    def test_variable_substrings_preserved(self):
        # Variable names containing keyword as substring (e.g. agarbatti) must remain intact
        source = "agarbatti = 42\nagar agarbatti == 42:\n    likho(agarbatti)"
        expected = "agarbatti = 42\nif agarbatti == 42:\n    print(agarbatti)"
        result = transpile(source, dialect="hinglish")
        self.assertEqual(result, expected)

    def test_function_definition_and_return(self):
        source = "kaam add(a, b):\n    wapas a + b\nans = add(2, 3)"
        expected = "def add(a, b):\n    return a + b\nans = add(2, 3)"
        result = transpile(source, dialect="hinglish")
        self.assertEqual(result, expected)

    def test_execution_in_runtime(self):
        code = """
kaam multiply(x, y):
    wapas x * y

ans = multiply(6, 7)
status = sahi
"""
        scope = run_code(code, dialect="hinglish")
        self.assertEqual(scope["ans"], 42)
        self.assertIs(scope["status"], True)

    def test_stdout_execution(self):
        code = """
har n mein ginte(3):
    likho(n)
"""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            run_code(code, dialect="hinglish")
            output = sys.stdout.getvalue().strip()
            self.assertEqual(output, "0\n1\n2")
        finally:
            sys.stdout = old_stdout

    def test_genz_dialect(self):
        code = """
flex test_vibe(v):
    lowkey v == fr:
        bop "W"
    deadass:
        bop "L"

result = test_vibe(cap)
"""
        scope = run_code(code, dialect="genz")
        self.assertEqual(scope["result"], "L")

    def test_invalid_dialect_error(self):
        with self.assertRaises(ValueError):
            transpile("likho('hi')", dialect="invalid_dialect")


if __name__ == "__main__":
    unittest.main()

