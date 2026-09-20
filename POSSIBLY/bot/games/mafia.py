"""Mafia game engine skeleton — state machine stored as JSON-serializable dict."""
from __future__ import annotations

from enum import StrEnum
from typing import Any
import random


class MafiaPhase(StrEnum):
    LOBBY = "lobby"
    NIGHT = "night"
    DAY = "day"
    VOTING = "voting"
    ENDED = "ended"


ROLES = ("mafia", "citizen", "doctor", "detective")


def assign_roles(player_ids: list[int]) -> dict[int, str]:
    n = len(player_ids)
    if n < 4:
        raise ValueError("حداقل ۴ بازیکن لازم است")
    mafia_count = max(1, n // 4)
    roles = ["mafia"] * mafia_count + ["doctor", "detective"] + ["citizen"] * (n - mafia_count - 2)
    roles = roles[:n]
    random.shuffle(roles)
    return dict(zip(player_ids, roles))


def new_mafia_state(creator_id: int) -> dict[str, Any]:
    return {
        "phase": MafiaPhase.LOBBY.value,
        "creator_id": creator_id,
        "players": [],
        "roles": {},
        "alive": [],
        "night_actions": {},
        "votes": {},
        "day": 0,
    }
