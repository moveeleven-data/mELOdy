"""
Continuously prints incoming MIDI messages (NoteOn/Off) from the Kawai input.
"""
import mido

mido.set_backend("mido.backends.rtmidi")


def pick_input_port(preferred_substring: str = "usb-midi") -> str:
    """Pick an input port containing the substring (case-insensitive), or the first one."""
    inputs = mido.get_input_names()
    if not inputs:
        raise RuntimeError("No MIDI input ports found.")
    for name in inputs:
        if preferred_substring.lower() in name.lower():
            return name
    return inputs[0]


def main() -> None:
    in_name = pick_input_port()
    print(f"Listening on: {in_name}")
    with mido.open_input(in_name) as inp:
        for msg in inp:
            print(msg)

if __name__ == "__main__":
    main()
