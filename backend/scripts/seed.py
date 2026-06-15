"""Validate the datasets and load them into the database.

    python -m scripts.seed
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.exc import OperationalError  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.models import ContaminantRow, StateRow  # noqa: E402
from app.schemas import Contaminant, StateProfile  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "data"


def load_contaminants() -> list[Contaminant]:
    raw = json.loads((DATA / "contaminants.json").read_text())
    return [Contaminant.model_validate(r) for r in raw]


def load_states() -> list[StateProfile]:
    raw = json.loads((DATA / "state_water_quality.json").read_text())
    return [StateProfile.model_validate(r) for r in raw]


def validate() -> tuple[list[Contaminant], list[StateProfile]]:
    contaminants = load_contaminants()
    states = load_states()
    known = {c.id for c in contaminants}
    for s in states:
        for sc in s.contaminants:
            if sc.contaminant not in known:
                raise ValueError(
                    f"{s.state}: unknown contaminant {sc.contaminant!r}"
                )
    return contaminants, states


def wait_for_db(retries: int = 30, delay: float = 1.0) -> None:
    for attempt in range(retries):
        try:
            with engine.connect():
                return
        except OperationalError:
            if attempt == retries - 1:
                raise
            time.sleep(delay)


def seed() -> int:
    contaminants, states = validate()
    wait_for_db()
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        db.query(ContaminantRow).delete()
        db.query(StateRow).delete()
        for c in contaminants:
            db.add(ContaminantRow.from_domain(c))
        for s in states:
            db.add(StateRow.from_domain(s))
        db.commit()
    print(f"seeded {len(contaminants)} contaminants, {len(states)} states")
    return 0


if __name__ == "__main__":
    raise SystemExit(seed())
