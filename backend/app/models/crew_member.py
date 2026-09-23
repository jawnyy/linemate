from typing import ClassVar
from .enums import CrewStation

class CrewMember:
    registry: ClassVar[list["CrewMember"]] = []

    def __init__(self, id: int, name: str, station: CrewStation):
        self.id = id
        self.name = name
        self.station = station
        CrewMember.registry.append(self)

    @classmethod
    def find_by_id(cls, user_id: int) -> "CrewMember | None":
        for user in cls.registry:
            if user.id == user_id:
                return user
        return None

    def __repr__(self) -> str:
        return f"CrewMember(id={self.id}, name={self.name!r}, station={self.station.value})"