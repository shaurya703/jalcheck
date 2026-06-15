from pathlib import Path

import pytest

from app.engine import build_report
from app.schemas import SEVERITY_RANK, Contaminant, Severity, StateProfile
from scripts.seed import load_contaminants, load_states, validate

DATA = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def contaminants() -> dict[str, Contaminant]:
    return {c.id: c for c in load_contaminants()}


@pytest.fixture(scope="module")
def states() -> dict[str, StateProfile]:
    return {p.state: p for p in load_states()}


class TestDataset:
    def test_validates(self):
        contaminants, states = validate()
        assert len(contaminants) == 7
        assert len(states) >= 25

    def test_every_state_contaminant_is_known(self, contaminants, states):
        for p in states.values():
            for sc in p.contaminants:
                assert sc.contaminant in contaminants

    def test_real_arsenic_numbers_present(self, states):
        wb = next(c for c in states["West Bengal"].contaminants if c.contaminant == "arsenic")
        assert wb.affected_habitations == 10846  # real IMIS figure
        assert wb.severity == Severity.severe


class TestEngine:
    def test_rajasthan_fluoride_is_severe(self, states, contaminants):
        r = build_report(states["Rajasthan"], contaminants, None)
        assert r.overall_severity == Severity.severe
        top = r.risks[0]
        assert top.contaminant_id == "fluoride"

    def test_district_match_floats_to_top_and_flags(self, states, contaminants):
        # Nalgonda is the classic fluoride district in Telangana
        r = build_report(states["Telangana"], contaminants, "Nalgonda")
        assert r.risks[0].contaminant_id == "fluoride"
        assert r.risks[0].in_your_district is True

    def test_unknown_district_does_not_flag(self, states, contaminants):
        r = build_report(states["Telangana"], contaminants, "Notarealplace")
        assert all(not i.in_your_district for i in r.risks)

    def test_boiling_warning_present_for_geogenic_contaminants(self, states, contaminants):
        r = build_report(states["West Bengal"], contaminants, None)
        assert r.boiling_warning is not None
        assert "not" in r.boiling_warning.lower()
        assert "arsenic" in r.boiling_warning.lower()

    def test_ro_recommended_for_dissolved_contaminants(self, states, contaminants):
        r = build_report(states["Punjab"], contaminants, None)
        assert r.recommended_filter and "RO" in r.recommended_filter

    def test_clean_state_has_no_risks_but_hedges(self, states, contaminants):
        r = build_report(states["Goa"], contaminants, None)
        assert r.risks == []
        assert r.overall_severity == Severity.none_reported
        assert "testing your own water" in r.summary.lower()
        assert r.note  # the dataset note is surfaced

    def test_ranking_orders_by_severity(self, states, contaminants):
        r = build_report(states["Bihar"], contaminants, None)
        ranks = [SEVERITY_RANK[i.severity] for i in r.risks]
        assert ranks == sorted(ranks, reverse=True)

    def test_every_report_carries_disclaimer(self, states, contaminants):
        r = build_report(states["Karnataka"], contaminants, None)
        assert "not a test of your specific" in r.disclaimer.lower()
