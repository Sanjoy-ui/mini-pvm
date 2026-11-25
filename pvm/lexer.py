"""
Lexer for Hinglish / Vernacular dialects using Python's standard tokenizer.
Converts source code into a clean stream of typed tokens for the AST Parser.
"""

import tokenize
import io
from dataclasses import dataclass
from typing import List, Any

# Dialect keyword mappings to normalized canonical keywords
KEYWORD_MAPPINGS = {
    # Hinglish
    "agar": "agar",
    "warna_agar": "warna_agar",
    "warna": "warna",
    "jabtak": "jabtak",
    "har": "har",
    "mein": "mein",
    "likho": "likho",
    "batao": "likho",
    "bolo": "likho",
    "sahi": "sahi",
    "galat": "galat",
    "shunya": "shunya",
    "khali": "shunya",

    # Gen-Z
    "lowkey": "agar",
    "highkey": "warna_agar",
    "deadass": "warna",
    "spin": "jabtak",
    "vibe": "har",
    "wit": "mein",
    "spill": "likho",
    "fr": "sahi",
    "no_cap": "sahi",
    "cap": "galat",
    "sus": "shunya",
}

@dataclass
class Token:
    type: str       # 'KEYWORD', 'IDENT', 'NUMBER', 'STRING', 'OP', 'INDENT', 'DEDENT', 'NEWLINE', 'EOF'
    value: Any
    line: int

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r}, line={self.line})"


def tokenize_source(source_code: str) -> List[Token]:
    """Tokenizes custom vernacular source code into a stream of Token instances."""
    source_bytes = source_code.encode("utf-8")
    byte_reader = io.BytesIO(source_bytes).readline

    raw_tokens = list(tokenize.tokenize(byte_reader))
    tokens: List[Token] = []

    i = 0
    while i < len(raw_tokens):
        tok = raw_tokens[i]
        tok_type = tok.type
        tok_str = tok.string
        line_num = tok.start[0]

        # Ignore encoding comments and standalone comment tokens
        if tok_type in (tokenize.ENCODING, tokenize.COMMENT):
            i += 1
            continue

        if tok_type == tokenize.NAME:
            # Check for two-word "warna agar" -> "warna_agar"
            if tok_str == "warna" and i + 1 < len(raw_tokens) and raw_tokens[i + 1].string == "agar":
                tokens.append(Token("KEYWORD", "warna_agar", line_num))
                i += 2
                continue

            normalized = KEYWORD_MAPPINGS.get(tok_str)
            if normalized:
                if normalized in ("sahi", "galat"):
                    tokens.append(Token("BOOL", normalized == "sahi", line_num))
                elif normalized == "shunya":
                    tokens.append(Token("NONE", None, line_num))
                else:
                    tokens.append(Token("KEYWORD", normalized, line_num))
            else:
                tokens.append(Token("IDENT", tok_str, line_num))

        elif tok_type == tokenize.NUMBER:
            # Parse as int or float
            try:
                num_val = int(tok_str) if "." not in tok_str else float(tok_str)
            except ValueError:
                num_val = float(tok_str)
            tokens.append(Token("NUMBER", num_val, line_num))

        elif tok_type == tokenize.STRING:
            # Strip quotes and evaluate escape sequences safely
            str_val = eval(tok_str)
            tokens.append(Token("STRING", str_val, line_num))

        elif tok_type == tokenize.OP:
            tokens.append(Token("OP", tok_str, line_num))

        elif tok_type in (tokenize.NEWLINE, tokenize.NL):
            # Only append NEWLINE if previous token was not already a NEWLINE
            if tokens and tokens[-1].type != "NEWLINE":
                tokens.append(Token("NEWLINE", "\n", line_num))

        elif tok_type == tokenize.INDENT:
            tokens.append(Token("INDENT", "INDENT", line_num))

        elif tok_type == tokenize.DEDENT:
            tokens.append(Token("DEDENT", "DEDENT", line_num))

        elif tok_type == tokenize.ENDMARKER:
            tokens.append(Token("EOF", "EOF", line_num))

        i += 1

    # Ensure trailing NEWLINE before EOF if missing
    if tokens and tokens[-1].type != "EOF":
        tokens.append(Token("EOF", "EOF", tokens[-1].line))

    return tokens
