from sqlalchemy import JSON, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base
from .schemas import Contaminant, StateProfile


class StateRow(Base):
    __tablename__ = "states"

    state_code: Mapped[str] = mapped_column(String(4), primary_key=True)
    state: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    contaminants: Mapped[list] = mapped_column(JSON, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    def to_domain(self) -> StateProfile:
        return StateProfile.model_validate({
            "state": self.state, "state_code": self.state_code,
            "contaminants": self.contaminants, "note": self.note,
        })

    @classmethod
    def from_domain(cls, p: StateProfile) -> "StateRow":
        return cls(
            state_code=p.state_code, state=p.state, note=p.note,
            contaminants=[c.model_dump() for c in p.contaminants],
        )


class ContaminantRow(Base):
    __tablename__ = "contaminants"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    unit: Mapped[str] = mapped_column(String(10), nullable=False)
    acceptable_limit: Mapped[float] = mapped_column(Float, nullable=False)
    permissible_limit: Mapped[float] = mapped_column(Float, nullable=False)
    limit_source: Mapped[str] = mapped_column(String(80), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    health_effects: Mapped[str] = mapped_column(Text, nullable=False)
    vulnerable: Mapped[list] = mapped_column(JSON, nullable=False)
    boiling_helps: Mapped[bool] = mapped_column(nullable=False)
    removal: Mapped[str] = mapped_column(Text, nullable=False)
    severity_rank: Mapped[int] = mapped_column(Integer, nullable=False)

    def to_domain(self) -> Contaminant:
        return Contaminant.model_validate(
            {c.name: getattr(self, c.name) for c in self.__table__.columns}
        )

    @classmethod
    def from_domain(cls, c: Contaminant) -> "ContaminantRow":
        return cls(**c.model_dump())
