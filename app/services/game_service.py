"""
Herní logika pro piškvorky (tic-tac-toe), 3x3, 1v1.

Board je Python list o 9 prvcích, indexy 0-8:
 0 1 2
 3 4 5
 6 7 8
Hodnoty: "X", "O", nebo None (prázdné).
"""
import json
from typing import List, Optional

WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # řádky
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # sloupce
    (0, 4, 8), (2, 4, 6),             # diagonály
]


def empty_board() -> List[Optional[str]]:
    return [None] * 9


def board_to_json(board: List[Optional[str]]) -> str:
    return json.dumps(board)


def board_from_json(raw: str) -> List[Optional[str]]:
    return json.loads(raw)


def check_winner(board: List[Optional[str]]) -> Optional[str]:
    """Vrátí 'X', 'O', 'draw', nebo None (hra pokračuje)."""
    for a, b, c in WIN_LINES:
        if board[a] is not None and board[a] == board[b] == board[c]:
            return board[a]
    if all(cell is not None for cell in board):
        return "draw"
    return None


def build_turn_order(team1_ids: List[int], team2_ids: List[int]) -> List[int]:
    """Sestaví pořadí tahů pro 2v2: střídání týmů, uvnitř týmu pořadí dle
    připojení. Např. [t1_p1, t2_p1, t1_p2, t2_p2]. Vyhazuje ValueError,
    pokud každý tým nemá přesně 2 hráče (2v2 je pevně dané pro v16)."""
    if len(team1_ids) != 2 or len(team2_ids) != 2:
        raise ValueError("Oba týmy musí mít přesně 2 hráče")
    return [team1_ids[0], team2_ids[0], team1_ids[1], team2_ids[1]]


def next_turn_index(turn_order: List[int], current_index: int) -> int:
    return (current_index + 1) % len(turn_order)


def apply_move(board: List[Optional[str]], position: int, symbol: str) -> List[Optional[str]]:
    """Vrátí nový board po tahu. Vyhazuje ValueError při neplatném tahu."""
    if position < 0 or position > 8:
        raise ValueError("position musí být 0-8")
    if board[position] is not None:
        raise ValueError("Toto pole je už obsazené")
    if symbol not in ("X", "O"):
        raise ValueError("symbol musí být 'X' nebo 'O'")

    new_board = board.copy()
    new_board[position] = symbol
    return new_board
