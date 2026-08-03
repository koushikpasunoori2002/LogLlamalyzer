"""
test_dictionary_manager.py

Tests the DictionaryManager class.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.preprocessing.normalizer import DictionaryManager


def main():

    dictionary = DictionaryManager()

    print("=" * 70)
    print("DICTIONARY MANAGER TEST")
    print("=" * 70)

    words = [
        "failed",
        "password",
        "authentication",
        "connection",
        "failed",
        "password",
    ]

    print("\nCreating tokens\n")

    for word in words:

        token = dictionary.get_token(word)

        print(f"{word:<20} -> {token}")

    print("\n")

    print("=" * 70)
    print("Dictionary size")
    print("=" * 70)

    print(dictionary.size())

    print("\n")

    print("=" * 70)
    print("Token expansion")
    print("=" * 70)

    for token in dictionary.token_to_word:

        expanded = dictionary.expand_token(token)

        print(f"{token:<10} -> {expanded}")

    print("\nSaving dictionary ...")

    dictionary.save()

    print("Dictionary saved successfully.")

    print("\n")

    print("=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()