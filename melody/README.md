# mELOdy

**Cantus** is a musical language for chess: every move is communicated and understood as melodic phrases.  
This package contains the runtime engine that listens to a MIDI keyboard, decodes phrases into chess moves,
sends them to Stockfish, and plays the engine’s replies back as phrases.

---

## High-level Architecture

melody/
  app.py            ← Orchestrator (main loop, human/engine turns)
  __main__.py       ← Enables `python -m melody`
  key_ctx.py        ← Scale degree mapping & MIDI helpers

  midi/
    ports.py        ← Port discovery & robust open for OUTPUT
    listener.py     ← Queue-based INPUT listener (non-blocking)
    playback.py     ← Render degree sequences as MIDI notes
    earcons.py      ← Small earcons (e.g., “please repeat”)

  phrases/
    capture_stream.py  ← Collect phrases from non-blocking message stream
    canonical.py       ← Canonicalize phrases (White/Black anchors/closures)
    decode_square.py   ← Decode start/landing squares (incl. A/H signatures)
    castling.py        ← Detect castling prelude (#4 motif and direction)
    promotion.py       ← Decode promotion-identification tetrachord
    encode.py          ← Encode engine moves, castling, promotions for playback

---

## Runtime Flow

- **Listen**  
  `midi.listener.MidiListener` opens the input with a callback and buffers messages.

- **Capture**  
  `phrases.capture_stream.collect_structural_phrase_stream()` polls messages without blocking.  
  - With sustain pedal: releasing ends the phrase once enough structure is present.  
  - Without pedal: a silence longer than `phrase_gap_ms` ends the phrase.

- **Decode**  
  - Start/landing squares → `phrases.decode_square` (with `phrases.canonical`)  
  - Castling prelude → `phrases.castling`  
  - Promotion piece → `phrases.promotion`

- **Validate**  
  `python-chess` ensures the move is legal; if not, the app asks for a repeat.

- **Respond**  
  `phrases.encode` builds the engine’s phrase(s); `midi.playback` renders them over MIDI.


## Key Components

### KeyContext
- Converts MIDI notes into **(degree, alteration)** relative to a tonic.  
- Degree **8** is reserved for the **octave anchor** (tonic +12 semitones).  
- Computes MIDI pitch for a given degree for playback.

### MidiListener (graceful Ctrl+C)
- Non-blocking, queue-based input makes signal handling reliable on Windows.  
- Use `.get(timeout=...)` in loops; no blocking calls.

### collect_structural_phrase_stream
- Consolidates ornamented playing into a minimal **structural** sequence:  
  - Collapses adjacent duplicates but preserves a single intentional final repeat.  
  - Uses sustain or time-gap to delimit phrases.


## Running

From the repo root:

```bash
python -m melody
```