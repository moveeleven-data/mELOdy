"""
Run mELOdy: play a full game vs Stockfish using Cantus (melodic phrases).

This module is imported by:
  - python -m melody   (via melody/__main__.py)
"""

import os
import time
from pathlib import Path
from typing import Optional

import chess
import chess.engine
import mido

from melody.key_ctx import KeyContext
from melody.midi.earcons import earcon_retry
from melody.midi.listener import MidiListener
from melody.midi.playback import play_degrees
from melody.midi.ports import (
    open_output_robust,
    pick_input_port,
    pick_output_port,
)
from melody.phrases.castling import detect_castling_motif
from melody.phrases.decode_square import decode_black_square, decode_white_square
from melody.phrases.encode import phrase_for_castling, phrase_for_promotion, phrase_for_square
from melody.phrases.promotion import decode_promotion_piece
from melody.phrases.capture_stream import collect_structural_phrase_stream

mido.set_backend("mido.backends.rtmidi")
MIDI_CHANNEL = 0


# ------------------------------ engine path ------------------------------

def _resolve_engine_path() -> Path:
    """
    Locate Stockfish executable in this order:
      1) MELODY_STOCKFISH env var (absolute path)
      2) <repo>/tools/stockfish/stockfish.exe
      3) first occurrence of 'stockfish' on PATH
    """
    env_path = os.environ.get("MELODY_STOCKFISH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    p = Path(__file__).parents[1] / "tools" / "stockfish" / "stockfish.exe"
    if p.exists():
        return p

    from shutil import which
    exe = which("stockfish")
    if exe:
        return Path(exe)

    raise FileNotFoundError(
        "Stockfish not found. Put stockfish.exe in tools/stockfish/ "
        "or set MELODY_STOCKFISH to an absolute path."
    )


ENGINE_PATH = _resolve_engine_path()


# ------------------------------ small helpers ----------------------------

def _decode_square_for_side(
    degrees,
    side_white: bool,
    landing: bool,
) -> Optional[str]:
    """Decode a square for White or Black; allow short-form only on landing."""
    if side_white:
        return decode_white_square(degrees, short_form_ok=landing)
    return decode_black_square(degrees, short_form_ok=landing)


def _print_help_banner() -> None:
    print("\n=== How to play (Cantus) ===")
    print("• Phrase boundary:")
    print("  Hold sustain while playing a phrase; release the pedal to end it.")
    print("• Normal move = TWO phrases:")
    print("  1) Start square     2) Landing square")
    print("  White starts on 1 (tonic). Black (engine) starts on 8 (tonic↑).")
    print("  Example (White): e2 = 1→5→2   (C→G→D)")
    print("  Example (Black): e7 = 8→5→7   (C↑→G→B)")
    print("  Landing short-form allowed: 1→file  or  1→file→file")
    print("  Example: d4 = 1→4  (or 1→4→4)")
    print("• Edge files:")
    print("  White A-file: 1–7–1–<rank>        |  White H-file: 1–8–<rank>")
    print("  Black H-file: 8–2–8–<rank> (engine) |  Black A-file: 8–1–<rank> (engine)")
    print("• Castling (both colors): anchor – #4 – 5, then a short run:")
    print("  Ascend from 5 ⇒ Kingside   |  Descend from 5 ⇒ Queenside")
    print("• Promotion (both colors) — third phrase after a pawn reaches last rank:")
    print("  Cue: anchor – ♭2 (ascending minor second).")
    print("  Identify with tetrachord steps:")
    print("    step 1 = 1 (tonic)        → rook (r)")
    print("    step 2 = ♭2 (degree 2,-1) → knight (n)")
    print("    step 3 = ♭3 (degree 3,-1) → bishop (b)")
    print("    step 4 = ♮3 (degree 3, 0) → queen  (q)")
    print("=============================\n")


# ------------------------------ turn handlers ----------------------------

def _handle_human_turn(
    board: chess.Board,
    listener: MidiListener,
    outp: mido.ports.BaseOutput,
    ctx: KeyContext,
) -> bool:
    """
    Capture and apply a human move.
    Returns True if a legal move was pushed; otherwise False (caller should loop).
    """
    side_white_to_move = board.turn
    side_str = "White" if side_white_to_move else "Black"
    print(f"\nYour move ({side_str}).")

    # First phrase: castling prelude OR start-square phrase.
    p1 = collect_structural_phrase_stream(
        get_msg=listener.get,
        ctx=ctx,
        min_structural=3,
        use_sustain=True,
    )

    castle_side = detect_castling_motif(p1)
    if castle_side:
        move_uci = "e1g1" if side_white_to_move else "e8g8"
        if castle_side == "queenside":
            move_uci = "e1c1" if side_white_to_move else "e8c8"

        move = chess.Move.from_uci(move_uci)
        if move in board.legal_moves:
            board.push(move)
            print("Last move (you):", move.uci())
            return True

        print("Illegal castling attempt; please repeat.")
        earcon_retry(outp, MIDI_CHANNEL)
        return False

    # Normal move: two phrases (start, landing).
    start_sq = _decode_square_for_side(
        degrees=p1,
        side_white=side_white_to_move,
        landing=False,
    )
    if not start_sq:
        print("Could not decode start square; please repeat.")
        earcon_retry(outp, MIDI_CHANNEL)
        return False

    p2 = collect_structural_phrase_stream(
        get_msg=listener.get,
        ctx=ctx,
        min_structural=3,
        use_sustain=True,
    )
    landing_sq = _decode_square_for_side(
        degrees=p2,
        side_white=side_white_to_move,
        landing=True,
    )
    if not landing_sq:
        print("Could not decode landing square; please repeat.")
        earcon_retry(outp, MIDI_CHANNEL)
        return False

    if start_sq == landing_sq:
        print(f"Start and landing are identical ({start_sq}). Please repeat.")
        earcon_retry(outp, MIDI_CHANNEL)
        return False

    tentative = chess.Move.from_uci(start_sq + landing_sq)

    # Promotion: request third phrase only when required.
    if tentative not in board.legal_moves:
        from_sq = chess.parse_square(start_sq)
        to_sq = chess.parse_square(landing_sq)
        piece = board.piece_at(from_sq)

        if piece and piece.piece_type == chess.PAWN:
            dest_rank = chess.square_rank(to_sq)
            if dest_rank in (0, 7):
                print("Promotion cue: anchor – ♭2, then steps 1..4 (r, n, b, q).")
                p3 = collect_structural_phrase_stream(
                    get_msg=listener.get,
                    ctx=ctx,
                    min_structural=2,
                    use_sustain=True,
                )
                promo = decode_promotion_piece(p3)
                if promo:
                    tentative = chess.Move.from_uci(start_sq + landing_sq + promo)

    if tentative in board.legal_moves:
        board.push(tentative)
        print("Last move (you):", tentative.uci())
        return True

    bad = tentative.uci() if tentative else "(none)"
    print(f"Illegal move {bad}; please repeat.")
    earcon_retry(outp, MIDI_CHANNEL)
    return False


def _handle_engine_turn(
    board: chess.Board,
    engine: chess.engine.SimpleEngine,
    outp: mido.ports.BaseOutput,
    ctx: KeyContext,
) -> None:
    """Ask Stockfish for a move, render its phrases, and push the move."""
    mover_is_white = board.turn
    print(f"\nEngine move ({'White' if mover_is_white else 'Black'}) thinking...")

    result = engine.play(board, chess.engine.Limit(time=0.7))
    move = result.move
    print("Engine:", move.uci())

    # Render phrases before pushing (use mover’s color rules).
    sq_from = chess.square_name(move.from_square)
    sq_to = chess.square_name(move.to_square)

    if board.is_castling(move):
        kingside = sq_to in ("g1", "g8")
        degrees = phrase_for_castling(side_white=mover_is_white, kingside=kingside)
        play_degrees(outp, ctx, degrees, MIDI_CHANNEL)
    else:
        play_degrees(outp, ctx, phrase_for_square(sq_from, mover_is_white), MIDI_CHANNEL)
        time.sleep(0.15)
        play_degrees(outp, ctx, phrase_for_square(sq_to, mover_is_white), MIDI_CHANNEL)

        if move.promotion:
            piece_char = {
                chess.QUEEN: "q",
                chess.ROOK: "r",
                chess.BISHOP: "b",
                chess.KNIGHT: "n",
            }[move.promotion]
            time.sleep(0.12)
            play_degrees(outp, ctx, phrase_for_promotion(piece_char, mover_is_white), MIDI_CHANNEL)

    board.push(move)
    print("Last move (engine):", move.uci())


# ----------------------------------- main --------------------------------

def main() -> None:
    # MIDI setup
    in_name = pick_input_port()
    out_name = pick_output_port()
    print(f"MIDI in:  {in_name}")
    print(f"MIDI out: {out_name}")

    ctx = KeyContext(tonic_midi=60, phrase_gap_ms=500)
    _print_help_banner()

    with MidiListener(in_name) as listener, open_output_robust(out_name) as outp:
        engine = chess.engine.SimpleEngine.popen_uci(str(ENGINE_PATH))
        engine.configure({"UCI_LimitStrength": True, "UCI_Elo": 1500})

        board = chess.Board()
        human_is_white = True  # set to False to play Black

        try:
            while not board.is_game_over():
                human_turn = (board.turn and human_is_white) or (
                    (not board.turn) and (not human_is_white)
                )

                if human_turn:
                    moved = _handle_human_turn(board, listener, outp, ctx)
                    if not moved:
                        continue
                else:
                    _handle_engine_turn(board, engine, outp, ctx)

            print("\nResult:", board.result())
            engine.quit()

        except KeyboardInterrupt:
            print("\nInterrupted. Exiting...")
            engine.quit()
