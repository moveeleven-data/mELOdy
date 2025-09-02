"""
List available MIDI input and output ports using the RtMidi backend.
"""
import mido

mido.set_backend("mido.backends.rtmidi")

def main() -> None:
    print("Inputs:")
    for i, name in enumerate(mido.get_input_names()):
        print(f"{i}: {name}")

    print("\nOutputs:")
    for i, name in enumerate(mido.get_output_names()):
        print(f"{i}: {name}")

if __name__ == "__main__":
    main()
