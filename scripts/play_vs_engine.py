from __future__ import annotations

import os
from pathlib import Path
import sys
import time
from typing import Optional

# Ensure project root importable
sys.path.append(str(Path(__file__).resolve().parents[1]))

import mido
import chess
import chess.engine

from melody.key_ctx import KeyContext
from melody.io_utils import (
    pick_input_port, pick_output_port, open_input_robust, open_output_robust,
    earcon_retry
)
from melody.decode import (
    collect_structural_phrase, decode_white_square, decode_black_square,
    detect_castling_motif, decode_promotion_piece
)
from melody.encode import (
    phrase_for_square, phrase_for_castling, phrase_for_promotion, play_degrees
)

mido.set_backend("mido.backends.rtmidi")


def resolve_engine_path() -> Path:
    """
    Robust Stockfish discovery:
      1) MELODY_STOCKFISH env var (absolute path to exe).
      2) repo/tools/stockfish/stockfish.exe (standard location).
      3) shutil.which('stockfish') on PATH.
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


ENGINE_PATH = resolve_engine_path()
MIDI_CHANNEL = 0  # change if desired


def decode_square_for_side(deg_seq, side_white: bool, landing: bool) -> Optional[str]:
    """Decode a square for the given side; allow short-form only on landing phrases."""
    if side_white:
        return decode_white_square(deg_seq, short_form_ok=landing)
    else:
        return decode_black_square(deg_seq, short_form_ok=landing)


def print_help_banner() -> None:
    print("\n=== How to play (Cantus) ===")
    print("• Phrase boundary: HOLD sustain while playing a phrase, RELEASE to end it.")
    print("• Normal move = TWO phrases:")
    print("    1) Start square   2) Landing square")
    print("  White starts on 1 (tonic). Black (engine) starts on 8 (tonic up an octave).")
    print("  Example (White): e2 = 1→5→2  (C→G→D)")
    print("  Example (Black): e7 = 8→5→7  (C↑→G→B)")
    print("  Landing short-form allowed: 1→file  or  1→file→file  (e.g., d4 = 1→4 or 1→4→4).")
    print("• Edge files:")
    print("  White A-file: 1–7–1–<rank>          |  White H-file: 1–8–<rank>")
    print("  Black H-file: 8–2–8–<rank> (engine) |  Black A-file: 8–1–<rank> (engine)")
    print("• Castling (both colors): anchor – #4 – 5, then a small run:")
    print("  Ascend from 5 ⇒ Kingside   |  Descend from 5 ⇒ Queenside")
    print("• Promotion (both colors): AFTER a pawn lands on last rank, play a third phrase:")
    print("  Cue: anchor – ♭2 (ascending minor second).")
    print("  Identify with tetrachord steps:")
    print("    step 1 = 1 (tonic)        → rook (r)")
    print("    step 2 = ♭2 (degree 2,-1) → knight (n)")
    print("    step 3 = ♭3 (degree 3,-1) → bishop (b)")
    print("    step 4 = ♮3 (degree 3, 0) → queen  (q)")
    print("=============================\n")


def main() -> None:
    # --- MIDI setup ---
    in_name = pick_input_port()
    out_name = pick_output_port()
    print(f"MIDI in:  {in_name}")
    print(f"MIDI out: {out_name}")

    ctx = KeyContext(tonic_midi=60, phrase_gap_ms=500)
    print_help_banner()

    with open_input_robust(in_name) as inp, open_output_robust(out_name) as outp:
        # --- Engine setup ---
        engine = chess.engine.SimpleEngine.popen_uci(str(ENGINE_PATH))
        engine.configure({"UCI_LimitStrength": True, "UCI_Elo": 1500})

        board = chess.Board()
        human_is_white = True  # set False if you want to play Black

        try:
            while not board.is_game_over():
                side_white_to_move = board.turn  # True if White to move

                # -------- HUMAN TURN --------
                if (side_white_to_move and human_is_white) or ((not side_white_to_move) and (not human_is_white)):
                    print(f"\nYour move ({'White' if side_white_to_move else 'Black'}).")

                    # Phrase 1: castling motif or start square
                    p1 = collect_structural_phrase(inp, ctx, min_structural=3, use_sustain=True)
                    castle_side = detect_castling_motif(p1)
                    if castle_side:
                        move = chess.Move.from_uci(
                            "e1g1" if side_white_to_move and castle_side == "kingside"
                            else "e1c1" if side_white_to_move
                            else "e8g8" if castle_side == "kingside" else "e8c8"
                        )
                        if move in board.legal_moves:
                            board.push(move)
                            print("Last move (you):", move.uci())
                        else:
                            print("Illegal castling attempt; please repeat.")
                            earcon_retry(outp, MIDI_CHANNEL)
                            continue
                    else:
                        # Normal move: need two phrases
                        start_sq = decode_square_for_side(p1, side_white_to_move, landing=False)
                        if not start_sq:
                            print("Could not decode start square; please repeat.")
                            earcon_retry(outp, MIDI_CHANNEL)
                            continue

                        p2 = collect_structural_phrase(inp, ctx, min_structural=3, use_sustain=True)
                        landing_sq = decode_square_for_side(p2, side_white_to_move, landing=True)
                        if not landing_sq:
                            print("Could not decode landing square; please repeat.")
                            earcon_retry(outp, MIDI_CHANNEL)
                            continue

                        if start_sq == landing_sq:
                            print(f"Start and landing are identical ({start_sq}). Please repeat.")
                            earcon_retry(outp, MIDI_CHANNEL)
                            continue

                        tentative = chess.Move.from_uci(start_sq + landing_sq)
                        promo_piece = None

                        if tentative not in board.legal_moves:
                            # Promotion check
                            from_s = chess.parse_square(start_sq)
                            to_s   = chess.parse_square(landing_sq)
                            piece = board.piece_at(from_s)
                            if piece and piece.piece_type == chess.PAWN:
                                dest_rank = chess.square_rank(to_s)
                                if dest_rank in (0, 7):
                                    print("Promotion cue: anchor – ♭2, then climb steps 1..4 (r,n,b,q).")
                                    p3 = collect_structural_phrase(inp, ctx, min_structural=2, use_sustain=True)
                                    promo_piece = decode_promotion_piece(p3)
                                    if promo_piece:
                                        tentative = chess.Move.from_uci(start_sq + landing_sq + promo_piece)

                        if tentative in board.legal_moves:
                            board.push(tentative)
                            print("Last move (you):", tentative.uci())
                        else:
                            print(f"Illegal move {tentative.uci() if tentative else '(none)'}; please repeat.")
                            earcon_retry(outp, MIDI_CHANNEL)
                            continue

                # -------- ENGINE TURN --------
                else:
                    side_white_engine = side_white_to_move  # engine is the side to move now
                    print(f"\nEngine move ({'White' if side_white_engine else 'Black'}) thinking...")
                    res = engine.play(board, chess.engine.Limit(time=0.7))
                    move = res.move
                    print("Engine:", move.uci())

                    # Render phrases BEFORE pushing (so we use the mover's color)
                    sq_from = chess.square_name(move.from_square)
                    sq_to   = chess.square_name(move.to_square)

                    if board.is_castling(move):
                        kingside = (sq_to in ("g1", "g8"))
                        play_degrees(outp, ctx, phrase_for_castling(side_white_engine, kingside), MIDI_CHANNEL)
                    else:
                        play_degrees(outp, ctx, phrase_for_square(sq_from, side_white_engine), MIDI_CHANNEL)
                        time.sleep(0.15)
                        play_degrees(outp, ctx, phrase_for_square(sq_to,   side_white_engine), MIDI_CHANNEL)

                        if move.promotion:
                            piece_char = {
                                chess.QUEEN:  "q",
                                chess.ROOK:   "r",
                                chess.BISHOP: "b",
                                chess.KNIGHT: "n"
                            }[move.promotion]
                            time.sleep(0.12)
                            play_degrees(outp, ctx, phrase_for_promotion(piece_char, side_white_engine), MIDI_CHANNEL)

                    board.push(move)
                    print("Last move (engine):", move.uci())

            print("\nResult:", board.result())
            engine.quit()

        except KeyboardInterrupt:
            print("\nInterrupted. Exiting...")
            engine.quit()


if __name__ == "__main__":
    main()
