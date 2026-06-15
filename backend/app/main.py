import datetime
import os
from collections import Counter

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from .db import SessionLocal
from .engine import DISCLAIMER, build_report
from .models import ContaminantRow, StateRow
from .schemas import SEVERITY_RANK, RiskReport, Severity, Stats

CORS_ORIGINS = [
    o.strip() for o in os.environ.get(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",") if o.strip()
]


def load_contaminants():
    with SessionLocal() as db:
        return {r.id: r.to_domain() for r in db.scalars(select(ContaminantRow))}


def load_states():
    with SessionLocal() as db:
        return [r.to_domain() for r in db.scalars(select(StateRow).order_by(StateRow.state))]


def create_app() -> FastAPI:
    app = FastAPI(title="JalCheck API", version="1.0.0")
    app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS,
                       allow_methods=["*"], allow_headers=["*"])

    @app.exception_handler(HTTPException)
    async def http_err(request: Request, exc: HTTPException):
        code = {404: "not_found", 422: "validation_error"}.get(exc.status_code, "request_error")
        return JSONResponse(status_code=exc.status_code,
                            content={"error": {"code": code, "message": str(exc.detail)}})

    @app.exception_handler(RequestValidationError)
    async def val_err(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"error": {
            "code": "validation_error", "message": "Invalid request",
            "details": [{"loc": list(e.get("loc", [])), "msg": e.get("msg")} for e in exc.errors()],
        }})

    @app.get("/api/health")
    def health():
        return {"status": "ok", "states": len(load_states())}

    @app.get("/api/states")
    def states():
        out = []
        for p in load_states():
            worst = (
                max((c.severity for c in p.contaminants), key=lambda s: SEVERITY_RANK[s])
                if p.contaminants else Severity.none_reported
            )
            out.append({
                "state": p.state, "state_code": p.state_code,
                "contaminant_count": len(p.contaminants),
                "worst_severity": worst.value,
                "contaminants": [c.contaminant for c in p.contaminants],
            })
        return {"count": len(out), "states": out}

    @app.get("/api/check", response_model=RiskReport)
    def check(
        state: str = Query(min_length=2, max_length=60),
        district: str | None = Query(default=None, max_length=60),
    ):
        profiles = {p.state.lower(): p for p in load_states()}
        codes = {p.state_code.lower(): p for p in load_states()}
        key = state.strip().lower()
        profile = profiles.get(key) or codes.get(key)
        if profile is None:
            raise HTTPException(404, f"State {state!r} not found")
        return build_report(profile, load_contaminants(), district)

    @app.get("/api/contaminants")
    def contaminants():
        return {"contaminants": list(load_contaminants().values())}

    @app.get("/api/stats", response_model=Stats)
    def stats():
        states = load_states()
        contam = [sc for p in states for sc in p.contaminants]
        by = Counter(sc.contaminant for sc in contam)

        def worst_for(cid: str):
            cands = [(p.state, sc.severity) for p in states for sc in p.contaminants
                     if sc.contaminant == cid]
            if not cands:
                return None
            return max(cands, key=lambda x: SEVERITY_RANK[x[1]])[0]

        return Stats(
            states_covered=len(states),
            states_with_contamination=sum(1 for p in states if p.contaminants),
            total_state_contaminant_records=len(contam),
            by_contaminant=dict(by),
            worst_arsenic_state=worst_for("arsenic"),
            worst_fluoride_state=worst_for("fluoride"),
            generated_on=datetime.date.today(),
        )

    @app.get("/api/meta")
    def meta():
        return {"disclaimer": DISCLAIMER}

    return app


app = create_app()
