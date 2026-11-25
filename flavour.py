#!/usr/bin/env python3
"""
Flavour: A Custom-Keyword Python Dialect & Virtual Machine (Mini-PVM).

Features:
1. Mini-PVM Execution: Compiles custom dialect source directly into bytecode instructions
   and executes on a stack-based virtual machine (no exec()).
2. Bytecode Disassembler: Inspects the compiled bytecode listing (opcodes, jump targets).
3. Transpiler: Source-to-source translator to standard Python syntax.
4. Interactive REPL: Live interactive shell.
"""

import sys
import io
import os
import argparse
import tokenize
import traceback
from dialects import get_dialect, DIALECTS
from pvm.vm import run_source as run_on_pvm, MiniPVM
from pvm.disassembler import disassemble_source
from pvm.compiler import compile_source

# --- Transpiler Core ---

def transpile(source_code: str, dialect: str = "hinglish") -> str:
    """
    Transpiles source code from a custom dialect into standard Python.
    Uses tokenization so strings, comments, and non-keyword identifiers are preserved.
    """
    keyword_map = get_dialect(dialect)
    
    source_bytes = source_code.encode("utf-8")
    byte_reader = io.BytesIO(source_bytes).readline
    
    replacements = []
    try:
        for tok in tokenize.tokenize(byte_reader):
            if tok.type == tokenize.NAME and tok.string in keyword_map:
                replacements.append((tok.start, tok.end, keyword_map[tok.string]))
    except tokenize.TokenError as err:
        raise SyntaxError(f"Tokenization error: {err}") from err

    replacements.sort(key=lambda item: (item[0][0], item[0][1]), reverse=True)

    lines = source_code.splitlines(keepends=True)
    if not lines and source_code:
        lines = [source_code]

    for (s_row, s_col), (e_row, e_col), new_text in replacements:
        line_idx = s_row - 1
        line = lines[line_idx]
        lines[line_idx] = line[:s_col] + new_text + line[e_col:]

    return "".join(lines)


def run_code_transpiled(source_code: str, filename: str = "<flavour>", dialect: str = "hinglish", global_scope: dict = None) -> dict:
    """Transpiles and executes custom dialect code using Python's exec()."""
    transpiled = transpile(source_code, dialect=dialect)
    
    if global_scope is None:
        global_scope = {
            "__name__": "__main__",
            "__file__": os.path.abspath(filename) if filename != "<flavour>" else filename,
            "__doc__": None,
        }

    try:
        compiled = compile(transpiled, filename, "exec")
        exec(compiled, global_scope)
    except Exception as exc:
        sys.stderr.write(f"\n[Flavour Transpiler Runtime Error in '{filename}']:\n")
        traceback.print_exc(file=sys.stderr)
        raise exc

    return global_scope

run_code = run_code_transpiled


# --- Runners and Tools ---

def run_file(filepath: str, dialect: str = "hinglish", mode: str = "pvm") -> None:
    """Runs a source file using either Mini-PVM bytecode execution or transpiler."""
    if not os.path.isfile(filepath):
        sys.stderr.write(f"Error: File '{filepath}' not found.\n")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    if mode == "pvm":
        try:
            run_on_pvm(source)
        except Exception as exc:
            sys.stderr.write(f"\n[Mini-PVM Execution Error in '{filepath}']:\n")
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)
    else:
        run_code_transpiled(source, filename=filepath, dialect=dialect)


def disassemble_file(filepath: str) -> None:
    """Compiles a source file and prints its disassembled bytecode instructions."""
    if not os.path.isfile(filepath):
        sys.stderr.write(f"Error: File '{filepath}' not found.\n")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    print(disassemble_source(source))


def transpile_file(filepath: str, output_path: str = None, dialect: str = "hinglish") -> str:
    """Transpiles a file to standard Python and saves it or prints to stdout."""
    if not os.path.isfile(filepath):
        sys.stderr.write(f"Error: File '{filepath}' not found.\n")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    transpiled = transpile(source, dialect=dialect)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(transpiled)
        print(f"Transpiled code successfully written to: {output_path}")
    else:
        print(transpiled)

    return transpiled


def start_repl(dialect: str = "hinglish", mode: str = "pvm") -> None:
    """Starts an interactive REPL shell on Mini-PVM or transpiler."""
    print("=" * 65)
    print(f"  Flavour Interactive REPL ({dialect.capitalize()} Dialect - Mode: {mode.upper()})")
    print("  Type custom code, or 'exit()' / Ctrl+C to quit.")
    print("=" * 65)

    pvm_env = {}
    transpile_scope = {"__name__": "__main__", "__doc__": None}

    buffer = []
    in_multiline = False

    while True:
        try:
            prompt = "... " if in_multiline else ">>> "
            line = input(prompt)

            if not in_multiline and line.strip() in ("exit()", "quit()"):
                print("Alvida! (Goodbye)")
                break

            buffer.append(line)

            stripped = line.strip()
            if stripped.endswith(":") or (in_multiline and stripped != ""):
                in_multiline = True
                continue

            code_block = "\n".join(buffer)
            buffer = []
            in_multiline = False

            if not code_block.strip():
                continue

            if mode == "pvm":
                try:
                    pvm_env = run_on_pvm(code_block, environment=pvm_env)
                except Exception as e:
                    print(f"PVM Error: {e}")
            else:
                transpiled_block = transpile(code_block, dialect=dialect)
                try:
                    expr = compile(transpiled_block.strip(), "<repl>", "eval")
                    res = eval(expr, transpile_scope)
                    if res is not None:
                        print(repr(res))
                except SyntaxError:
                    compiled = compile(transpiled_block, "<repl>", "exec")
                    exec(compiled, transpile_scope)

        except (KeyboardInterrupt, EOFError):
            print("\nAlvida! (Exiting)")
            break
        except Exception as e:
            print(f"Error: {e}")


