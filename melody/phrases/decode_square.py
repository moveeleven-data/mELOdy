"""Decoding of start/landing square phrases for White and Black."""

from typing import List, Optional, Tuple

from melody.phrases.canonical import canonicalize_white, canonicalize_black

Degree = Tuple[int, int]  # (degree, alteration)

FILE_FROM_DEGREE: dict[int, str] = {
    1: "a", 2: "b", 3: "c", 4: "d",
    5: "e", 6: "f", 7: "g", 8: "h",
}


def _decode_square_common(
    seq: List[Degree],
    short_form_ok: bool,
    file_deg: int | None,
    rank_index: int,
) -> Optional[str]:
    """
    Common tail for square decoding. `file_deg` may already be fixed by
    a file signature (A/H). Otherwise, it's the second degree in the phrase.
    """
    if file_deg is None:
        file_deg = seq[1][0]

    if len(seq) >= rank_index + 1:
        rank_deg = seq[-1][0]
    elif short_form_ok:
        rank_deg = file_deg
    else:
        return None

    if not (1 <= rank_deg <= 8):
        return None

    file_letter = FILE_FROM_DEGREE[file_deg]
    return f"{file_letter}{rank_deg}"


def decode_white_square(
    degrees: List[Degree],
    short_form_ok: bool = False,
) -> Optional[str]:
    """
    White file signatures:
      A-file: [1, 7, 1, <rank>]   (require 4+ to avoid colliding with g1)
      H-file: [1, 8, <rank...>]
      Else:   [1, file, <rank...>]

    Landing short-form:
      If `short_form_ok` and only [1, file], interpret rank=file.
    """
    seq = canonicalize_white(degrees)
    if len(seq) < 2:
        return None

    # A-file mordent (explicit rank required)
    if len(seq) >= 4 and seq[1][0] == 7 and seq[2][0] == 1:
        return _decode_square_common(seq, False, file_deg=1, rank_index=3)

    # H-file octave
    if seq[1][0] == 8:
        return _decode_square_common(seq, short_form_ok, file_deg=8, rank_index=2)

    # Normal ([1, file, rank...])
    return _decode_square_common(seq, short_form_ok, file_deg=None, rank_index=2)


def decode_black_square(
    degrees: List[Degree],
    short_form_ok: bool = False,
) -> Optional[str]:
    """
    Black file signatures:
      H-file: [8, 2, 8, <rank>]   (forward mordent; require 4+)
      A-file: [8, 1, <rank...>]
      Else:   [8, file, <rank...>]

    Landing short-form:
      If `short_form_ok` and only [8, file], interpret rank=file.
    """
    seq = canonicalize_black(degrees)
    if len(seq) < 2:
        return None

    # H-file forward mordent (explicit rank required)
    if len(seq) >= 4 and seq[1][0] == 2 and seq[2][0] == 8:
        return _decode_square_common(seq, False, file_deg=8, rank_index=3)

    # A-file octave flip
    if seq[1][0] == 1:
        return _decode_square_common(seq, short_form_ok, file_deg=1, rank_index=2)

    # Normal ([8, file, rank...])
    return _decode_square_common(seq, short_form_ok, file_deg=None, rank_index=2)
