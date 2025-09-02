from __future__ import annotations

import time
from typing import Iterable, List, Tuple
import mido

from melody.key_ctx import KeyContext

DEGREE_FROM_FILE = {'a':1,'b':2,'c':3,'d':4,'e':5,'f':6,'g':7,'h':8}


def phrase_for_square(square: str, side_white: bool) -> List[Tuple[int, int]]:
    """
    Minimal identifying degree sequence for one square (start or landing).

    White (anchor 1):
      - A-file: [1, 7, 1, rank]
      - H-file: [1, 8,    rank]
      - Else:   [1, file, rank]

    Black (anchor 8):
      - H-file: [8, 2, 8, rank]   (forward mordent; avoids g8 collision)
      - A-file: [8, 1,    rank]
      - Else:   [8, file, rank]
    """
    file_letter = square[0]
    rank_digit = int(square[1])
    file_deg = DEGREE_FROM_FILE[file_letter]
    if side_white:
        if file_letter == 'a':
            return [(1, 0), (7, 0), (1, 0), (rank_digit, 0)]
        if file_letter == 'h':
            return [(1, 0), (8, 0), (rank_digit, 0)]
        return [(1, 0), (file_deg, 0), (rank_digit, 0)]
    else:
        if file_letter == 'h':
            return [(8, 0), (2, 0), (8, 0), (rank_digit, 0)]
        if file_letter == 'a':
            return [(8, 0), (1, 0), (rank_digit, 0)]
        return [(8, 0), (file_deg, 0), (rank_digit, 0)]


def phrase_for_castling(side_white: bool, kingside: bool) -> List[Tuple[int, int]]:
    """anchor (1 or 8), then #4 (alt +1), then 5, then a small directional run."""
    anchor = 1 if side_white else 8
    prelude = [(anchor, 0), (4, +1), (5, 0)]
    run = [(6, 0), (7, 0)] if kingside else [(4, 0), (3, 0)]
    return prelude + run


def phrase_for_promotion(piece: str, side_white: bool) -> List[Tuple[int, int]]:
    """
    Promotion phrase after landing on last rank:

      cue: anchor (1 or 8) – ♭2  => (anchor,0), (2,-1)
      identify: climb through tetrachord steps up to TARGET:
          step 1: (1, 0)        -> rook (r)
          step 2: (2, -1)       -> knight (n)
          step 3: (3, -1)       -> bishop (b)
          step 4: (3,  0)       -> queen  (q)

    We emit the sequence [step1, step2, ... stepN].
    """
    target_step = {"r": 1, "n": 2, "b": 3, "q": 4}[piece]
    anchor = 1 if side_white else 8

    seq: List[Tuple[int, int]] = [(anchor, 0), (2, -1)]  # cue
    steps = [(1, 0), (2, -1), (3, -1), (3, 0)]
    seq.extend(steps[:target_step])
    return seq


def play_degrees(
    outp: mido.ports.BaseOutput,
    ctx: KeyContext,
    degrees: Iterable[Tuple[int, int]],
    channel: int = 0,
    ms_per_note: int = 220
) -> None:
    """
    Render degrees as short notes at the tonic’s octave.
    Degree 8 renders as tonic +12 semitones (C up an octave),
    which naturally makes Black phrases start high and drop down.
    """
    for d, _ in degrees:
        note = ctx.midi_of_degree(d)
        outp.send(mido.Message("note_on", note=note, velocity=100, channel=channel))
        time.sleep(ms_per_note / 1000.0)
        outp.send(mido.Message("note_off", note=note, channel=channel))
        time.sleep(0.04)
