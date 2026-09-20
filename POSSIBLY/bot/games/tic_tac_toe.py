"""Tic-Tac-Toe pure game engine (no Bale dependency)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TicTacToe:
    board: list[Optional[str]]
    x: int
    o: int
    turn: str = "X"

    @classmethod
    def new(cls, x: int, o: int = 0) -> "TicTacToe":
        return cls(board=[None] * 9, x=x, o=o)

    def move(self, pos: int) -> bool:
        if not 0 <= pos < 9 or self.board[pos] is not None:
            return False
        self.board[pos] = self.turn
        self.turn = "O" if self.turn == "X" else "X"
        return True

    def winner(self) -> Optional[str]:
        lines = (
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6),
        )
        for a, b, c in lines:
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a]
        if all(self.board):
            return "draw"
        return None

    def to_dict(self) -> dict:
        return {"board": self.board, "x": self.x, "o": self.o, "turn": self.turn}

    @classmethod
    def from_dict(cls, d: dict) -> "TicTacToe":
        return cls(board=d["board"], x=d["x"], o=d["o"], turn=d.get("turn", "X"))
