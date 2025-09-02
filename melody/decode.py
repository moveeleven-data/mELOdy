from __future__ import annotations

import time
from typing import List, Tuple, Optional
import mido

from melody.key_ctx import KeyContext

FILE_FROM_DEGREE: dict[int, str] = {1:'a',2:'b',3:'c',4:'d',5:'e',6:'f',7:'g',8:'h'}


# ---------- Collapse while preserving an intentional final repeat ----------

def _collapse_with_final_repeat(raw: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Collapse consecutive duplicates, but keep ONE extra copy if the phrase
    ends with a repeated degree (e.g., 1→4→4).
    """
    if not raw:
        return []
    collapsed: List[Tuple[int, int]] = [raw[0]]
    for d, a in raw[1:]:
        if collapsed[-1][0] != d:
            collapsed.append((d, a))
    # If raw ends with a repeat, keep one duplicate at the end.
    if len(raw) >= 2 and raw[-1][0] == raw[-2][0]:
        if not (len(collapsed) >= 2 and collapsed[-1][0] == collapsed[-2][0]):
            collapsed.append(collapsed[-1])
    return collapsed


# ---------- Phrase collection ----------

def collect_structural_phrase(
    port: mido.ports.BaseInput,
    ctx: KeyContext,
    min_structural: int = 3,
    use_sustain: bool = True
) -> List[Tuple[int, int]]:
    """
    Capture a phrase and return a collapsed (degree, alt) sequence.

    Boundaries:
      - With sustain (CC64): hold while playing, release to end (once we have ≥ min_structural).
      - Without sustain: a silence > ctx.phrase_gap_ms ends the phrase (once we have ≥ min_structural).
    """
    raw: List[Tuple[int, int]] = []
    last_note_time: float | None = None
    sustain_down = False

    while True:
        msg = port.receive()
        now = time.perf_counter()

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

        # time gap fallback
        if (
            not use_sustain
            and last_note_time is not None
            and (now - last_note_time) * 1000 > ctx.phrase_gap_ms
        ):
            collapsed = _collapse_with_final_repeat(raw)
            if len(collapsed) >= min_structural:
                return collapsed


# ---------- Canonicalization ----------

def canonicalize_white(degrees: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    White: must start on 1.
    Drop a trailing 1 only if it is a closure beyond the minimal 3 notes AND
    the sequence does NOT begin with an A-file mordent [1,7,1,...].
    """
    if not degrees or degrees[0][0] != 1:
        return []
    cleaned = degrees[:]
    if (
        len(cleaned) >= 4
        and cleaned[-1][0] == 1
        and not (len(cleaned) >= 3 and cleaned[1][0] == 7 and cleaned[2][0] == 1)
    ):
        cleaned.pop()
    return cleaned


def canonicalize_black(degrees: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Black: must start on 8.
    Drop a trailing 8 only if it is a closure beyond the minimal 3 notes AND
    the sequence does NOT begin with the H-file mordent [8,2,8,...].
    """
    if not degrees or degrees[0][0] != 8:
        return []
    cleaned = degrees[:]
    if (
        len(cleaned) >= 4
        and cleaned[-1][0] == 8
        and not (len(cleaned) >= 3 and cleaned[1][0] == 2 and cleaned[2][0] == 8)
    ):
        cleaned.pop()
    return cleaned


# ---------- Square decoders (A/H signatures + short-form landing) ----------

def decode_white_square(degrees: List[Tuple[int, int]], short_form_ok: bool = False) -> Optional[str]:
    """
    White file signatures:
      A-file: mordent around 1 => [1, 7, 1, <rank>]  (requires 4+ structural degrees)
      H-file: octave leap     => [1, 8, <rank...>]
      Else: normal            => [1, file, <rank...>]

    Rank = last structural degree; if short_form_ok and only [1,file], set rank=file (landing short-form).
    """
    seq = canonicalize_white(degrees)
    n = len(seq)
    if n < 2:
        return None

    # A-file mordent (explicit rank required to avoid colliding with g1 = [1,7,1])
    if n >= 4 and seq[1][0] == 7 and seq[2][0] == 1:
        file_deg = 1
        rank_deg = seq[-1][0]

    # H-file octave
    elif seq[1][0] == 8:
        file_deg = 8
        if n >= 3:
            rank_deg = seq[-1][0]
        elif short_form_ok:
            rank_deg = 8
        else:
            return None

    # Normal pattern
    else:
        file_deg = seq[1][0]
        if n >= 3:
            rank_deg = seq[-1][0]
        elif short_form_ok:
            rank_deg = file_deg
        else:
            return None

    if not (1 <= rank_deg <= 8):
        return None
    return f"{FILE_FROM_DEGREE[file_deg]}{rank_deg}"


def decode_black_square(degrees: List[Tuple[int, int]], short_form_ok: bool = False) -> Optional[str]:
    """
    Black file signatures (mirrored and collision-free with g8):
      H-file: forward mordent around 8 => [8, 2, 8, <rank>]  (requires 4+)
      A-file: octave flip              => [8, 1, <rank...>]
      Else:   normal                   => [8, file, <rank...>]

    Rank = last structural degree; if short_form_ok and only [8,file], set rank=file (landing short-form).
    """
    seq = canonicalize_black(degrees)
    n = len(seq)
    if n < 2:
        return None

    # H-file forward mordent [8,2,8,...]
    if n >= 4 and seq[1][0] == 2 and seq[2][0] == 8:
        file_deg = 8
        rank_deg = seq[-1][0]

    # A-file octave flip [8,1,...]
    elif seq[1][0] == 1:
        file_deg = 1
        if n >= 3:
            rank_deg = seq[-1][0]
        elif short_form_ok:
            rank_deg = 1
        else:
            return None

    # Normal
    else:
        file_deg = seq[1][0]
        if n >= 3:
            rank_deg = seq[-1][0]
        elif short_form_ok:
            rank_deg = file_deg
        else:
            return None

    if not (1 <= rank_deg <= 8):
        return None
    return f"{FILE_FROM_DEGREE[file_deg]}{rank_deg}"


# ---------- Castling motif (both colors) ----------

def detect_castling_motif(degrees: List[Tuple[int, int]]) -> Optional[str]:
    """
    Detect the castling prelude for either color:
      anchor (1 or 8), then degree 4 with # (alt +1), then degree 5.
    Returns 'kingside' (ascending from 5) or 'queenside' (descending),
    defaulting to 'kingside' if the run is omitted.
    """
    if len(degrees) < 3:
        return None
    d1, _  = degrees[0]
    d2, a2 = degrees[1]
    d3, _  = degrees[2]

    if d1 not in (1, 8):
        return None
    if not (d2 == 4 and a2 == +1 and d3 == 5):
        return None

    if len(degrees) >= 4:
        d4, _ = degrees[3]
        if d4 > 5:
            return "kingside"
        if d4 < 5:
            return "queenside"
    return "kingside"


# ---------- Promotion piece (third phrase, tetrachord) ----------

def decode_promotion_piece(degrees: List[Tuple[int, int]]) -> Optional[str]:
    """
    Promotion cue may start on 1 (White) or 8 (Black), but must include
    anchor → ♭2 (degree 2, alt -1).

    After the cue, we evaluate tetrachord *steps* reached:
        step 1: (1, 0)           -> rook (r)
        step 2: (2, -1)          -> knight (n)
        step 3: (3, -1)          -> bishop (b)
        step 4: (3,  0) (♮3)     -> queen  (q)

    The piece is determined by the highest step reached.
    """
    if len(degrees) < 2:
        return None
    d1, _  = degrees[0]
    d2, a2 = degrees[1]
    if d1 not in (1, 8):
        return None
    if not (d2 == 2 and a2 == -1):
        return None

    step_max = 0
    for d, a in degrees:
        if (d, a) == (1, 0):
            step_max = max(step_max, 1)
        elif (d, a) == (2, -1):
            step_max = max(step_max, 2)
        elif (d, a) == (3, -1):
            step_max = max(step_max, 3)
        elif (d, a) == (3, 0):
            step_max = max(step_max, 4)

    return {1: "r", 2: "n", 3: "b", 4: "q"}.get(step_max)
