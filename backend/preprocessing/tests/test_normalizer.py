"""
test_normalizer.py

Tests the LogNormalizer class.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.preprocessing.normalizer import (
    DictionaryManager,
    LogNormalizer,
)


def main():

    dictionary = DictionaryManager()

    normalizer = LogNormalizer(dictionary)

    print("=" * 70)
    print("LOG NORMALIZER TEST")
    print("=" * 70)

    samples = [
        "Failed password for root from 192.168.1.10",
        "Accepted password for admin from 10.0.0.5",
        "Connection refused by server",
        "Authentication failure detected",
        "Failed password for invalid user root",
    ]

    for text in samples:

        normalized = normalizer.normalize_text(text)

        expanded = normalizer.expand_text(normalized)

        print("\n" + "-" * 70)

        print("ORIGINAL")
        print(text)

        print("\nNORMALIZED")
        print(normalized)

        print("\nEXPANDED")
        print(expanded)

    print("\n")

    print("=" * 70)
    print("DICTIONARY CONTENTS")
    print("=" * 70)

    for word, token in dictionary.word_to_token.items():

        print(f"{word:<20} -> {token}")

    print("\n")

    print("=" * 70)
    print("TOTAL TOKENS")
    print("=" * 70)

    print(dictionary.size())

    print("\n")

    print("=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()