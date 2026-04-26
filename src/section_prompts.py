from __future__ import annotations

import re
from pathlib import Path

SECTIONS = [
("01", "Executive Summary", "executive-summary"),
("02", "Portfolio Analysis", "portfolio-analysis"),
("03", "App Inventory", "app-inventory"),
("04", "Benchmarking", "benchmarking"),
("05", "AI Transformation", "ai-transformation"),
("06", "Methodology / Modernization Roadmap", "methodology"),
("07", "Cloud & Data Strategy", "cloud-data-strategy"),
("08", "Financials", "financials"),
("09", "Execution Roadmap", "execution-roadmap"),
("10", "Delivery Center Architecture", "delivery-center"),
("11", "Benchmarking Summary", "benchmarking-summary"),
("12", "Partnership Overview", "partnership-overview"),
]

STYLE_GUIDE = """You are generating one ADM report section as HTML fragment only.
- No markdown.
- Analytical consulting tone.
- Never invent financial numbers.
- Use only provided names and supplied numbers.
"""


def _title_from_id(section_id: str) -> str:
    return section_id.replace("-", " ").title()


def discover_sections_from_reference(project_root: Path):
    reference = project_root / "templates" / "reference" / "Cisco_ADM.html"
    if not reference.exists():
        reference = project_root / "templates" / "reference" / "ciscoADM.html"
    
    if not reference.exists():
        return SECTIONS

    html = reference.read_text(encoding="utf-8", errors="ignore")
    # Find all section container IDs
    ids = re.findall(r'id=["\'](section-[^"\']+)["\']', html, flags=re.IGNORECASE)
    unique_ids = []
    for sid in ids:
        clean_id = sid.replace("section-", "")
        if clean_id not in unique_ids:
            unique_ids.append(clean_id)

    if not unique_ids:
        return SECTIONS

    discovered = []
    for i, section_id in enumerate(unique_ids, start=1):
        # Look for a title in the buttons or just capitalize the ID
        btn_match = re.search(rf'data-section-id=["\']{re.escape(section_id)}["\'][^>]*>.*?<span[^>]*>(.*?)</span>', html, flags=re.IGNORECASE | re.DOTALL)
        title = btn_match.group(1).strip() if btn_match else _title_from_id(section_id)
        discovered.append((f"{i:02d}", title, section_id))
    
    return discovered

def build_prompt(project_root, section_name, section_id, client, financial, roadmap, matrix, benchmarks, reference_html=None):
    master = (project_root / "data" / "master_prompt.txt")
    prefix = ""
    if master.exists():
        txt = master.read_text(encoding="utf-8").strip()
        if txt:
            prefix = txt + "\n\n"
    
    ref_part = ""
    if reference_html:
        ref_part = f"\n\nREFERENCE HTML TEMPLATE FOR THIS SECTION:\n{reference_html}\n\nCRITICAL UI INSTRUCTIONS:\n- You MUST preserve all CSS classes (especially Tailwind classes like bg-slate-50, rounded-[2.5rem], etc.).\n- You MUST preserve the exact HTML structure (divs, grids, cards).\n- Only update the text content and numbers within the structure to match the client data below.\n- Ensure the final output is a valid HTML fragment that fits into the template.\n"

    return f"""{prefix}{STYLE_GUIDE}{ref_part}
Section: {section_name} ({section_id})
Client: {client.company_name}, {client.industry}, HQ {client.headquarters}
Financial authoritative values:
- Total annual run cost: {financial.total_current_annual_run_cost:.2f}
- Baseline 5-year run cost: {financial.baseline_5_year_run_cost:.2f}
- Cumulative savings: {financial.cumulative_savings_5yr:.2f}
- Cumulative investment: {financial.cumulative_investment_5yr:.2f}
- ROI: {financial.roi:.4f}
- NPV: {financial.npv:.2f}
Roadmap: {roadmap}
Matrix: {matrix}
Benchmarks: {benchmarks}
Return HTML fragment only for section id '{section_id}'.
"""
