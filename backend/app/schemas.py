"""Domain models for JalCheck."""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    severe = "severe"
    high = "high"
    moderate = "moderate"
    localized = "localized"
    none_reported = "none_reported"


SEVERITY_RANK = {
    Severity.severe: 4,
    Severity.high: 3,
    Severity.moderate: 2,
    Severity.localized: 1,
    Severity.none_reported: 0,
}


class Contaminant(BaseModel):
    id: str
    name: str
    unit: str
    acceptable_limit: float
    permissible_limit: float
    limit_source: str
    type: str                       # geogenic | anthropogenic
    health_effects: str
    vulnerable: list[str]
    boiling_helps: bool
    removal: str
    severity_rank: int


class StateContaminant(BaseModel):
    contaminant: str
    severity: Severity
    affected_habitations: Optional[int] = None
    affected_population: Optional[int] = None
    notable_districts: list[str] = Field(default_factory=list)
    source: str


class StateProfile(BaseModel):
    state: str
    state_code: str
    contaminants: list[StateContaminant] = Field(default_factory=list)
    note: Optional[str] = None


class RiskItem(BaseModel):
    contaminant_id: str
    name: str
    severity: Severity
    in_your_district: bool          # the district you named appears in the affected list
    exceeds_limit_text: str         # "above 1.5 mg/L (IS 10500)"
    health_effects: str
    vulnerable: list[str]
    boiling_helps: bool
    removal: str
    notable_districts: list[str]
    affected_habitations: Optional[int]
    affected_population: Optional[int]
    source: str


class RiskReport(BaseModel):
    state: str
    district_query: Optional[str]
    overall_severity: Severity
    headline: str
    summary: str
    boiling_warning: Optional[str]  # set when a serious contaminant resists boiling
    recommended_filter: Optional[str]
    risks: list[RiskItem]
    note: Optional[str] = None
    disclaimer: str


class Stats(BaseModel):
    states_covered: int
    states_with_contamination: int
    total_state_contaminant_records: int
    by_contaminant: dict[str, int]
    worst_arsenic_state: Optional[str]
    worst_fluoride_state: Optional[str]
    generated_on: datetime.date
