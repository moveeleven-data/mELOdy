"""
KeyContext: maps MIDI notes to robust diatonic degree buckets for a major key.

Bucket rules (relative to the tonic's pitch class):
  0  -> 1  (tonic; use 8 if played an octave above the tonic)
  1,2 -> 2
  3,4 -> 3
  5,6 -> 4
  7   -> 5
  8,9 -> 6
  10,11 -> 7

This collapses common accidentals onto their nearest functional degree,
making phrase identity resilient to coloration/ornaments.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Dict

# Map semitone offsets (mod 12) to degree buckets (1..7)
BUCKET_MAP: Dict[int, int] = {
    0: 1,
    1: 2, 2: 2,
    3: 3, 4: 3,
    5: 4, 6: 4,
    7: 5,
    8: 6, 9: 6,
    10: 7, 11: 7,
}

@dataclass(slots=True)
class KeyContext:
    """
    Encapsulates tonic and phrase boundary settings.

    Attributes
    ----------
    tonic_midi : int
        MIDI note number for the tonic reference (e.g., 60 == C4).
    phrase_gap_ms : int
        Minimum silence (ms) that marks a phrase boundary.
    octave_anchor_threshold : int
        If a tonic-class note is >= tonic_midi + this many semitones,
        we classify it as degree 8 (octave anchor) instead of 1.
        Default 12 (one octave).
    """
    tonic_midi: int = 60
    phrase_gap_ms: int = 400
    octave_anchor_threshold: int = 12

    def degree_of(self, midi_note: int) -> Tuple[int, int]:
        """
        Map a MIDI note to a degree bucket. Returns (degree, alteration).

        For this bucketed identity, alteration is always 0 (kept for API compatibility).
        Degree is 1..7 normally; returns 8 when tonic is intentionally played an octave above.
        """
        rel = (midi_note - self.tonic_midi) % 12
        degree = BUCKET_MAP[rel]

        # Special-case tonic: allow explicit octave anchor (used for Black starts).
        if rel == 0 and midi_note - self.tonic_midi >= self.octave_anchor_threshold:
            degree = 8  # explicit "tonic+octave"

        return degree, 0  # alteration collapsed by design
