"""
Key context: pitch-class bucketing, alteration tagging, and MIDI helpers.

Degree mapping (relative to the tonic's pitch class):
  0        → 1   (tonic)     — use 8 if explicitly one octave above
  1, 2     → 2   (Db/D)
  3, 4     → 3   (Eb/E)
  5, 6     → 4   (F/F#)
  7        → 5   (G)
  8, 9     → 6   (Ab/A)
  10, 11   → 7   (Bb/B)
"""

from dataclasses import dataclass
from typing import Dict, Tuple


# Semitone bucket → degree
BUCKET_MAP: Dict[int, int] = {
    0: 1,
    1: 2, 2: 2,
    3: 3, 4: 3,
    5: 4, 6: 4,
    7: 5,
    8: 6, 9: 6,
    10: 7, 11: 7,
}

# Diatonic offsets for playback / alteration computation (in semitones)
DEGREE_OFFSETS: Dict[int, int] = {
    1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11, 8: 12
}


@dataclass(slots=True)
class KeyContext:
    """Tonic reference and phrase boundary configuration."""

    tonic_midi: int = 60                  # e.g., 60 == C4
    phrase_gap_ms: int = 500              # time-gap boundary (when not using pedal)
    octave_anchor_threshold: int = 12     # ≥ +12 semitones → degree 8 (octave)

    def degree_of(self, midi_note: int) -> Tuple[int, int]:
        """
        Convert a MIDI note to (degree, alteration).

        Degree is usually 1..7; returns 8 when the tonic pitch class occurs
        at least one octave above the tonic (explicit octave anchor).

        Alteration is -1, 0, or +1 relative to the diatonic offset of the
        chosen degree (used to detect #4, ♭2/♭3 in motifs).
        """
        rel_pc = (midi_note - self.tonic_midi) % 12
        degree = BUCKET_MAP[rel_pc]

        # Explicit octave anchor: tonic at or above one octave → degree 8
        if rel_pc == 0 and midi_note - self.tonic_midi >= self.octave_anchor_threshold:
            return 8, 0

        base_pc = DEGREE_OFFSETS[degree] % 12
        diff = (rel_pc - base_pc) % 12

        if diff == 0:
            alt = 0
        elif diff == 1:
            alt = +1
        elif diff == 11:  # == -1 mod 12
            alt = -1
        else:
            alt = 0

        return degree, alt

    def midi_of_degree(self, degree: int, octave_shift: int = 0) -> int:
        """
        Convert a degree (1..8) to a MIDI note near the tonic.

        Degree 8 uses +12 semitones; other degrees use diatonic offsets.
        `octave_shift` shifts by whole octaves after the base mapping.
        """
        base = 12 if degree == 8 else DEGREE_OFFSETS[degree]
        return self.tonic_midi + base + 12 * octave_shift
