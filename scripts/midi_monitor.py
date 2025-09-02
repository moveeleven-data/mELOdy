import mido
mido.set_backend('mido.backends.rtmidi')

# Pick your Kawai input (shows up as "USB-MIDI 0" on your box)
ins = mido.get_input_names()
in_name = next((n for n in ins if "usb-midi" in n.lower()), None)
assert in_name, f"No USB-MIDI input found. Inputs: {ins}"
print("Listening on:", in_name)

with mido.open_input(in_name) as inp:
    for msg in inp:
        print(msg)
