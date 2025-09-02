"""Phrase capture from a non-blocking MIDI message stream (queue-backed)."""

import time
from typing import List, Tuple, Optional

import mido

from melody.key_ctx import KeyContext

Degree = Tuple[int, int]  # (degree, alteration)


def _collapse_with_final_repeat(raw: List[Degree]) -> List[Degree]:
    """
    Collapse consecutive duplicate degrees, but keep ONE extra copy at the end
    if the phrase intentionally ends on a repeated degree.
    """
    if not raw:
        return []

    collapsed: List[Degree] = [raw[0]]
    for deg, alt in raw[1:]:
        if collapsed[-1][0] != deg:
            collapsed.append((deg, alt))

    if len(raw) >= 2 and raw[-1][0] == raw[-2][0]:
        if not (len(collapsed) >= 2 and collapsed[-1][0] == collapsed[-2][0]):
            collapsed.append(collapsed[-1])

    return collapsed


def collect_structural_phrase_stream(
    get_msg,
    ctx: KeyContext,
    min_structural: int = 3,
    use_sustain: bool = True,
    poll_timeout: float = 0.10,
) -> List[Degree]:
    """
    Collect a phrase by polling a message source (e.g., MidiListener.get).

    Boundaries:
      - With sustain (CC64): hold while playing; releasing ends the phrase
        after we have at least `min_structural` structural degrees.
      - Without sustain: a silence > `ctx.phrase_gap_ms` ends the phrase
        after `min_structural`.

    The function never blocks on I/O; it polls regularly so Ctrl+C is responsive.
    """
    raw: List[Degree] = []
    last_note_time: Optional[float] = None
    sustain_down = False

    while True:
        msg = get_msg(timeout=poll_timeout)
        now = time.perf_counter()

        if msg is None:
            # Check gap timeout in pedal-less mode
            if not use_sustain and last_note_time is not None:
                gap_ms = (now - last_note_time) * 1000.0
                if gap_ms > ctx.phrase_gap_ms:
                    collapsed = _collapse_with_final_repeat(raw)
                    if len(collapsed) >= min_structural:
                        return collapsed
            continue

        if msg.type == "control_change" and msg.control == 64:
            sustain_down = msg.value >= 64
            if use_sustain and not sustain_down:
                collapsed = _collapse_with_final_repeat(raw)
                if len(collapsed) >= min_structural:
                    return collapsed

        elif msg.type == "note_on" and msg.velocity > 0:
            degree, alt = ctx.degree_of(msg.note)
            raw.append((degree, alt))
            last_note_time = now
