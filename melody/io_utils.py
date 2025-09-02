from __future__ import annotations

import time
import mido

# RtMidi backend
mido.set_backend("mido.backends.rtmidi")


def pick_input_port(preferred_substring: str = "usb-midi") -> str:
    ins = mido.get_input_names()
    if not ins:
        raise RuntimeError("No MIDI input ports found.")
    for name in ins:
        if preferred_substring.lower() in name.lower():
            return name
    return ins[0]


def pick_output_port(preferred_substring: str = "usb-midi") -> str:
    outs = mido.get_output_names()
    if not outs:
        raise RuntimeError("No MIDI output ports found.")
    for name in outs:
        if preferred_substring.lower() in name.lower():
            return name
    return outs[-1]


def open_input_robust(name: str, attempts: int = 3, delay_s: float = 0.5) -> mido.ports.BaseInput:
    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            return mido.open_input(name)
        except Exception as exc:
            last_exc = exc
            time.sleep(delay_s)
    ins = mido.get_input_names()
    if ins:
        return mido.open_input(ins[0])
    raise RuntimeError(f"Failed to open MIDI input '{name}'. Last error: {last_exc!r}")


def open_output_robust(name: str, attempts: int = 3, delay_s: float = 0.5) -> mido.ports.BaseOutput:
    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            return mido.open_output(name)
        except Exception as exc:
            last_exc = exc
            time.sleep(delay_s)
    outs = mido.get_output_names()
    if outs:
        return mido.open_output(outs[-1])
    raise RuntimeError(f"Failed to open MIDI output '{name}'. Last error: {last_exc!r}")


# ---- Earcons ----
# No “OK” motif (per your request). Only a gentle retry cue for errors.

def earcon_retry(outp: mido.ports.BaseOutput, channel: int = 0) -> None:
    """Two short low beeps: “please repeat”."""
    for _ in range(2):
        outp.send(mido.Message("note_on", note=48, velocity=100, channel=channel))  # C3
        time.sleep(0.12)
        outp.send(mido.Message("note_off", note=48, channel=channel))
        time.sleep(0.08)
