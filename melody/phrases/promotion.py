"""Promotion identification phrase decoding (tetrachord steps)."""

from typing import List, Optional, Tuple

Degree = Tuple[int, int]  # (degree, alteration)


def decode_promotion_piece(degrees: List[Degree]) -> Optional[str]:
    """
    Decode the promotion identification phrase (after landing on last rank).

    Required cue:
      anchor (1 or 8) → ♭2  == (2, -1)

    Identification by tetrachord *steps* reached:
      step 1: (1,  0)  → rook   (r)
      step 2: (2, -1)  → knight (n)
      step 3: (3, -1)  → bishop (b)
      step 4: (3,  0)  → queen  (q)

    The highest step reached determines the piece.
    """
    if len(degrees) < 2:
        return None

    d1, _ = degrees[0]
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
