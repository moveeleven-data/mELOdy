"""Castling motif detection."""

from typing import List, Optional, Tuple

Degree = Tuple[int, int]  # (degree, alteration)


def detect_castling_motif(degrees: List[Degree]) -> Optional[str]:
    """
    Detect the castling prelude for either color:

      anchor (1 or 8) → #4 (degree 4, alt +1) → 5 → small run
        - ascend from 5 ⇒ "kingside"
        - descend from 5 ⇒ "queenside"
        - if no run, default to "kingside"
    """
    if len(degrees) < 3:
        return None

    d1, _ = degrees[0]
    d2, a2 = degrees[1]
    d3, _ = degrees[2]

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
