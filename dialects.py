"""
Dialect Keyword Mappings for Python 'Flavour'.

Defines keyword translations from custom vernacular dialects
(e.g., Hinglish, Gen-Z) to standard Python keywords and built-in functions.
"""

HINGLISH_MAP = {
    # Control Flow
    "agar": "if",
    "warna_agar": "elif",
    "warna": "else",
    "jabtak": "while",
    "har": "for",
    "mein": "in",
    "ruko": "break",
    "aage": "continue",
    "pass_karo": "pass",

    # Functions & Classes
    "kaam": "def",
    "wapas": "return",
    "varg": "class",

    # Exception Handling
    "koshish": "try",
    "pakdo": "except",
    "aakhirkar": "finally",
    "phenko": "raise",

    # Logical & Boolean
    "sahi": "True",
    "galat": "False",
    "shunya": "None",
    "khali": "None",
    "aur": "and",
    "ya": "or",
    "nahi": "not",
    "hai": "is",

    # Import / Context
    "le_aao": "import",
    "se": "from",
    "saath": "with",
    "jaise": "as",

    # Common Built-ins
    "likho": "print",
    "batao": "print",
    "bolo": "print",
    "pucho": "input",
    "ginti": "range",
    "ginte": "range",
    "lambai": "len",
    "jodo": "sum",
}

GENZ_MAP = {
    # Control Flow
    "lowkey": "if",
    "highkey": "elif",
    "deadass": "else",
    "spin": "while",
    "vibe": "for",
    "wit": "in",
    "period": "break",
    "pass_it": "continue",
    "ghost": "pass",

    # Functions & Return
    "flex": "def",
    "bop": "return",
    "squad": "class",

    # Exception Handling
    "vibe_check": "try",
    "catch_hands": "except",
    "yeet": "raise",

    # Logical & Boolean
    "fr": "True",
    "no_cap": "True",
    "cap": "False",
    "sus": "None",
    "and_that": "and",
    "or_nah": "or",
    "nah": "not",

    # Common Built-ins
    "spill": "print",
    "listen": "input",
    "count": "range",
    "size": "len",
}

DIALECTS = {
    "hinglish": HINGLISH_MAP,
    "genz": GENZ_MAP,
}

def get_dialect(name: str = "hinglish") -> dict:
    """Retrieve dialect keyword mapping by name (case-insensitive)."""
    normalized = name.strip().lower()
    if normalized not in DIALECTS:
        available = ", ".join(repr(k) for k in DIALECTS)
        raise ValueError(f"Unknown dialect '{name}'. Available: {available}")
    return DIALECTS[normalized]

