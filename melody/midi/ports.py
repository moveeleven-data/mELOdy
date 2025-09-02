"""MIDI port discovery and robust open helpers."""

import time
import mido

# RtMidi backend on Windows
mido.set_backend("mido.backends.rtmidi")


def pick_input_port(preferred_substring: str = "usb-midi") -> str:
    """Pick an input port, favoring names containing `preferred_substring`."""
    ports = mido.get_input_names()
    if not ports:
        raise RuntimeError("No MIDI input ports found.")
    for name in ports:
        if preferred_substring.lower() in name.lower():
            return name
    return ports[0]


def pick_output_port(preferred_substring: str = "usb-midi") -> str:
    """Pick an output port, favoring names containing `preferred_substring`."""
    ports = mido.get_output_names()
    if not ports:
        raise RuntimeError("No MIDI output ports found.")
    for name in ports:
        if preferred_substring.lower() in name.lower():
            return name
    return ports[-1]


def open_input_robust(
    name: str,
    attempts: int = 3,
    delay_s: float = 0.5,
) -> mido.ports.BaseInput:
    """Open an input port with retries, then fall back to the first port."""
    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            return mido.open_input(name)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(delay_s)

    fallback = mido.get_input_names()
    if fallback:
        return mido.open_input(fallback[0])

    raise RuntimeError(
        f"Failed to open MIDI input '{name}'. Last error: {last_exc!r}"
    )


def open_output_robust(
    name: str,
    attempts: int = 3,
    delay_s: float = 0.5,
) -> mido.ports.BaseOutput:
    """Open an output port with retries, then fall back to the last port."""
    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            return mido.open_output(name)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(delay_s)

    fallback = mido.get_output_names()
    if fallback:
        return mido.open_output(fallback[-1])

    raise RuntimeError(
        f"Failed to open MIDI output '{name}'. Last error: {last_exc!r}"
    )
