from __future__ import annotations

import time
from pathlib import Path
import sys
from typing import List, Tuple

# Make the project root importable (so 'melody' resolves)
sys.path.append(str(Path(__file__).resolve().parents[1]))

import mido
from melody.key_ctx import KeyContext

mido.set_backend("mido.backends.rtmidi")


def pick_input_port(preferred_substring: str = "usb-midi") -> str:
    inputs = mido.get_input_names()
    if not inputs:
        raise RuntimeError("No MIDI input ports found.")
    for name in inputs:
        if preferred_substring.lower() in name.lower():
            return name
    return inputs[0]


def open_input_robust(name: str, attempts: int = 3, delay_s: float = 0.5) -> mido.ports.BaseInput:
    last_exc = None
    for _ in range(attempts):
        try:
            return mido.open_input(name)
        except Exception as exc:
            last_exc = exc
            time.sleep(delay_s)
    # last resort: try first available port
    inputs = mido.get_input_names()
    if inputs:
        return mido.open_input(inputs[0])
    raise RuntimeError(f"Failed to open MIDI input '{name}'. Last error: {last_exc!r}")


def main() -> None:
    in_name = pick_input_port()
    print(f"Listening on: {in_name}")

    context = KeyContext(tonic_midi=60, phrase_gap_ms=500)  # try 500ms to start
    phrase: List[Tuple[int, int]] = []  # collapsed structural (degree, alt)
    last_time: float | None = None

    with open_input_robust(in_name) as inp:
        while True:
            msg = inp.receive()
            now = time.perf_counter()

            if msg.type == "control_change" and msg.control == 64:
                print(f"CC64 sustain: {msg.value}")
            elif msg.type == "note_on" and msg.velocity > 0:
                degree, alteration = context.degree_of(msg.note)
                # collapse immediate repeats of the same degree
                if not phrase or phrase[-1][0] != degree:
                    phrase.append((degree, alteration))
                print(f"note_on: midi={msg.note:3d} -> degree={(degree, alteration)}")

            # phrase boundary if silence exceeds threshold
            if last_time is not None and (now - last_time) * 1000 > context.phrase_gap_ms and phrase:
                print("Phrase degrees:", phrase)
                phrase.clear()

            last_time = now


if __name__ == "__main__":
    main()
