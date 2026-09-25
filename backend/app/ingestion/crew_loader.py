import csv
from pathlib import Path

from app.core.exceptions import CrewLoadError
from app.models import CrewMember, CrewStation


def _row_to_crew(row: dict[str, str]) -> CrewMember:
    try:
        station = CrewStation(row["station"])
    except ValueError as exc:
        raise CrewLoadError(f"row {row.get('id')}: invalid station {row['station']!r}") from exc

    try:
        crew_id = int(row["id"])
    except ValueError as exc:
        raise CrewLoadError(
            f"row {row.get('id')}: id must be an integer."
        ) from exc

    return CrewMember(
        crew_id,
        row["name"],
        station,
    )


def load_crew_from_csv(csv_path: str | Path) -> list[CrewMember]:
    crew_members: list[CrewMember] = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                crew_members.append(_row_to_crew(row))
            except CrewLoadError as exc:
                print(f" SKIPPED {exc}")

    return crew_members