from enum import StrEnum
class MafiaPhase(StrEnum):
    LOBBY="lobby"; NIGHT="night"; DAY="day"; VOTING="voting"; EXECUTION="execution"; VICTORY="victory"
ROLES=("mafia","citizen","doctor","detective")
