"""
Tests for SynchronizedRAGRunner.
"""


class FakeSynchronizationRunner:
    """
    Fake synchronization runner used to isolate
    the combined workflow from rsync.
    """

    def __init__(self):
        self.calls = 0

    def sync_once(self):
        self.calls += 1

        return {
            "server-a": True,
            "server-b": True,
        }

    def info(self):
        return {
            "component": "FakeSynchronizationRunner",
            "source_count": 2,
            "sync_interval": 60,
            "running": False,
        }


class FakeRAGPipeline:
    """
    Fake RAG pipeline used to isolate the runner
    from preprocessing, embeddings and ChromaDB.
    """

    def __init__(self):
        self.calls = 0
        self.vector_count = 0
        self.closed = False

    def process_all(self):
        self.calls += 1

        self.vector_count = 3

        return {
            "server-a": [
                "chunk:server-a:0",
            ],
            "server-b": [
                "chunk:server-b:0",
                "chunk:server-b:1",
            ],
        }

    def count(self):
        return self.vector_count

    def info(self):
        return {
            "component": "FakeRAGPipeline",
            "vector_count": self.vector_count,
        }

    def close(self):
        self.closed = True


def create_runner():
    from backend.synchronization.pipeline.synchronized_rag_runner import (
        SynchronizedRAGRunner,
    )

    synchronization_runner = (
        FakeSynchronizationRunner()
    )

    rag_pipeline = FakeRAGPipeline()

    runner = SynchronizedRAGRunner(
        synchronization_runner=synchronization_runner,
        rag_pipeline=rag_pipeline,
    )

    return (
        runner,
        synchronization_runner,
        rag_pipeline,
    )


def test_run_once_synchronizes_before_rag_processing():
    """
    Verify that one complete cycle performs
    synchronization and then RAG processing.
    """

    runner, synchronization_runner, rag_pipeline = (
        create_runner()
    )

    result = runner.run_once()

    assert synchronization_runner.calls == 1

    assert rag_pipeline.calls == 1

    assert result == {
        "server-a": [
            "chunk:server-a:0",
        ],
        "server-b": [
            "chunk:server-b:0",
            "chunk:server-b:1",
        ],
    }


def test_run_once_returns_source_results():
    """
    Verify that results remain separated by source.
    """

    runner, _, _ = create_runner()

    result = runner.run_once()

    assert set(result.keys()) == {
        "server-a",
        "server-b",
    }

    assert len(result["server-a"]) == 1

    assert len(result["server-b"]) == 2


def test_multiple_cycles_repeat_both_stages():
    """
    Verify that each run_once call performs a new
    synchronization and RAG processing cycle.
    """

    runner, synchronization_runner, rag_pipeline = (
        create_runner()
    )

    runner.run_once()
    runner.run_once()

    assert synchronization_runner.calls == 2

    assert rag_pipeline.calls == 2


def test_runner_count():
    """
    Verify that vector count is delegated to the
    RAG pipeline.
    """

    runner, _, _ = create_runner()

    runner.run_once()

    assert runner.count() == 3


def test_runner_info():
    """
    Verify combined runner information.
    """

    runner, _, _ = create_runner()

    info = runner.info()

    assert info["component"] == (
        "SynchronizedRAGRunner"
    )

    assert (
        info["synchronization"]["component"]
        == "FakeSynchronizationRunner"
    )

    assert (
        info["rag_pipeline"]["component"]
        == "FakeRAGPipeline"
    )

    assert info["vector_count"] == 0


def test_runner_close():
    """
    Verify that closing the runner delegates
    to the RAG pipeline.
    """

    runner, _, rag_pipeline = create_runner()

    runner.close()

    assert rag_pipeline.closed is True