"""Export service — 导出与审计。

支持按时间范围筛选，输出 JSON / CSV / PDF 三种格式。
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

from apps.api.vinaya_api.repository import get_review, list_reports
from apps.api.vinaya_api.schemas import RequestReportResponse, ReviewResponse


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str)
    except ValueError:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None
    # Ensure timezone-aware (UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _get_report_time(report: RequestReportResponse) -> datetime | None:
    """Try to extract a timestamp from the report."""
    req = report.report.get("request", {})
    ts = req.get("created_at") or req.get("createdAt")
    if ts:
        dt = _parse_date(ts)
        if dt:
            return dt
    # Fallback: try gradualRelease reviewAt
    gr = report.report.get("gradualRelease", {})
    trial = gr.get("trialPlan", {})
    if trial and trial.get("reviewAt"):
        dt = _parse_date(trial["reviewAt"])
        if dt:
            return dt
    return None


def _to_naive(dt: datetime) -> datetime:
    """Strip timezone info for safe comparison."""
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def _filter_reports(
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[tuple[RequestReportResponse, ReviewResponse | None]]:
    reports = list_reports()
    from_dt = _parse_date(date_from)
    to_dt = _parse_date(date_to)

    results: list[tuple[RequestReportResponse, ReviewResponse | None]] = []
    for report in reports:
        if from_dt or to_dt:
            report_time = _get_report_time(report)
            if report_time:
                rt = _to_naive(report_time)
                if from_dt and rt < _to_naive(from_dt):
                    continue
                if to_dt and rt > _to_naive(to_dt).replace(hour=23, minute=59, second=59):
                    continue
        review = get_review(report.request_id)
        results.append((report, review))
    return results


def export_json(date_from: str | None = None, date_to: str | None = None) -> bytes:
    items = _filter_reports(date_from, date_to)
    records = []
    for report, review in items:
        req = report.report.get("request", {})
        record = {
            "request_id": report.request_id,
            "title": req.get("title", ""),
            "domain": req.get("domain", ""),
            "risk_level": req.get("riskLevel", ""),
            "submitter": req.get("submitter", "anonymous"),
            "decision": report.report.get("decision", ""),
            "reasoning": report.report.get("reasoningSummary", ""),
            "hard_block": report.report.get("precepts", {}).get("hardBlock", False),
            "human_review_required": report.report.get("precepts", {}).get("humanReviewRequired", False),
        }
        if review:
            record["reviewer"] = review.reviewer
            record["review_result"] = review.result
            record["review_comment"] = review.comment
            record["review_time"] = review.created_at
        else:
            record["reviewer"] = None
            record["review_result"] = None
            record["review_comment"] = None
            record["review_time"] = None
        records.append(record)

    return json.dumps(records, ensure_ascii=False, indent=2).encode("utf-8")


def export_csv(date_from: str | None = None, date_to: str | None = None) -> bytes:
    items = _filter_reports(date_from, date_to)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "request_id", "title", "domain", "risk_level", "submitter",
        "decision", "reasoning", "hard_block", "human_review_required",
        "reviewer", "review_result", "review_comment", "review_time",
    ])
    for report, review in items:
        req = report.report.get("request", {})
        writer.writerow([
            report.request_id,
            req.get("title", ""),
            req.get("domain", ""),
            req.get("riskLevel", ""),
            req.get("submitter", "anonymous"),
            report.report.get("decision", ""),
            report.report.get("reasoningSummary", ""),
            report.report.get("precepts", {}).get("hardBlock", False),
            report.report.get("precepts", {}).get("humanReviewRequired", False),
            review.reviewer if review else "",
            review.result if review else "",
            review.comment if review else "",
            review.created_at if review else "",
        ])
    return output.getvalue().encode("utf-8-sig")


def export_pdf(date_from: str | None = None, date_to: str | None = None) -> bytes:
    from fpdf import FPDF

    items = _filter_reports(date_from, date_to)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Use built-in Helvetica (no CJK support needed for PDF header structure),
    # but we add a Unicode font for Chinese text
    font_path = _find_cjk_font()
    if font_path:
        pdf.add_font("CJK", "", font_path, uni=True)
        font_name = "CJK"
    else:
        font_name = "Helvetica"

    # ── Cover page ──
    pdf.add_page()
    pdf.set_font(font_name, size=20)
    pdf.cell(0, 20, "Vinaya Audit Report", ln=True, align="C")
    pdf.set_font(font_name, size=12)
    range_str = ""
    if date_from:
        range_str += f"From: {date_from}  "
    if date_to:
        range_str += f"To: {date_to}"
    if not range_str:
        range_str = "All records"
    pdf.cell(0, 10, range_str, ln=True, align="C")
    pdf.cell(0, 10, f"Total: {len(items)} records", ln=True, align="C")
    pdf.ln(10)

    # ── Summary statistics ──
    decisions = {"allow": 0, "defer": 0, "stop": 0}
    risks = {"low": 0, "medium": 0, "high": 0}
    for report, _ in items:
        d = report.report.get("decision", "defer")
        if d in decisions:
            decisions[d] += 1
        r = report.report.get("request", {}).get("riskLevel", "medium")
        if r in risks:
            risks[r] += 1

    pdf.set_font(font_name, size=14)
    pdf.cell(0, 10, "Summary", ln=True)
    pdf.set_font(font_name, size=11)
    pdf.cell(0, 8, f"  Allow: {decisions['allow']}  |  Defer: {decisions['defer']}  |  Stop: {decisions['stop']}", ln=True)
    pdf.cell(0, 8, f"  Low Risk: {risks['low']}  |  Medium Risk: {risks['medium']}  |  High Risk: {risks['high']}", ln=True)
    pdf.ln(10)

    # ── Detail records ──
    for idx, (report, review) in enumerate(items, 1):
        req = report.report.get("request", {})
        pdf.set_font(font_name, size=12)
        pdf.cell(0, 8, f"#{idx}  {report.request_id}", ln=True)
        pdf.set_font(font_name, size=10)
        pdf.cell(0, 6, f"  Title: {req.get('title', '')}", ln=True)
        pdf.cell(0, 6, f"  Domain: {req.get('domain', '')}  |  Risk: {req.get('riskLevel', '')}  |  Submitter: {req.get('submitter', 'anonymous')}", ln=True)
        pdf.cell(0, 6, f"  Decision: {report.report.get('decision', '')}  |  Hard Block: {report.report.get('precepts', {}).get('hardBlock', False)}", ln=True)

        reasoning = report.report.get("reasoningSummary", "")
        if reasoning:
            pdf.multi_cell(0, 6, f"  Reasoning: {reasoning}")

        if review:
            pdf.cell(0, 6, f"  Reviewer: {review.reviewer}  |  Result: {review.result}", ln=True)
            if review.comment:
                pdf.multi_cell(0, 6, f"  Comment: {review.comment}")

        pdf.ln(4)

    return bytes(pdf.output())


def _find_cjk_font() -> str | None:
    """Try to find a system CJK font for PDF rendering."""
    import platform
    from pathlib import Path

    system = platform.system()
    candidates: list[str] = []

    if system == "Windows":
        windir = Path("C:/Windows/Fonts")
        candidates = [
            str(windir / "msyh.ttc"),     # Microsoft YaHei
            str(windir / "simsun.ttc"),    # SimSun
            str(windir / "simhei.ttf"),    # SimHei
        ]
    elif system == "Darwin":
        candidates = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        ]

    for path in candidates:
        if Path(path).exists():
            return path
    return None
