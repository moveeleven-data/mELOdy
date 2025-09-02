"""Canonicalization for White/Black phrases (anchors and closures)."""

from typing import List, Tuple

Degree = Tuple[int, int]  # (degree, alteration)


def canonicalize_white(degrees: List[Degree]) -> List[Degree]:
    """
    White phrases must start on 1. If a trailing 1 is just a closure beyond
    the minimal identity (≥4 structural degrees), drop it — unless the phrase
    begins with the A-file mordent [1,7,1,...].
    """
    if not degrees or degrees[0][0] != 1:
        return []

    cleaned = degrees[:]
    has_a_mordent = len(cleaned) >= 3 and cleaned[1][0] == 7 and cleaned[2][0] == 1
    trailing_closure = len(cleaned) >= 4 and cleaned[-1][0] == 1

    if trailing_closure and not has_a_mordent:
        cleaned.pop()

    return cleaned


def canonicalize_black(degrees: List[Degree]) -> List[Degree]:
    """
    Black phrases must start on 8. If a trailing 8 is just a closure beyond
    the minimal identity (≥4 structural degrees), drop it — unless the phrase
    begins with the H-file forward mordent [8,2,8,...].
    """
    if not degrees or degrees[0][0] != 8:
        return []

    cleaned = degrees[:]
    has_h_mordent = len(cleaned) >= 3 and cleaned[1][0] == 2 and cleaned[2][0] == 8
    trailing_closure = len(cleaned) >= 4 and cleaned[-1][0] == 8

    if trailing_closure and not has_h_mordent:
        cleaned.pop()

    return cleaned
