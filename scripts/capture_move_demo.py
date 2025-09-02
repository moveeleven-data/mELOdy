from __future__ import annotations

import time
from pathlib import Path
import sys
from typing import Iterable, List, Tuple, Optional

# Make the project root importable (so 'melody' resolves)
sys.path.append(str(Path(__file__).resolve().parents[1]))

import mido
from melody.key_ctx import KeyContext

mido.set_backend("mido.backends.rtmidi")

FILE_FROM_DEGREE: dict[int, str] = {1: 'a', 2: 'b', 3: 'c', 4: 'd', 5: 'e', 6: 'f', 7: 'g', 8: 'h'}

# --- config you can tweak ---
PHRASE_GAP_MS = 500           # try 500–600ms if you pause between notes
MIN_STRUCTURAL_DEGREES = 3    # anchor -> fileRef -> rank
USE_SUSTAIN_FOR_BOUNDARY = True  # hold sustain while playing a phrase; release to end


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
    inputs = mido.get_input_names()
    if inputs:
        return mido.open_input(inputs[0])
    raise RuntimeError(f"Failed to open MIDI input '{name}'. Last error: {last_exc!r}")


def collect_structural_phrase(
    port: mido.ports.BaseInput,
    ctx: KeyContext,
    min_structural: int = MIN_STRUCTURAL_DEGREES,
    use_sustain: bool = USE_SUSTAIN_FOR_BOUNDARY
) -> List[Tuple[int, int]]:
    """
    Collect a phrase and return a collapsed structural degree sequence.
    Ends when:
      - sustain (CC64) is released AND we already have >= min_structural, OR
      - silence gap exceeds ctx.phrase_gap_ms AND we have >= min_structural.
    """
    collapsed: list[tuple[int, int]] = []
    last_note_time: Optional[float] = None
    sustain_down = False

    while True:
        msg = port.receive()
        now = time.perf_counter()

        if msg.type == "control_change" and msg.control == 64:
            # sustain pedal state
            sustain_down = msg.value >= 64
            if use_sustain and not sustain_down and len(collapsed) >= min_structural:
                return collapsed

        elif msg.type == "note_on" and msg.velocity > 0:
            degree, _ = ctx.degree_of(msg.note)
            if not collapsed or collapsed[-1][0] != degree:
                collapsed.append((degree, 0))
            last_note_time = now

        # time-based phrase end (only if we already have enough structure)
        if (
            last_note_time is not None
            and (now - last_note_time) * 1000 > ctx.phrase_gap_ms
            and len(collapsed) >= min_structural
        ):
            return collapsed


def canonicalize_white_phrase(degrees: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    For White:
    - Must anchor on 1.
    - If the phrase ends on 1 (closing tonic), drop that trailing 1.
    """
    if not degrees or degrees[0][0] != 1:
        return []
    cleaned = degrees[:]
    if len(cleaned) >= 3 and cleaned[-1][0] == 1:
        cleaned.pop()
    return cleaned


def decode_white_phrase_to_square(degrees: List[Tuple[int, int]]) -> Optional[str]:
    """
    Naive identity rule for White after canonicalization:
      [1, file_ref, ..., rank] -> '<file><rank>'
    """
    seq = canonicalize_white_phrase(degrees)
    if len(seq) < 2:
        return None

    file_ref = seq[1][0]
    file_letter = FILE_FROM_DEGREE.get(file_ref)
    if file_letter is None:
        return None

    rank_deg = seq[-1][0]
    if not (1 <= rank_deg <= 8):
        return None

    return f"{file_letter}{rank_deg}"


def main() -> None:
    in_name = pick_input_port()
    print(f"Listening on: {in_name}")

    ctx = KeyContext(tonic_midi=60, phrase_gap_ms=PHRASE_GAP_MS)

    with open_input_robust(in_name) as inp:
        print("Play two phrases (start square, then landing square).")
        if USE_SUSTAIN_FOR_BOUNDARY:
            print("Tip: hold sustain while playing each phrase; release to end it.")

        start_degrees = collect_structural_phrase(inp, ctx)
        print("Start phrase degrees:", start_degrees)

        landing_degrees = collect_structural_phrase(inp, ctx)
        print("Landing phrase degrees:", landing_degrees)

        from_sq = decode_white_phrase_to_square(start_degrees)
        to_sq = decode_white_phrase_to_square(landing_degrees)

        if from_sq and to_sq:
            print(f"Decoded move (white, naive): {from_sq}{to_sq}")
        else:
            print("Could not decode (white, naive). "
                  "Keep phrases compact: anchor→fileRef→rank "
                  "(e.g., 1→5→2 for e2, then 1→5→4 for e4).")


if __name__ == "__main__":
    main()
