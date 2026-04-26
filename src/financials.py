from collections import defaultdict
from .models import ClientProfile, FinancialSummary

SAVINGS_RATE = {"Retire": 0.90, "Retain": 0.05, "Rehost": 0.15, "Replatform": 0.30, "Refactor": 0.45, "Rearchitect": 0.60}
SAVINGS_RAMP = {"Y1": 0.10, "Y2": 0.25, "Y3": 0.50, "Y4": 0.75, "Y5": 1.00}
INVESTMENT_DISTRIBUTION = {"Y1": 0.30, "Y2": 0.25, "Y3": 0.20, "Y4": 0.15, "Y5": 0.10}

def compute_financials(client: ClientProfile, discount_rate: float = 0.10) -> FinancialSummary:
    total_current = sum(a.annual_run_cost for a in client.application_inventory)
    baseline_5y = total_current * 5
    full_savings = sum(a.annual_run_cost * SAVINGS_RATE[a.modernization_recommendation] for a in client.application_inventory)
    cumulative_investment = client.annual_adm_spend * 5
    investment_by_year = {y: cumulative_investment * w for y, w in INVESTMENT_DISTRIBUTION.items()}
    savings_by_year = {y: full_savings * ramp for y, ramp in SAVINGS_RAMP.items()}
    offshore_multiplier = max([max(0.0, 1.0 - dc.avg_cost_multiplier) for dc in client.delivery_centers_preferred if dc.type == "offshore"] + [0.0])
    offshore_full = total_current * 0.15 * offshore_multiplier
    offshore_by_year = {y: offshore_full * r for y, r in SAVINGS_RAMP.items()}
    total_savings_by_year = {y: savings_by_year[y] + offshore_by_year[y] for y in SAVINGS_RAMP}
    cumulative_savings = sum(total_savings_by_year.values())
    roi = cumulative_savings / cumulative_investment if cumulative_investment else 0.0
    npv = 0.0
    running_net = 0.0
    payback = None
    for idx, y in enumerate(["Y1", "Y2", "Y3", "Y4", "Y5"], start=1):
        net = total_savings_by_year[y] - investment_by_year[y]
        npv += net / ((1 + discount_rate) ** idx)
        running_net += net
        if payback is None and running_net >= 0:
            payback = idx
    legacy_curve = {y: client.transformation_targets.legacy_cost_reduction_target_percent * r for y, r in SAVINGS_RAMP.items()}
    return FinancialSummary(
        total_current_annual_run_cost=total_current,
        baseline_5_year_run_cost=baseline_5y,
        investment_by_year=investment_by_year,
        savings_by_year=total_savings_by_year,
        offshore_arbitrage_savings_by_year=offshore_by_year,
        cumulative_savings_5yr=cumulative_savings,
        cumulative_investment_5yr=cumulative_investment,
        total_contract_value_5yr=cumulative_investment,
        roi=roi,
        npv=npv,
        payback_period_year=payback,
        legacy_cost_reduction_curve_by_year=legacy_curve,
    )

def build_modernization_matrix(client: ClientProfile) -> list[dict]:
    buckets = defaultdict(list)
    for app in client.application_inventory:
        buckets[app.modernization_recommendation].append(app)
    ordered = ["Retire", "Retain", "Rehost", "Replatform", "Refactor", "Rearchitect"]
    return [{"category": cat, "app_names": [a.app_name for a in buckets.get(cat, [])], "app_count": len(buckets.get(cat, [])), "annual_run_cost_total": sum(a.annual_run_cost for a in buckets.get(cat, []))} for cat in ordered]

def build_execution_roadmap(client: ClientProfile, financial: FinancialSummary) -> list[dict]:
    groups = {"Y1": [], "Y2": [], "Y3": [], "Y4": [], "Y5": []}
    for a in client.application_inventory:
        rec = a.modernization_recommendation
        if rec in {"Retire", "Rehost"}:
            target = "Y1" if a.criticality != "High" else "Y2"
        elif rec in {"Refactor", "Replatform"}:
            target = "Y3" if a.criticality != "High" else "Y4"
        elif rec == "Rearchitect":
            target = "Y5" if a.criticality == "High" else "Y4"
        else:
            target = "Y2"
        groups[target].append(a)
    rows = []
    for y in ["Y1", "Y2", "Y3", "Y4", "Y5"]:
        bucket = groups[y]
        initiatives = sorted({f"{a.modernization_recommendation} wave" for a in bucket}) or ["Stabilization and optimization"]
        rows.append({"year": y, "initiatives": initiatives, "apps_impacted": [a.app_name for a in bucket], "expected_savings": financial.savings_by_year[y], "expected_investment": financial.investment_by_year[y], "key_milestones": [f"Complete {i.lower()}" for i in initiatives]})
    return rows

def build_competitor_benchmarks(client: ClientProfile) -> list[dict]:
    out = []
    for comp in client.competitors:
        score = max(1, min(10, len(comp.gaps_vs_client) * 2 + len(comp.weaknesses)))
        gaps = comp.gaps_vs_client[:3]
        actions = [f"Exploit advantage in {g.lower()}" for g in gaps] or ["Sustain operational differentiation"]
        out.append({"name": comp.name, "gap_score": score, "top_gaps": gaps, "recommended_actions": actions})
    return out

def build_financial_chart_svg(financial: FinancialSummary) -> str:
    years = ["Y1", "Y2", "Y3", "Y4", "Y5"]
    inv = [financial.investment_by_year[y] for y in years]
    sav = [financial.savings_by_year[y] for y in years]
    cum = []
    run = 0.0
    for y in years:
        run += financial.savings_by_year[y] - financial.investment_by_year[y]
        cum.append(run)
    maxv = max(inv + sav + cum + [1.0])
    w, h, pad = 820, 260, 40
    step = (w - 2 * pad) / (len(years) - 1)
    def pts(vals):
        return " ".join(f"{pad+i*step:.1f},{h-pad-(v/maxv)*(h-2*pad):.1f}" for i, v in enumerate(vals))
    labels = "".join(f"<text x='{pad+i*step:.1f}' y='{h-12}' text-anchor='middle' font-size='11'>{y}</text>" for i, y in enumerate(years))
    return f"<svg viewBox='0 0 {w} {h}' width='100%' height='260'><line x1='{pad}' y1='{h-pad}' x2='{w-pad}' y2='{h-pad}' stroke='#bbb'/><polyline fill='none' stroke='#0B5FFF' stroke-width='3' points='{pts(inv)}'/><polyline fill='none' stroke='#00A870' stroke-width='3' points='{pts(sav)}'/><polyline fill='none' stroke='#6F42C1' stroke-width='3' points='{pts(cum)}'/>{labels}</svg>"
