from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class TicTacToe:
    board: list[Optional[str]]
    x: int
    o: int
    turn: str = "X"

    @classmethod
    def new(cls, x: int, o: int = 0) -> "TicTacToe":
        return cls([None] * 9, x, o)

    def move(self, pos: int) -> bool:
        if not 0 <= pos < 9 or self.board[pos] is not None:
            return False
        self.board[pos] = self.turn
        self.turn = "O" if self.turn == "X" else "X"
        return True

    def winner(self) -> Optional[str]:
        for a, b, c in ((0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)):
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a]
        return "draw" if all(self.board) else None

    def board_text(self) -> str:
        rows = []
        for r in range(3):
            cells = [self.board[r * 3 + c] or "·" for c in range(3)]
            rows.append(" | ".join(cells))
        return "\n".join(rows)
