"""Risk engine: turn a state (and optional district) into a ranked, plain-language
drinking-water risk report.

The valuable, opinionated parts:
- District awareness: if the user names a district that appears in a
  contaminant's affected list, that risk is marked 'in your district' and
  sorted to the top — local specificity beats a state-level average.
- Actionable output: the report names the correct removal method and, crucially,
  warns when boiling will NOT help (a dangerous and widespread misconception for
  arsenic, fluoride, nitrate and uranium).
"""

from __future__ import annotations

from .schemas import (
    SEVERITY_RANK,
    Contaminant,
    RiskItem,
    RiskReport,
    Severity,
    StateProfile,
)

DISCLAIMER = (
    "JalCheck reports area-level groundwater contamination from national "
    "government datasets (Jal Shakti / CGWB). It is a guide, not a test of your "
    "specific tap or borewell — contamination varies street to street. The only "
    "way to be sure is to test your own source at a certified lab. Not medical advice."
)


def _norm(s: str) -> str:
    return "".join(c for c in s.lower().strip() if c.isalnum())


def _limit_text(c: Contaminant) -> str:
    lim = c.permissible_limit
    val = int(lim) if lim == int(lim) else lim
    return f"above the safe limit of {val} {c.unit} ({c.limit_source})"


def build_report(
    profile: StateProfile,
    contaminants: dict[str, Contaminant],
    district: str | None,
) -> RiskReport:
    dnorm = _norm(district) if district else ""
    items: list[RiskItem] = []

    for sc in profile.contaminants:
        ref = contaminants.get(sc.contaminant)
        if ref is None:
            continue
        in_district = bool(
            dnorm and any(dnorm in _norm(d) or _norm(d) in dnorm
                          for d in sc.notable_districts)
        )
        items.append(RiskItem(
            contaminant_id=ref.id,
            name=ref.name,
            severity=sc.severity,
            in_your_district=in_district,
            exceeds_limit_text=_limit_text(ref),
            health_effects=ref.health_effects,
            vulnerable=ref.vulnerable,
            boiling_helps=ref.boiling_helps,
            removal=ref.removal,
            notable_districts=sc.notable_districts,
            affected_habitations=sc.affected_habitations,
            affected_population=sc.affected_population,
            source=sc.source,
        ))

    # Rank: district matches first, then by severity, then by contaminant rank.
    items.sort(key=lambda i: (
        not i.in_your_district,
        -SEVERITY_RANK[i.severity],
        contaminants[i.contaminant_id].severity_rank,
    ))

    overall = (
        max((i.severity for i in items), key=lambda s: SEVERITY_RANK[s])
        if items else Severity.none_reported
    )

    headline, summary = _headline(profile, items, district, overall)
    boiling_warning = _boiling_warning(items)
    recommended = _recommend_filter(items, contaminants)

    return RiskReport(
        state=profile.state,
        district_query=district or None,
        overall_severity=overall,
        headline=headline,
        summary=summary,
        boiling_warning=boiling_warning,
        recommended_filter=recommended,
        risks=items,
        note=profile.note,
        disclaimer=DISCLAIMER,
    )


def _headline(profile, items, district, overall) -> tuple[str, str]:
    where = f"{district.title()}, {profile.state}" if district else profile.state
    if not items:
        return (
            f"No major groundwater contamination on record for {profile.state}",
            "National datasets don't flag a major contaminant here. That's "
            "reassuring, but local sources still vary — testing your own water "
            "is the only certain check.",
        )
    serious = [i for i in items if SEVERITY_RANK[i.severity] >= 3]
    names = ", ".join(i.name for i in (serious or items)[:3])
    if serious:
        return (
            f"{where}: serious contamination reported — {names}",
            f"Groundwater in {profile.state} is flagged for {names.lower()}. "
            "See the health effects and the right way to remove each below.",
        )
    return (
        f"{where}: some contamination reported — {names}",
        f"{profile.state} has reported {names.lower()} in groundwater. "
        "Severity is lower than the worst-hit states, but check the details below.",
    )


def _boiling_warning(items: list[RiskItem]) -> str | None:
    resist = [i for i in items
              if not i.boiling_helps and SEVERITY_RANK[i.severity] >= 2]
    if not resist:
        return None
    names = ", ".join(i.name.split(" (")[0] for i in resist)
    return (
        f"Boiling will NOT make this water safe — it does not remove {names}, "
        "and can even concentrate some of them. You need the right filter, not a stove."
    )


def _recommend_filter(items, contaminants) -> str | None:
    serious = [i for i in items if SEVERITY_RANK[i.severity] >= 2]
    if not serious:
        return None
    # RO covers the broadest set of the dissolved/geogenic contaminants here.
    ro_targets = {"arsenic", "fluoride", "nitrate", "uranium", "salinity", "heavy_metals"}
    if any(i.contaminant_id in ro_targets for i in serious):
        return (
            "A reverse-osmosis (RO) unit removes the dissolved contaminants "
            "flagged here (arsenic, fluoride, nitrate, uranium, salts). For "
            "fluoride-only areas, an activated-alumina filter is a cheaper option."
        )
    if any(i.contaminant_id == "iron" for i in serious):
        return "An aeration + iron-removal filter handles the iron flagged here."
    return None
