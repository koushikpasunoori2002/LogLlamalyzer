"""
synchronization_runner.py

Runs periodic synchronization for all configured log sources.
"""

import time

from ..config.synchronization_config import SynchronizationConfig
from ..rsync.rsync_synchronizer import RsyncSynchronizer


class SynchronizationRunner:
    """
    Coordinates periodic synchronization.

    The runner is independent of the number of configured
    sources. All source information comes from the configuration.
    """

    def __init__(
        self,
        config: SynchronizationConfig,
        synchronizer: RsyncSynchronizer,
        sleep_function=time.sleep,
    ):
        self.config = config
        self.synchronizer = synchronizer
        self.sleep_function = sleep_function

        self.running = False

    def sync_once(self):
        """
        Perform one synchronization cycle.

        Every configured source is synchronized once.
        """

        return self.synchronizer.sync_all(
            self.config.sources
        )

    def run(self):
        """
        Continuously synchronize configured sources.

        The interval is controlled by SynchronizationConfig.
        """

        self.running = True

        while self.running:

            self.sync_once()

            if not self.running:
                break

            self.sleep_function(
                self.config.sync_interval
            )

    def stop(self):
        """
        Stop the synchronization loop.
        """

        self.running = False

    def info(self):
        """
        Return runner metadata.
        """

        return {
            "component": "SynchronizationRunner",
            "source_count": len(
                self.config.sources
            ),
            "sync_interval": (
                self.config.sync_interval
            ),
            "running": self.running,
        }