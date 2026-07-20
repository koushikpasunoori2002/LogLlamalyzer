"""
persistent_reader.py

Reads only newly added log data and remembers progress.
"""

import glob
import json
import os


class PersistentReader:

    def __init__(self, state_file="reader_state.json"):
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as file:
                return json.load(file)
        return {}

    def _save_state(self):
        with open(self.state_file, "w") as file:
            json.dump(self.state, file, indent=4)

    def read_increment(self, log_file):

        result = []

        stat = os.stat(log_file)

        current = {
            "device": stat.st_dev,
            "inode": stat.st_ino,
            "offset": 0
        }

        previous = self.state.get(log_file)

        # First time
        if previous is None:

            with open(log_file, "r", errors="ignore") as file:
                data = file.read()

            current["offset"] = os.path.getsize(log_file)

            self.state[log_file] = current

            self._save_state()

            return data

        # Same file

        if (previous["device"], previous["inode"]) == (stat.st_dev, stat.st_ino):

            with open(log_file, "r", errors="ignore") as file:

                file.seek(previous["offset"])

                result.append(file.read())

            previous["offset"] = os.path.getsize(log_file)

            self._save_state()

            return "".join(result)

        # Rotated

        candidates = sorted(glob.glob(log_file + "*"))

        for candidate in candidates:

            if candidate.endswith(".gz"):
                continue

            try:
                cstat = os.stat(candidate)
            except FileNotFoundError:
                continue

            if (cstat.st_dev, cstat.st_ino) == (previous["device"], previous["inode"]):

                with open(candidate, "r", errors="ignore") as file:
                    file.seek(previous["offset"])
                    result.append(file.read())

                break

        with open(log_file, "r", errors="ignore") as file:
            result.append(file.read())

        self.state[log_file] = {
            "device": stat.st_dev,
            "inode": stat.st_ino,
            "offset": os.path.getsize(log_file)
        }

        self._save_state()

        return "".join(result)