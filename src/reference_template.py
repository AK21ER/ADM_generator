from __future__ import annotations
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _find_container_range(html: str, element_id: str) -> tuple[int, int, int] | None:
    for quote in ['"', "'"]:
        marker = f"id={quote}{element_id}{quote}"
        marker_idx = html.find(marker)
        if marker_idx == -1:
            continue
        open_idx = html.rfind("<div", 0, marker_idx)
        if open_idx == -1:
            continue
        tag_end = html.find(">", marker_idx)
        if tag_end == -1:
            continue
        tag_end += 1
        depth = 1
        pos = tag_end
        while depth > 0:
            next_open = html.find("<div", pos)
            next_close = html.find("</div>", pos)
            if next_close == -1:
                return None
            if next_open != -1 and next_open < next_close:
                depth += 1
                pos = next_open + 4
            else:
                depth -= 1
                pos = next_close + 6
                if depth == 0:
                    return open_idx, tag_end, next_close
    return None


def _extract_inner_content(fragment: str, sid: str) -> str:
    fragment = fragment.strip()
    wrapped = _find_container_range(fragment, f"section-{sid}")
    if wrapped:
        _, inner_start, inner_end = wrapped
        return fragment[inner_start:inner_end].strip()
    return fragment


def render_with_reference(project_root: Path, sections: list[dict]) -> tuple[str | None, list[str]]:
    reference_path = project_root / "templates" / "reference" / "Cisco_ADM.html"
    if not reference_path.exists():
        reference_path = project_root / "templates" / "reference" / "ciscoADM.html"
    if not reference_path.exists():
        logger.error("Reference template not found.")
        return None, []

    # IMPORTANT: keep reference HTML/CSS/JS exactly as-is.
    html = reference_path.read_text(encoding="utf-8", errors="ignore")
    missing_ids: list[str] = []

    for section in sections:
        sid = section["id"]
        target_id = f"section-{sid}"
        container = _find_container_range(html, target_id)
        if not container:
            missing_ids.append(sid)
            continue
        _, inner_start, inner_end = container
        inner = _extract_inner_content(section["html"], sid)
        html = f"{html[:inner_start]}\n{inner}\n{html[inner_end:]}"

    return html, missing_ids


def get_reference_section_html(project_root: Path, sid: str) -> str | None:
    reference_path = project_root / "templates" / "reference" / "Cisco_ADM.html"
    if not reference_path.exists():
        reference_path = project_root / "templates" / "reference" / "ciscoADM.html"
    if not reference_path.exists():
        return None

    html = reference_path.read_text(encoding="utf-8", errors="ignore")
    target_id = f"section-{sid}"
    
    # Use the robust depth-counting algorithm to find the exact inner content
    start_pattern = f'id="{target_id}"'
    start_idx = html.find(start_pattern)
    if start_idx == -1:
        start_pattern = f"id='{target_id}'"
        start_idx = html.find(start_pattern)
        
    if start_idx != -1:
        tag_end = html.find(">", start_idx) + 1
        depth = 1
        search_pos = tag_end
        close_tag_idx = -1
        
        while depth > 0:
            next_open = html.find("<div", search_pos)
            next_close = html.find("</div>", search_pos)
            if next_close == -1: break
            
            if next_open != -1 and next_open < next_close:
                depth += 1
                search_pos = next_open + 4
            else:
                depth -= 1
                if depth == 0:
                    close_tag_idx = next_close
                search_pos = next_close + 6
        
        if close_tag_idx != -1:
            return html[tag_end:close_tag_idx].strip()
            
    return None
