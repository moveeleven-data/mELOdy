"""
Sends a short C-major chord to the Kawai output so you can hear it in headphones.
"""
import time
import mido

mido.set_backend("mido.backends.rtmidi")

MIDI_CHANNEL: int = 0  # 0-based (0 == MIDI channel 1)


def pick_output_port(preferred_substring: str = "usb-midi") -> str:
    """Pick an output port containing the substring (case-insensitive), or the last one."""
    outputs = mido.get_output_names()
    if not outputs:
        raise RuntimeError("No MIDI output ports found.")
    for name in outputs:
        if preferred_substring.lower() in name.lower():
            return name
    return outputs[-1]


def main() -> None:
    out_name = pick_output_port()
    print(f"Sending to: {out_name}")
    with mido.open_output(out_name) as outp:
        for note in (60, 64, 67):  # C, E, G
            outp.send(mido.Message("note_on", note=note, velocity=100, channel=MIDI_CHANNEL))
        time.sleep(1.0)
        for note in (60, 64, 67):
            outp.send(mido.Message("note_off", note=note, channel=MIDI_CHANNEL))

if __name__ == "__main__":
    main()