# --- CLI Parser ---

def parse_cli_args(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Flavour: Custom-Keyword Python Dialect & Virtual Machine (Mini-PVM)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 'run' subcommand
    run_parser = subparsers.add_parser("run", help="Run a source file on Mini-PVM or via Transpiler")
    run_parser.add_argument("file", help="Path to custom dialect source file (.mypy)")
    run_parser.add_argument(
        "--mode",
        choices=["pvm", "transpile"],
        default="pvm",
        help="Execution mode: 'pvm' (Stack Virtual Machine, default) or 'transpile'",
    )

    # 'dis' subcommand (Disassemble)
    dis_parser = subparsers.add_parser("dis", help="Disassemble source file into PVM bytecode")
    dis_parser.add_argument("file", help="Path to custom dialect source file")

    # 'transpile' subcommand
    trans_parser = subparsers.add_parser("transpile", help="Transpile .mypy to standard Python")
    trans_parser.add_argument("file", help="Path to custom dialect source file")
    trans_parser.add_argument("-o", "--output", help="Optional output file path")

    # 'repl' subcommand
    repl_parser = subparsers.add_parser("repl", help="Start an interactive REPL shell")
    repl_parser.add_argument(
        "--mode",
        choices=["pvm", "transpile"],
        default="pvm",
        help="REPL mode: 'pvm' (default) or 'transpile'",
    )

    # Extract --dialect and --mode flags if present anywhere in argv
    dialect = "hinglish"
    mode = "pvm"
    cleaned = []
    i = 0
    while i < len(argv):
        if argv[i] == "--dialect" and i + 1 < len(argv):
            dialect = argv[i + 1]
            i += 2
        elif argv[i].startswith("--dialect="):
            dialect = argv[i].split("=", 1)[1]
            i += 1
        elif argv[i] == "--mode" and i + 1 < len(argv):
            mode = argv[i + 1]
            i += 2
        elif argv[i].startswith("--mode="):
            mode = argv[i].split("=", 1)[1]
            i += 1
        else:
            cleaned.append(argv[i])
            i += 1

    if dialect.lower() not in DIALECTS:
        sys.stderr.write(f"Error: Unknown dialect '{dialect}'. Available: {', '.join(DIALECTS.keys())}\n")
        sys.exit(2)

    if cleaned and cleaned[0] not in ("run", "dis", "transpile", "repl", "-h", "--help"):
        cleaned = ["run"] + cleaned

    args = parser.parse_args(cleaned)
    args.dialect = dialect.lower()
    args.mode = mode.lower()
    return args


def interactive_menu():
    """Interactive launcher menu when no CLI arguments are supplied."""
    while True:
        print("\n" + "=" * 60)
        print("  🌶️  Flavour: Custom-Keyword Python Dialect & Mini-PVM")
        print("=" * 60)
        print("  1. Run an existing .mypy file")
        print("  2. Create and run a new .mypy file")
        print("  3. Launch Interactive REPL Shell")
        print("  4. Disassemble .mypy file into PVM Bytecode")
        print("  5. Exit")
        print("=" * 60)

        try:
            choice = input("Enter choice [1-5]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAlvida! (Exiting)")
            break

        if choice == "1":
            filepath = input("Enter .mypy file path (e.g. examples/fizzbuzz.mypy): ").strip()
            if filepath:
                run_file(filepath, mode="pvm")
        elif choice == "2":
            filename = input("Enter file name [default: my_code.mypy]: ").strip() or "my_code.mypy"
            print("\nEnter your custom code below. Type 'RUN' on a new line to execute:\n" + "-" * 50)
            lines = []
            while True:
                try:
                    line = input()
                    if line.strip() == "RUN":
                        break
                    lines.append(line)
                except (KeyboardInterrupt, EOFError):
                    break
            code = "\n".join(lines)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(code)
            print(f"\n[Saved to '{filename}'] Executing on Mini-PVM:\n" + "-" * 50)
            run_file(filename, mode="pvm")
        elif choice == "3":
            start_repl(mode="pvm")
        elif choice == "4":
            filepath = input("Enter .mypy file path to disassemble: ").strip()
            if filepath:
                disassemble_file(filepath)
        elif choice in ("5", "q", "exit"):
            print("Alvida! (Exiting)")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")


def main():
    args = parse_cli_args()

    if args.command == "run":
        run_file(args.file, dialect=args.dialect, mode=args.mode)
    elif args.command == "dis":
        disassemble_file(args.file)
    elif args.command == "transpile":
        transpile_file(args.file, output_path=args.output, dialect=args.dialect)
    elif args.command == "repl":
        start_repl(dialect=args.dialect, mode=args.mode)
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
