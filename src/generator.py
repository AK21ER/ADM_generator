import logging
import re
import time
from collections import Counter
from .financials import compute_financials, build_modernization_matrix, build_execution_roadmap, build_competitor_benchmarks, build_financial_chart_svg
from .section_prompts import SECTIONS, build_prompt, discover_sections_from_reference
from .ai_client import AIClient
from .renderer import render_report
from .reference_template import render_with_reference, get_reference_section_html
from .utils import write_text

logger = logging.getLogger(__name__)


def _fmt_money_m(v: float) -> str:
    return f"${v / 1_000_000:.0f}M"


def _fmt_money_b(v: float) -> str:
    return f"${v / 1_000_000_000:.2f}B"


def _personalize_fragment(fragment: str, client, financial) -> str:
    # Keep structure/classes untouched; only replace visible business values.
    out = fragment
    out = re.sub(r"Cisco Systems Inc\.", client.company_name, out, flags=re.IGNORECASE)
    out = re.sub(r"Cisco Systems", client.company_name, out, flags=re.IGNORECASE)
    out = re.sub(r"\bCisco\b", client.company_name, out, flags=re.IGNORECASE)

    primary_industry = client.industry.split(",")[0].strip() if "," in client.industry else client.industry
    out = out.replace("Networking, Security, and CX", client.industry)
    out = out.replace(">Networking<", f">{primary_industry}<")
    out = out.replace("Networking:", f"{primary_industry}:")

    # Deterministic financials from financials.py
    net_value = financial.cumulative_savings_5yr - financial.cumulative_investment_5yr
    replacements = {
        "$450M": _fmt_money_m(financial.cumulative_investment_5yr),
        "$2.25B": _fmt_money_b(financial.cumulative_savings_5yr),
        "$1.5B": _fmt_money_b(net_value),
        "200%": f"{financial.roi * 100:.0f}%",
    }
    for old, new in replacements.items():
        out = out.replace(old, new)

    app_count = len(client.application_inventory)
    if app_count > 0:
        out = re.sub(r"\b950\b(?=\s*Total|\s*Apps|:|\))", str(app_count), out)
    return out


def _personalize_final_html(html: str, client, financial) -> str:
    out = html
    out = re.sub(r"Cisco Systems Inc\.", client.company_name, out, flags=re.IGNORECASE)
    out = re.sub(r"Cisco Systems", client.company_name, out, flags=re.IGNORECASE)
    out = re.sub(r"\bCisco\b", client.company_name, out, flags=re.IGNORECASE)
    out = out.replace("Networking, Security, and CX", client.industry)
    out = out.replace(">Networking<", f">{client.industry}<")
    out = re.sub(r"\$\s*450M\b", _fmt_money_m(financial.cumulative_investment_5yr), out, flags=re.IGNORECASE)
    out = re.sub(r"\$\s*2\.25B\b", _fmt_money_b(financial.cumulative_savings_5yr), out, flags=re.IGNORECASE)
    out = re.sub(r"\$\s*1\.5B\b", _fmt_money_b(financial.cumulative_savings_5yr - financial.cumulative_investment_5yr), out, flags=re.IGNORECASE)
    out = re.sub(r"\b200%\b", f"{financial.roi * 100:.0f}%", out)
    return out


