from __future__ import annotations

import numpy as np
import pandas as pd

from app.models import CrewMember, Ticket

PRIORITY_WEIGHT = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}

OPEN_STATUSES = {"Open", "In-Progress"}


def _tickets_to_frame(tickets: list[Ticket]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": ticket.id,
                "priority": ticket.priority.value,
                "status": ticket.status.value,
                "assignee_id": ticket.assignee_id,
            }
            for ticket in tickets
        ],
        columns=["id", "priority", "status", "assignee_id"],
    )


def _crew_to_frame(crew: list[CrewMember]) -> pd.DataFrame:
    return pd.DataFrame(
        [{"id": member.id, "station": member.station.value} for member in crew],
        columns=["id", "station"],
    )


def compute_station_workload(tickets: list[Ticket], crew: list[CrewMember]) -> dict:
    tickets_df = _tickets_to_frame(tickets)
    crew_df = _crew_to_frame(crew)

    merged = tickets_df.merge(
        crew_df, left_on="assignee_id", right_on="id", suffixes=("_ticket", "_crew")
    )

    open_tickets = merged[merged["status"].isin(OPEN_STATUSES)].copy()
    open_tickets["priority_weight"] = open_tickets["priority"].map(PRIORITY_WEIGHT)

    counts = open_tickets.groupby("station").size()
    load = open_tickets.groupby("station")["priority_weight"].sum()

    stations = load.index.to_numpy()
    load_array = load.to_numpy(dtype=float)

    total_load = float(np.sum(load_array)) if load_array.size else 0.0
    share_pct = (load_array / total_load * 100) if total_load > 0 else np.zeros_like(load_array)
    mean_load = float(np.mean(load_array)) if load_array.size else 0.0
    std_load = float(np.std(load_array)) if load_array.size else 0.0
    overloaded = load_array > (mean_load + std_load)

    station_reports = [
        {
            "station": str(station),
            "open_ticket_count": int(counts[station]),
            "load_score": int(load_array[i]),
            "load_share_pct": float(share_pct[i]),
            "is_overloaded": bool(overloaded[i]),
        }
        for i, station in enumerate(stations)
    ]

    return {
        "stations": station_reports,
        "total_open_tickets": int(len(open_tickets)),
        "mean_load_score": mean_load,
        "std_load_score": std_load,
    }