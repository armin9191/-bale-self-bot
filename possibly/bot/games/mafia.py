from dataclasses import dataclass
from enum import StrEnum


class MafiaPhase(StrEnum):
    LOBBY = "lobby"
    NIGHT = "night"
    DAY = "day"
    VOTING = "voting"
    EXECUTION = "execution"
    VICTORY = "victory"


@dataclass
class MafiaRole:
    name: str


ROLES = {
    "mafia": MafiaRole("Mafia"),
    "citizen": MafiaRole("Citizen"),
    "doctor": MafiaRole("Doctor"),
    "detective": MafiaRole("Detective"),
}
