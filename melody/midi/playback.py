"""Playback of degree sequences as MIDI notes."""

import time
from typing import Iterable, Tuple

import mido

from melody.key_ctx import KeyContext

Degree = Tuple[int, int]  # (degree, alteration)


def play_degrees(
    outp: mido.ports.BaseOutput,
    ctx: KeyContext,
    degrees: Iterable[Degree],
    channel: int = 0,
    ms_per_note: int = 220,
) -> None:
    """
    Render degrees as short notes. Degree 8 renders as tonic + 12 semitones,
    which naturally places Black phrases an octave above White.
    """
    for deg, _ in degrees:
        note = ctx.midi_of_degree(deg)
        outp.send(mido.Message("note_on", note=note, velocity=100, channel=channel))
        time.sleep(ms_per_note / 1000.0)
        outp.send(mido.Message("note_off", note=note, channel=channel))
        time.sleep(0.04)
