import time, mido
mido.set_backend('mido.backends.rtmidi')

# Pick your Kawai output (you saw "USB-MIDI 1")
outs = mido.get_output_names()
out_name = next((n for n in outs if "usb-midi" in n.lower()), None)
assert out_name, f"No USB-MIDI output found. Outputs: {outs}"
print("Sending to:", out_name)

with mido.open_output(out_name) as outp:
    for n in (60, 64, 67):  # C major triad
        outp.send(mido.Message('note_on', note=n, velocity=96))
    time.sleep(1.2)
    for n in (60, 64, 67):
        outp.send(mido.Message('note_off', note=n, velocity=0))
