from dataclasses import dataclass


@dataclass
class TicTacToe:
    board: list[str | None]
    player_x: int
    player_o: int
    turn: str = "X"

    @classmethod
    def new(cls, player_x: int, player_o: int):
        return cls(
            board=[None] * 9,
            player_x=player_x,
            player_o=player_o,
        )

    def move(self, position: int) -> bool:
        if position < 0 or position > 8:
            return False

        if self.board[position] is not None:
            return False

        self.board[position] = self.turn
        self.turn = "O" if self.turn == "X" else "X"

        return True

    def winner(self) -> str | None:
        wins = (
            (0, 1, 2),
            (3, 4, 5),
            (6, 7, 8),
            (0, 3, 6),
            (1, 4, 7),
            (2, 5, 8),
            (0, 4, 8),
            (2, 4, 6),
        )

        for a, b, c in wins:
            if (
                self.board[a]
                and self.board[a]
                == self.board[b]
                == self.board[c]
            ):
                return self.board[a]

        if all(self.board):
            return "draw"

        return None
