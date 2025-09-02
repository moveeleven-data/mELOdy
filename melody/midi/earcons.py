"""Simple, unobtrusive earcons."""

import time
import mido


def earcon_retry(outp: mido.ports.BaseOutput, channel: int = 0) -> None:
    """
    Two short low beeps: gentle “please repeat” cue.
    No “OK” earcon by design, to keep the flow minimal.
    """
    note = 48  # C3
    for _ in range(2):
        outp.send(mido.Message("note_on", note=note, velocity=100, channel=channel))
        time.sleep(0.12)
        outp.send(mido.Message("note_off", note=note, channel=channel))
        time.sleep(0.08)
