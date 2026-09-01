"""
index_dataset.py

Index the repository dataset into the application's ChromaDB.

The repository dataset is organised by log category rather than
physical server. For local demonstration purposes, categories are
mapped to the application's server identifiers while the original
log category remains preserved in metadata.

Processing flow:

Raw log files
    ↓
PreprocessingPipeline
    ↓
LogRecord objects
    ↓
SynchronizedLogIngestor
    ↓
Chunking
    ↓
Embeddings
    ↓
ChromaDB
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.preprocessing.pipeline import (
    PreprocessingPipeline,
)

from backend.synchronization.ingestion.synchronized_log_ingestor import (
    SynchronizedLogIngestor,
)

from backend.database.chroma import (
    ChromaDatabase,
)


# ----------------------------------------------------------
# Local demonstration source mapping
# ----------------------------------------------------------

SOURCE_MAPPING = {
    "auth": "server-a",
    "dpkg": "server-b",
    "kern": "server-b",
    "syslog": "server-c",
    "dmesg": "server-c",
}


# ----------------------------------------------------------
# File-selection policy
# ----------------------------------------------------------

# Current log files are included.
#
# Rotated authentication logs are also included because they
# contain important historical security events such as:
#
#     AUTH_FAILURE
#     AUTH_SUCCESS
#     SUDO_COMMAND
#
# Large rotated system/kernel/network logs are deliberately
# excluded from the default demonstration rebuild because
# some contain tens of thousands of records and substantially
# increase indexing time without being required for the core
# security-query demonstration.
#
# This keeps the final local demonstration index reproducible
# and reasonably fast.

CURRENT_LOG_NAMES = {
    "auth": {
        "auth.log",
    },
    "dpkg": {
        "dpkg.log",
    },
    "kern": {
        "kern.log",
    },
    "syslog": {
        "syslog.log",
        "syslog",
    },
    "dmesg": {
        "dmesg.log",
        "dmesg",
    },
}


ROTATED_AUTH_LOG_NAMES = {
    "auth.log.1",
    "auth.log.1.gz",
    "auth.log.2.gz",
}


def find_log_files(
    dataset_root,
):
    """
    Discover the raw log files used for the application index.

    The default rebuild includes:

        auth.log
        auth.log.1
        auth.log.1.gz
        auth.log.2.gz
        dpkg.log
        kern.log

    and current syslog/dmesg files when present.

    Rotated syslog, kern, and dmesg files are deliberately excluded
    from the normal demonstration rebuild because some are extremely
    large.

    Returns
    -------
    list[Path]
        Sorted list of files to process.
    """

    files = []

    for path in dataset_root.rglob("*"):

        if not path.is_file():
            continue

        relative_parts = (
            path.relative_to(
                dataset_root
            ).parts
        )

        if not relative_parts:
            continue

        category = relative_parts[0]

        if category not in SOURCE_MAPPING:
            continue

        filename = path.name.lower()

        # ------------------------------------------------------
        # Current log files
        # ------------------------------------------------------

        current_names = {
            name.lower()
            for name in CURRENT_LOG_NAMES.get(
                category,
                set(),
            )
        }

        if filename in current_names:

            files.append(
                path
            )

            continue

        # ------------------------------------------------------
        # Rotated authentication logs
        # ------------------------------------------------------

        if category == "auth":

            if filename in {
                name.lower()
                for name in ROTATED_AUTH_LOG_NAMES
            }:

                files.append(
                    path
                )

                continue

        # ------------------------------------------------------
        # All other rotated logs are deliberately skipped.
        # ------------------------------------------------------

    return sorted(
        files
    )


def source_category(
    path,
    dataset_root,
):
    """
    Return the dataset category for a file.
    """

    relative = path.relative_to(
        dataset_root
    )

    if not relative.parts:
        return None

    return relative.parts[0]


def application_source(
    path,
    dataset_root,
):
    """
    Map the dataset category to an application
    server identifier.
    """

    category = source_category(
        path,
        dataset_root,
    )

    return SOURCE_MAPPING.get(
        category
    )


def clear_live_database():
    """
    Clear the live log collection before rebuilding it.

    This prevents stale vectors from previous indexing runs
    from remaining in the application database.
    """

    database = ChromaDatabase(
        collection_name="log_embeddings"
    )

    try:

        count_before = (
            database.count()
        )

        database.clear()

        print(
            f"Existing live vectors cleared: "
            f"{count_before}"
        )

    finally:

        database.close()


def main():

    dataset_root = (
        PROJECT_ROOT
        / "dataset"
        / "raw"
    )

    if not dataset_root.exists():

        raise FileNotFoundError(
            f"Dataset directory not found: "
            f"{dataset_root}"
        )

    print("=" * 70)
    print("DATASET VECTOR INDEXING")
    print("=" * 70)

    print(
        f"Dataset: {dataset_root}"
    )

    print("\nSource mapping:")

    for category, source in (
        SOURCE_MAPPING.items()
    ):

        print(
            f"  {category:<8} -> {source}"
        )

    # ------------------------------------------------------
    # Discover files
    # ------------------------------------------------------

    files = find_log_files(
        dataset_root
    )

    print(
        f"\nFiles selected for indexing: "
        f"{len(files)}"
    )

    if not files:

        print(
            "No selected log files found."
        )

        return

    # ------------------------------------------------------
    # Display selected files
    # ------------------------------------------------------

    print("\nSelected files:")

    for file_path in files:

        category = source_category(
            file_path,
            dataset_root,
        )

        source = application_source(
            file_path,
            dataset_root,
        )

        print(
            f"  {file_path}"
            f" | category={category}"
            f" | source={source}"
        )

    # ------------------------------------------------------
    # Rebuild live application index
    # ------------------------------------------------------

    clear_live_database()

    pipeline = PreprocessingPipeline()

    ingestor = SynchronizedLogIngestor()

    total_records = 0
    total_new_chunks = 0
    failed_files = 0
    skipped_files = 0

    # Event counters are useful for final verification.
    total_auth_failure = 0
    total_auth_success = 0
    total_sudo_command = 0

    try:

        for file_path in files:

            category = source_category(
                file_path,
                dataset_root,
            )

            source = application_source(
                file_path,
                dataset_root,
            )

            print(
                "\n"
                + "-"
                * 70
            )

            print(
                f"FILE     : {file_path}"
            )

            print(
                f"CATEGORY : {category}"
            )

            print(
                f"SOURCE   : {source}"
            )

            # --------------------------------------------------
            # Preprocess
            # --------------------------------------------------

            try:

                records = pipeline.process(
                    file_path
                )

            except Exception as exc:

                failed_files += 1

                print(
                    f"Processing failed: {exc}"
                )

                continue

            print(
                f"Records: {len(records)}"
            )

            if not records:

                skipped_files += 1

                print(
                    "No records generated."
                )

                continue

            total_records += len(
                records
            )

            # --------------------------------------------------
            # Count important security events
            # --------------------------------------------------

            auth_failure_count = sum(
                1
                for record in records
                if getattr(
                    record,
                    "event_type",
                    None,
                ) == "AUTH_FAILURE"
            )

            auth_success_count = sum(
                1
                for record in records
                if getattr(
                    record,
                    "event_type",
                    None,
                ) == "AUTH_SUCCESS"
            )

            sudo_command_count = sum(
                1
                for record in records
                if getattr(
                    record,
                    "event_type",
                    None,
                ) == "SUDO_COMMAND"
            )

            total_auth_failure += (
                auth_failure_count
            )

            total_auth_success += (
                auth_success_count
            )

            total_sudo_command += (
                sudo_command_count
            )

            if auth_failure_count > 0:

                print(
                    "AUTH_FAILURE records : "
                    f"{auth_failure_count}"
                )

            if auth_success_count > 0:

                print(
                    "AUTH_SUCCESS records : "
                    f"{auth_success_count}"
                )

            if sudo_command_count > 0:

                print(
                    "SUDO_COMMAND records : "
                    f"{sudo_command_count}"
                )

            # --------------------------------------------------
            # Ingest records
            # --------------------------------------------------

            try:

                new_chunks = (
                    ingestor.ingest_source_records(
                        source_id=source,
                        records=records,
                    )
                )

            except Exception as exc:

                failed_files += 1

                print(
                    f"Ingestion failed: {exc}"
                )

                continue

            total_new_chunks += len(
                new_chunks
            )

            stats = (
                ingestor.ingestion_statistics()
            )

            print(
                "Chunks created       : "
                f"{stats['chunks_created']}"
            )

            print(
                "Chunks skipped       : "
                f"{stats['chunks_skipped']}"
            )

            print(
                "Chunks indexed       : "
                f"{stats['chunks_indexed']}"
            )

            print(
                "Embeddings generated : "
                f"{stats['embeddings_generated']}"
            )

    finally:

        ingestor.close()

    # ------------------------------------------------------
    # Final database summary
    # ------------------------------------------------------

    database = ChromaDatabase(
        collection_name="log_embeddings"
    )

    try:

        final_count = (
            database.count()
        )

        stored = database.get()

    finally:

        database.close()

    # ------------------------------------------------------
    # Count stored event types
    # ------------------------------------------------------

    stored_metadatas = stored.get(
        "metadatas",
        [],
    )

    stored_auth_failure = sum(
        1
        for metadata in stored_metadatas
        if isinstance(
            metadata,
            dict,
        )
        and metadata.get(
            "event_type"
        ) == "AUTH_FAILURE"
    )

    stored_auth_success = sum(
        1
        for metadata in stored_metadatas
        if isinstance(
            metadata,
            dict,
        )
        and metadata.get(
            "event_type"
        ) == "AUTH_SUCCESS"
    )

    stored_sudo_command = sum(
        1
        for metadata in stored_metadatas
        if isinstance(
            metadata,
            dict,
        )
        and metadata.get(
            "event_type"
        ) == "SUDO_COMMAND"
    )

    # ------------------------------------------------------
    # Final summary
    # ------------------------------------------------------

    print(
        "\n"
        + "="
        * 70
    )

    print(
        "INDEXING SUMMARY"
    )

    print(
        "="
        * 70
    )

    print(
        f"Files selected          : "
        f"{len(files)}"
    )

    print(
        f"Files failed            : "
        f"{failed_files}"
    )

    print(
        f"Files skipped           : "
        f"{skipped_files}"
    )

    print(
        f"Records processed       : "
        f"{total_records}"
    )

    print(
        f"New chunks indexed      : "
        f"{total_new_chunks}"
    )

    print(
        f"Total vectors in Chroma : "
        f"{final_count}"
    )

    print(
        "\nImportant security events"
    )

    print(
        f"AUTH_FAILURE stored     : "
        f"{stored_auth_failure}"
    )

    print(
        f"AUTH_SUCCESS stored     : "
        f"{stored_auth_success}"
    )

    print(
        f"SUDO_COMMAND stored     : "
        f"{stored_sudo_command}"
    )

    print(
        "\nSecurity records processed"
    )

    print(
        f"AUTH_FAILURE processed  : "
        f"{total_auth_failure}"
    )

    print(
        f"AUTH_SUCCESS processed  : "
        f"{total_auth_success}"
    )

    print(
        f"SUDO_COMMAND processed  : "
        f"{total_sudo_command}"
    )

    print(
        "="
        * 70
    )


if __name__ == "__main__":
    main()