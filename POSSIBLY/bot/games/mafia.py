from __future__ import annotations
import random
from enum import StrEnum
from typing import Any


class Phase(StrEnum):
    LOBBY = "lobby"
    NIGHT = "night"
    DAY = "day"
    VOTING = "voting"
    ENDED = "ended"


def assign_roles(players: list[int]) -> dict[str, str]:
    n = len(players)
    if n < 4:
        raise ValueError("حداقل ۴ بازیکن")
    mafia_n = max(1, n // 4)
    roles = ["مافیا"] * mafia_n + ["دکتر", "کارآگاه"] + ["شهروند"] * (n - mafia_n - 2)
    roles = roles[:n]
    random.shuffle(roles)
    return {str(p): r for p, r in zip(players, roles)}


def new_state(creator_id: int) -> dict[str, Any]:
    return {
        "phase": Phase.LOBBY.value,
        "creator_id": creator_id,
        "players": [creator_id],
        "roles": {},
        "alive": [],
        "night_actions": {},
        "votes": {},
        "day": 0,
        "last_killed": None,
        "winner": None,
    }


def check_win(state: dict) -> str | None:
    alive = state.get("alive") or []
    roles = state.get("roles") or {}
    mafia = [p for p in alive if roles.get(str(p)) == "مافیا"]
    town = [p for p in alive if roles.get(str(p)) != "مافیا"]
    if not mafia:
        return "شهروندان"
    if len(mafia) >= len(town):
        return "مافیا"
    return None
