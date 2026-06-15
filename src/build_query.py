"""
Generate the SQL LIKE clause blocks for extract_genai_gov.sql from the lexicons
in dictionaries.py. Run directly to print the clauses, or import build_like_block().

Usage:
    python -m src.build_query
"""

from src.dictionaries import GENAI_LEXICON, GOV_LEXICON

# Fields to search for each lexicon (order matters: cheaper fields first)
_GENAI_FIELDS = ["AllNames", "Quotations"]
_GOV_FIELDS = ["Quotations", "V2Themes"]


def build_like_block(terms: list[str], fields: list[str], indent: int = 4) -> str:
    """Build a SQL OR block: each term × each field as a LOWER() LIKE clause."""
    pad = " " * indent
    clauses = []
    for field in fields:
        for term in terms:
            escaped = term.replace("'", "''")
            clauses.append(f"{pad}LOWER({field}) LIKE '%{escaped}%'")
    return ("\n" + pad + "OR ").join(clauses)


def main() -> None:
    print("-- GenAI filter block")
    print("(")
    print("    " + build_like_block(GENAI_LEXICON, _GENAI_FIELDS))
    print(")")
    print()
    print("-- Governance filter block")
    print("(")
    print("    " + build_like_block(GOV_LEXICON, _GOV_FIELDS))
    print(")")


if __name__ == "__main__":
    main()