def _inject_offline_dynamic_blocks(html: str, client, financial) -> str:
    out = html

    # Replace known competitor trio language with client competitors.
    competitors = [c.name for c in client.competitors[:3]]
    if competitors:
        if len(competitors) == 1:
            comp_text = competitors[0]
        elif len(competitors) == 2:
            comp_text = f"{competitors[0]} and {competitors[1]}"
        else:
            comp_text = f"{competitors[0]}, {competitors[1]}, and {competitors[2]}"
        out = re.sub(
            r"Arista,\s*Juniper,\s*and\s*Palo Alto Networks",
            comp_text,
            out,
            flags=re.IGNORECASE,
        )

    # Update total app count title.
    out = re.sub(
        r"Portfolio Distribution\s*\(\d+\s+Total\)",
        f"Portfolio Distribution ({len(client.application_inventory)} Total)",
        out,
        flags=re.IGNORECASE,
    )

    # Replace chart tooltip buckets with deterministic criticality distribution.
    crit = Counter(a.criticality for a in client.application_inventory)
    total = max(1, len(client.application_inventory))
    dist_rows = [
        ("High", crit.get("High", 0)),
        ("Medium", crit.get("Medium", 0)),
        ("Low", crit.get("Low", 0)),
    ]
    for label, count in dist_rows:
        pct = (count / total) * 100
        out = re.sub(
            rf'data-tooltip="{label}:[^"]+"',
            f'data-tooltip="{label}: {count} Apps ({pct:.1f}%)"',
            out,
            flags=re.IGNORECASE,
        )

    # Rebuild the deep-dive table rows using top run-cost apps (preserve table shell/classes).
    top_apps = sorted(client.application_inventory, key=lambda a: a.annual_run_cost, reverse=True)[:8]
    rows_html = []
    for app in top_apps:
        if app.age_years >= 10:
            age_cls = "bg-red-50 text-red-600"
        elif app.age_years >= 6:
            age_cls = "bg-amber-50 text-amber-700"
        else:
            age_cls = "bg-emerald-50 text-emerald-700"
        rows_html.append(
            "<tr class=\"hover:bg-slate-50/50 transition-colors\">"
            f"<td class=\"px-8 py-6 font-black text-slate-900\">{app.app_name}</td>"
            f"<td class=\"px-8 py-6 text-slate-500 font-medium\">{app.business_unit_owner}</td>"
            f"<td class=\"px-8 py-6\"><span class=\"px-4 py-1 rounded-full text-xs font-black {age_cls}\">{app.age_years}y</span></td>"
            f"<td class=\"px-8 py-6 text-slate-500\">{', '.join(app.tech_stack[:2])}</td>"
            f"<td class=\"px-8 py-6\"><span class=\"px-4 py-1 rounded-full text-xs font-black bg-blue-50 text-blue-700\">{app.modernization_recommendation}</span></td>"
            f"<td class=\"px-8 py-6 text-right font-black text-slate-900\">${app.annual_run_cost/1_000_000:.1f}M</td>"
            "</tr>"
        )
    if rows_html:
        out = re.sub(
            r"(<tbody class=\"divide-y divide-slate-50\">)(.*?)(</tbody>)",
            r"\1" + "".join(rows_html) + r"\3",
            out,
            count=1,
            flags=re.DOTALL,
        )

    # Replace one commonly static phrase with industry-aware wording.
    out = re.sub(
        r"legacy OS and networking data",
        f"legacy platform and {client.industry.lower()} data",
        out,
        flags=re.IGNORECASE,
    )
    return out


def generate_report(project_root, client, output_file, api_key, model, discount_rate=0.10, force=False):
    out_dir = output_file.parent
    sections_dir = out_dir / "sections"
    prompts_dir = out_dir / "prompts"
    raw_dir = out_dir / "raw_responses"
    for d in [sections_dir, prompts_dir, raw_dir]:
        d.mkdir(parents=True, exist_ok=True)
    financial = compute_financials(client, discount_rate=discount_rate)
    matrix = build_modernization_matrix(client)
    roadmap = build_execution_roadmap(client, financial)
    benchmarks = build_competitor_benchmarks(client)
    chart_svg = build_financial_chart_svg(financial)
    ai = AIClient(api_key=api_key, model=model)
    section_defs = discover_sections_from_reference(project_root)
    if section_defs != SECTIONS:
        logger.info("Using section IDs discovered from Cisco reference (%d sections).", len(section_defs))
    else:
        logger.info("Using default section map (%d sections).", len(section_defs))

    rendered_sections = []
    for idx, name, sid in section_defs:
        ref_html = get_reference_section_html(project_root, sid)
        prompt = build_prompt(project_root, name, sid, client, financial, roadmap, matrix, benchmarks, reference_html=ref_html)
        prompt_path = prompts_dir / f"section_{idx}_prompt.txt"
        raw_path = raw_dir / f"section_{idx}_raw.txt"
        sec_path = sections_dir / f"section_{idx}_{sid}.html"
        write_text(prompt_path, prompt)
        if sec_path.exists() and not force:
            html_fragment = sec_path.read_text(encoding="utf-8")
            logger.info("Skipping section %s (%s), exists", idx, sid)
        else:
            start = time.perf_counter()
            logger.info("Generating section %s (%s)", idx, sid)
            raw = ai.generate_html_fragment(prompt, reference_html=ref_html)
            write_text(raw_path, raw)
            html_fragment = _personalize_fragment(raw, client, financial)
            write_text(sec_path, html_fragment)
            logger.info("Section %s done in %.2fs", idx, time.perf_counter() - start)
        rendered_sections.append({"id": sid, "title": name, "html": html_fragment})
    # Cisco reference-first rendering for UI parity.
    rendered_html, missing_ids = render_with_reference(project_root, rendered_sections)
    if rendered_html is not None:
        rendered_html = _personalize_final_html(rendered_html, client, financial)
        rendered_html = _inject_offline_dynamic_blocks(rendered_html, client, financial)
        if missing_ids:
            logger.warning("Reference template missing containers for: %s. Those sections were skipped or partially injected.", ", ".join(missing_ids))
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(rendered_html, encoding="utf-8")
        logger.info("Rendered final report using Cisco reference template.")
        return output_file

    if missing_ids:
        logger.warning(
            "Reference template missing section containers for IDs: %s. Falling back to base Jinja template.",
            ", ".join(missing_ids),
        )
    else:
        logger.warning("Reference template unavailable. Falling back to base Jinja template.")

    render_report(project_root / "src" / "templates", output_file, client, financial, rendered_sections, matrix, roadmap, benchmarks, chart_svg)
    logger.info("Rendered final report using fallback base template.")
    return output_file
