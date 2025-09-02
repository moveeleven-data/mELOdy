<p align="center">
  <img src="docs/assets/melody_logo2.png" alt="mELOdy logo" width="400"/>
</p>

<h3 align="center"> Chess Through Musical Improvisation</h3><br/>

<p style="text-align:center;">
  Play a complete game of chess entirely through music.<br/><br/>
  Every move is expressed as a melodic phrase, with the engine answering in the same language.
</p><br/><br/>

<p align="center"><b>▷ See It in Action (demo coming soon)</b></p>

---

## How It Works

**Perform:** Enter chess moves as two short melodic phrases on a MIDI keyboard (start square, then landing square).  

**Interpret:** Phrases are mapped to files and ranks using tonal rules (with mirrored ascent/descents for White and 
Black).  

**Validate:** Moves are checked for legality via <a href="https://python-chess.readthedocs.io/">python-chess</a> and 
passed to the engine.  

**Respond:** Stockfish replies with its own move, rendered back as a melodic phrase.  

**Play on:** The entire game unfolds musically, without a board or notation.

[Learn the Cantus musical language →](docs/cantus_language.md)


## Key Features

| Capability | What you get |
|------------|--------------|
| Musical protocol | Deterministic grammar for files, ranks, castling, promotions |
| Real-time MIDI | Sub-10ms I/O via `mido` + `python-rtmidi` |
| Engine integration | Stockfish with Elo capped for human-like play |
| Bi-directional play | Both you and the engine communicate purely in music |
| UX gestures | Sustain pedal for take-back, commit, or draw offers |


## Quickstart

### Prereqs
- Python 3.10+  
- A USB-MIDI keyboard (tested with Kawai MP11SE)  
- Stockfish binary (download from [stockfishchess.org](https://stockfishchess.org/download/))  

### Install
```bash
git clone https://github.com/your-username/mELOdy.git
cd mELOdy
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Run

```bash
python -m melody
```

### Tech Stack

- Python
- mido + python-rtmidi (MIDI I/O)
- python-chess (rules & legality)
- Stockfish (engine)
- Optional: LC0 Maia nets for human-like style

---

<p align="center">
  <img src="https://img.shields.io/badge/♩_♪_♫_♬_♭_♮_♯-mELOdy-black?style=for-the-badge&labelColor=%23a38115" alt="mELOdy banner"/>
</p>