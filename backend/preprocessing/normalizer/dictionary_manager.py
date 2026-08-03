"""
dictionary_manager.py

Manages abbreviations used during log normalization.

"""

from pathlib import Path
import json


class DictionaryManager:
    """
    Creates, stores, loads, and expands abbreviations.
    """

    def __init__(self, dictionary_path=None):
        """
        Initialize the dictionary manager.
        """

        if dictionary_path is None:
            dictionary_path = (
                Path(__file__).parent
                / "abbreviation_dictionary.json"
            )

        self.dictionary_path = Path(dictionary_path)

        self.word_to_token = {}
        self.token_to_word = {}

        self.counter = 1

        if self.dictionary_path.exists():
            self.load()

    def create_token(self, word):
        """
        Create a new token.
        """

        token = f"TK{self.counter:04d}"

        self.counter += 1

        self.word_to_token[word] = token
        self.token_to_word[token] = word

        return token

    def get_token(self, word):
        """
        Obtain an existing token or create a new one.
        """

        word = str(word).lower()

        if word in self.word_to_token:
            return self.word_to_token[word]

        return self.create_token(word)

    def expand_token(self, token):
        """
        Expand a token back into its original form.
        """

        return self.token_to_word.get(token, token)

    def save(self):
        """
        Save the dictionary to disk.
        """

        data = {
            "counter": self.counter,
            "word_to_token": self.word_to_token,
        }

        self.dictionary_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            self.dictionary_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
            )

    def load(self):
        """
        Load the dictionary from disk.
        """

        try:

            with open(
                self.dictionary_path,
                "r",
                encoding="utf-8",
            ) as file:

                content = file.read().strip()

                if not content:
                    return

                data = json.loads(content)

        except (
            FileNotFoundError,
            json.JSONDecodeError,
        ):
            return

        self.counter = data.get(
            "counter",
            1,
        )

        self.word_to_token = data.get(
            "word_to_token",
            {},
        )

        self.token_to_word = {
            token: word
            for word, token in self.word_to_token.items()
        }

    def size(self):
        """
        Return the number of entries.
        """

        return len(self.word_to_token)

    def clear(self):
        """
        Remove all entries from memory.
        """

        self.word_to_token.clear()
        self.token_to_word.clear()

        self.counter = 1

    def __contains__(self, word):

        return word in self.word_to_token

    def __len__(self):

        return len(self.word_to_token)

    def __repr__(self):

        return (
            f"DictionaryManager("
            f"entries={len(self.word_to_token)})"
        )