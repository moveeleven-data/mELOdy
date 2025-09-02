import mido
mido.set_backend('mido.backends.rtmidi')

print("Inputs:")
for i, n in enumerate(mido.get_input_names()):
    print(f"{i}: {n}")

print("\nOutputs:")
for i, n in enumerate(mido.get_output_names()):
    print(f"{i}: {n}")
