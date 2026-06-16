"""
Generate the SQL LIKE clause blocks for extract_genai_gov.sql from the lexicons
in dictionaries.py. Run directly to print the clauses, or import build_like_block().

Usage:
    python -m src.build_query
"""

from src.dictionaries import GENAI_LEXICON, GOV_LEXICON, GOV_THEME_TAGS, GOV_URL_SLUGS

# Fields to search for each lexicon (order matters: cheaper fields first).
# V2Themes is deliberately excluded from _GOV_FIELDS: it holds structured
# theme codes (e.g. TAX_FNCACT), not prose, so English keywords like "act" or
# "law" would match it on accidental substrings rather than real signal.
# Theme-code matching against V2Themes is handled separately via
# GOV_THEME_TAGS/_GOV_THEME_FIELD with exact code substrings.
_GENAI_FIELDS = ["AllNames", "Quotations"]
_GOV_FIELDS = ["Quotations"]
_GOV_URL_FIELD = ["DocumentIdentifier"]
_GOV_THEME_FIELD = ["V2Themes"]


def build_like_block(terms: list[str], fields: list[str], indent: int = 4, lower: bool = True) -> str:
    """Build a SQL OR block: each term x each field as a LIKE clause.

    GDELT theme codes (V2Themes) are always upper-case by convention, so pass
    lower=False for those to match the existing style in extract_genai_gov.sql
    rather than wrapping both sides in LOWER() for no reason.
    """
    pad = " " * indent
    clauses = []
    for field in fields:
        for term in terms:
            escaped = term.replace("'", "''")
            target = f"LOWER({field})" if lower else field
            clauses.append(f"{pad}{target} LIKE '%{escaped}%'")
    return ("\n" + pad + "OR ").join(clauses)


def main() -> None:
    print("-- GenAI filter block")
    print("(")
    print("    " + build_like_block(GENAI_LEXICON, _GENAI_FIELDS))
    print(")")
    print()
    print("-- Governance filter block: keyword-in-text + theme tags + URL slugs")
    print("(")
    print("    " + build_like_block(GOV_LEXICON, _GOV_FIELDS))
    print("    OR")
    print("    " + build_like_block(GOV_THEME_TAGS, _GOV_THEME_FIELD, lower=False))
    print("    OR")
    print("    " + build_like_block(GOV_URL_SLUGS, _GOV_URL_FIELD))
    print(")")


if __name__ == "__main__":
    main()
