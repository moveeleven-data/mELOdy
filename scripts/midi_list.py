import mido
print("Inputs:")
for i,n in enumerate(mido.get_input_names()): print(i, n)
print("\nOutputs:")
for i,n in enumerate(mido.get_output_names()): print(i, n)