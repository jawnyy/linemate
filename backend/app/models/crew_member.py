from .enums import CrewStation

class CrewMember:
    def __init__(self, id: int, name: str, station: CrewStation):
        self.id = id
        self.name = name
        self.station = station

    def __repr__(self) -> str:
        return f"CrewMember(id={self.id}, name={self.name!r}, station={self.station.value})"