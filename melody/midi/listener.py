"""Queue-backed MIDI input listener for responsive (non-blocking) reads."""

from contextlib import AbstractContextManager
from queue import Queue, Empty
from typing import Optional

import mido


class MidiListener(AbstractContextManager):
    """
    Open a MIDI input with a callback that enqueues messages.

    Use .get(timeout) to poll; returns a mido Message or None.
    Works well with Ctrl+C since there is no blocking receive().
    """

    def __init__(self, port_name: str):
        self._queue: Queue = Queue()
        self._port_name = port_name
        self._port = mido.open_input(port_name, callback=self._queue.put)

    @property
    def port_name(self) -> str:
        return self._port_name

    def get(self, timeout: float = 0.10) -> Optional[mido.Message]:
        """Return the next message or None if no message within `timeout` seconds."""
        try:
            return self._queue.get(timeout=timeout)
        except Empty:
            return None

    def close(self) -> None:
        if self._port is not None:
            self._port.close()
            self._port = None

    # Context manager support
    def __enter__(self) -> "MidiListener":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
