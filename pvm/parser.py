"""
Recursive Descent Parser for Hinglish / Vernacular source code.
Builds an Abstract Syntax Tree (AST) representing statements and expressions.
"""

from dataclasses import dataclass
from typing import List, Optional, Any, Tuple
from pvm.lexer import Token

# --- AST Node Definitions ---

class ASTNode:
    pass

@dataclass
class ConstExpr(ASTNode):
    value: Any

@dataclass
class VarExpr(ASTNode):
    name: str

@dataclass
class UnaryOpExpr(ASTNode):
    op: str
    expr: ASTNode

@dataclass
class BinOpExpr(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode

@dataclass
class CallExpr(ASTNode):
    func_name: str
    args: List[ASTNode]

@dataclass
class AssignStmt(ASTNode):
    target: str
    expr: ASTNode

@dataclass
class PrintStmt(ASTNode):
    expr: ASTNode

@dataclass
class IfStmt(ASTNode):
    condition: ASTNode
    then_body: List[ASTNode]
    elif_blocks: List[Tuple[ASTNode, List[ASTNode]]]
    else_body: Optional[List[ASTNode]]

@dataclass
class WhileStmt(ASTNode):
    condition: ASTNode
    body: List[ASTNode]

@dataclass
class ForStmt(ASTNode):
    target: str
    iterable: ASTNode
    body: List[ASTNode]

@dataclass
class Program(ASTNode):
    statements: List[ASTNode]


# --- Parser Class ---

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current_token(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def peek_token(self, offset: int = 1) -> Token:
        target = self.pos + offset
        if target < len(self.tokens):
            return self.tokens[target]
        return self.tokens[-1]

    def match(self, tok_type: str, value: Any = None) -> bool:
        tok = self.current_token()
        if tok.type != tok_type:
            return False
        if value is not None and tok.value != value:
            return False
        return True

    def consume(self, tok_type: str = None, value: Any = None) -> Token:
        tok = self.current_token()
        if tok_type is not None and tok.type != tok_type:
            raise SyntaxError(
                f"Line {tok.line}: Expected token type '{tok_type}', got '{tok.type}' ({tok.value!r})"
            )
        if value is not None and tok.value != value:
            raise SyntaxError(
                f"Line {tok.line}: Expected '{value}', got '{tok.value}'"
            )
        self.pos += 1
        return tok

    def skip_newlines(self):
        while self.match("NEWLINE"):
            self.consume("NEWLINE")

    def parse(self) -> Program:
        statements = []
        self.skip_newlines()
        while not self.match("EOF"):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()
        return Program(statements)

    def parse_statement(self) -> ASTNode:
        self.skip_newlines()
        tok = self.current_token()

        # 1. Print statement: 'likho' / 'batao'
        if tok.type == "KEYWORD" and tok.value == "likho":
            self.consume("KEYWORD", "likho")
            # Can be likho(expr) or likho expr
            if self.match("OP", "("):
                self.consume("OP", "(")
                expr = self.parse_expr()
                self.consume("OP", ")")
            else:
                expr = self.parse_expr()
            if self.match("NEWLINE"):
                self.consume("NEWLINE")
            return PrintStmt(expr)

        # 2. While loop: 'jabtak'
        if tok.type == "KEYWORD" and tok.value == "jabtak":
            self.consume("KEYWORD", "jabtak")
            cond = self.parse_expr()
            self.consume("OP", ":")
            body = self.parse_block()
            return WhileStmt(cond, body)

        # 2b. For loop: 'har' target 'mein' iterable:
        if tok.type == "KEYWORD" and tok.value == "har":
            self.consume("KEYWORD", "har")
            target_tok = self.consume("IDENT")
            self.consume("KEYWORD", "mein")
            iterable = self.parse_expr()
            self.consume("OP", ":")
            body = self.parse_block()
            return ForStmt(target_tok.value, iterable, body)

        # 3. If condition: 'agar'
        if tok.type == "KEYWORD" and tok.value == "agar":
            self.consume("KEYWORD", "agar")
            cond = self.parse_expr()
            self.consume("OP", ":")
            then_body = self.parse_block()

            elif_blocks = []
            while self.match("KEYWORD", "warna_agar"):
                self.consume("KEYWORD", "warna_agar")
                elif_cond = self.parse_expr()
                self.consume("OP", ":")
                elif_body = self.parse_block()
                elif_blocks.append((elif_cond, elif_body))

            else_body = None
            if self.match("KEYWORD", "warna"):
                self.consume("KEYWORD", "warna")
                self.consume("OP", ":")
                else_body = self.parse_block()

            return IfStmt(cond, then_body, elif_blocks, else_body)

        # 4. Variable assignment: IDENT = expr
        if tok.type == "IDENT" and self.peek_token(1).type == "OP" and self.peek_token(1).value == "=":
            name_tok = self.consume("IDENT")
            self.consume("OP", "=")
            expr = self.parse_expr()
            if self.match("NEWLINE"):
                self.consume("NEWLINE")
            return AssignStmt(name_tok.value, expr)

        # 5. Expression as statement
        expr = self.parse_expr()
        if self.match("NEWLINE"):
            self.consume("NEWLINE")
        return expr

    def parse_block(self) -> List[ASTNode]:
        """Parses an indented suite of statements."""
        self.consume("NEWLINE")
        self.consume("INDENT")

        statements = []
        self.skip_newlines()
        while not self.match("DEDENT") and not self.match("EOF"):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()

        if self.match("DEDENT"):
            self.consume("DEDENT")

        return statements

    # --- Expression Parsing with Precedence ---

    def parse_expr(self) -> ASTNode:
        return self.parse_comparison()

    def parse_comparison(self) -> ASTNode:
        expr = self.parse_addition()
        comp_ops = ("==", "!=", "<", "<=", ">", ">=")
        while self.match("OP") and self.current_token().value in comp_ops:
            op_tok = self.consume("OP")
            right = self.parse_addition()
            expr = BinOpExpr(expr, op_tok.value, right)
        return expr

    def parse_addition(self) -> ASTNode:
        expr = self.parse_multiplication()
        while self.match("OP") and self.current_token().value in ("+", "-"):
            op_tok = self.consume("OP")
            right = self.parse_multiplication()
            expr = BinOpExpr(expr, op_tok.value, right)
        return expr

    def parse_multiplication(self) -> ASTNode:
        expr = self.parse_unary()
        while self.match("OP") and self.current_token().value in ("*", "/", "%"):
            op_tok = self.consume("OP")
            right = self.parse_unary()
            expr = BinOpExpr(expr, op_tok.value, right)
        return expr

    def parse_unary(self) -> ASTNode:
        if self.match("OP", "-"):
            self.consume("OP", "-")
            return UnaryOpExpr("-", self.parse_unary())
        if self.match("OP", "+"):
            self.consume("OP", "+")
            return self.parse_unary()
        return self.parse_primary()

    def parse_primary(self) -> ASTNode:
        tok = self.current_token()

        if tok.type == "NUMBER":
            self.consume("NUMBER")
            return ConstExpr(tok.value)

        if tok.type == "STRING":
            self.consume("STRING")
            return ConstExpr(tok.value)

        if tok.type == "BOOL":
            self.consume("BOOL")
            return ConstExpr(tok.value)

        if tok.type == "NONE":
            self.consume("NONE")
            return ConstExpr(None)

        if tok.type == "IDENT":
            name_tok = self.consume("IDENT")
            # Function call: e.g. str(x), int(x)
            if self.match("OP", "("):
                self.consume("OP", "(")
                args = []
                if not self.match("OP", ")"):
                    args.append(self.parse_expr())
                    while self.match("OP", ","):
                        self.consume("OP", ",")
                        args.append(self.parse_expr())
                self.consume("OP", ")")
                return CallExpr(name_tok.value, args)
            return VarExpr(name_tok.value)

        if self.match("OP", "("):
            self.consume("OP", "(")
            expr = self.parse_expr()
            self.consume("OP", ")")
            return expr

        raise SyntaxError(f"Line {tok.line}: Unexpected token {tok.type} ({tok.value!r})")


def parse_source(source_code: str) -> Program:
    """Helper to tokenize and parse source code into a Program AST."""
    from pvm.lexer import tokenize_source
    tokens = tokenize_source(source_code)
    parser = Parser(tokens)
    return parser.parse()
