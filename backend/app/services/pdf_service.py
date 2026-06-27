"""诊断报告 PDF 生成服务."""

import logging
from io import BytesIO
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# 严重度 → 颜色
SEVERITY_COLORS = {
    "critical": "#C0392B",
    "warning": "#D97706",
    "info": "#0ea5e9",
}


def _para(text: str, style) -> "Paragraph":
    from reportlab.platypus import Paragraph
    return Paragraph((text or "-").replace("\n", "<br/>"), style)


def generate_diagnosis_report_pdf(report: Dict[str, Any]) -> bytes:
    """生成诊断报告 PDF 字节流."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
        from reportlab.lib.enums import TA_LEFT
    except ImportError as e:
        logger.error("reportlab 未安装，无法生成 PDF")
        raise RuntimeError("reportlab 未安装，请在 Docker 环境或安装依赖后使用") from e

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
        title=f"诊断报告 #{report.get('report_id', '-')}",
        author="PVOps 光伏运维智能体",
    )

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal_style = styles["BodyText"]
    normal_style.wordWrap = "CJK"
    small_style = ParagraphStyle(
        "small", parent=normal_style, fontSize=9, textColor=colors.grey, alignment=TA_LEFT
    )

    story: List[Any] = []
    story.append(Paragraph(report.get("title", "光伏运维智能体 - 诊断报告"), title_style))
    story.append(Spacer(1, 0.5 * cm))

    # 元信息表
    meta = [
        ["电站", report.get("station_name", "-")],
        ["报告 ID", f"#{report.get('report_id', '-')}"],
        ["诊断时间", report.get("diagnosis_time", "-")],
        ["报告生成", report.get("created_at", "-")],
        ["总体健康度", report.get("overall_health", "-")],
        ["结论摘要", report.get("summary", "-")],
    ]
    table = Table(meta, colWidths=[4 * cm, 11 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.6 * cm))

    findings = report.get("findings") or []
    if findings:
        story.append(Paragraph(f"异常项（共 {len(findings)} 条）", heading_style))
        story.append(Spacer(1, 0.3 * cm))
        for idx, item in enumerate(findings, 1):
            sev = item.get("severity", "info")
            sev_color = SEVERITY_COLORS.get(sev, "#475569")
            sev_label = {"critical": "严重", "warning": "警告", "info": "信息"}.get(sev, sev)
            title_html = (
                f'<font color="{sev_color}"><b>[{sev_label}]</b></font> '
                f'{item.get("title", "未命名")}'
            )
            story.append(_para(title_html, styles["Heading3"]))
            if item.get("category"):
                story.append(_para(f"分类：{item['category']}", small_style))
            story.append(_para(f"<b>证据：</b>{item.get('evidence', '-')}", normal_style))
            story.append(_para(f"<b>根因：</b>{item.get('root_cause', '-')}", normal_style))
            story.append(_para(f"<b>建议：</b>{item.get('suggestion', '-')}", normal_style))
            story.append(Spacer(1, 0.4 * cm))
    else:
        story.append(_para("本次诊断未发现异常项，系统运行健康。", normal_style))

    # 页脚
    def _on_page(canvas, doc_) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(
            2 * cm,
            1.5 * cm,
            f"PVOps · 光伏运维智能体 · {report.get('created_at', '')}",
        )
        canvas.drawRightString(
            A4[0] - 2 * cm,
            1.5 * cm,
            f"第 {doc_.page} 页",
        )
        canvas.restoreState()

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_operation_report_pdf(report: Dict[str, Any]) -> bytes:
    """生成运维报告（日报/周报/月报）PDF 字节流."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as e:
        logger.error("reportlab 未安装，无法生成 PDF")
        raise RuntimeError("reportlab 未安装，请在 Docker 环境或安装依赖后使用") from e

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal_style = styles["BodyText"]
    normal_style.wordWrap = "CJK"

    story = []
    story.append(Paragraph(f"光伏运维智能体 - {report.get('title', '运维报告')}", title_style))
    story.append(Spacer(1, 0.5 * cm))

    meta = [
        ["报告类型", report.get("report_type", "-")],
        ["统计周期", f"{report.get('start_date', '-')} 至 {report.get('end_date', '-')}"],
        ["生成人", report.get("created_by", "-")],
        ["总发电量", f"{report.get('total_energy_kwh', 0):.2f} kWh"],
        ["平均 PR", f"{(report.get('avg_pr') or 0) * 100:.1f}%"],
        ["告警数", str(report.get("alarm_count", 0))],
        ["总结", report.get("summary", "-")],
    ]
    table = Table(meta, colWidths=[4 * cm, 10 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.8 * cm))

    details = report.get("details") or []
    if details:
        story.append(Paragraph("每日明细", heading_style))
        story.append(Spacer(1, 0.3 * cm))
        data = [["日期", "日发电量 (kWh)", "平均功率 (kW)"]]
        for item in details:
            data.append([
                item.get("date", "-"),
                f"{item.get('daily_energy_kwh', 0):.2f}",
                f"{item.get('avg_power_kw', 0):.2f}",
            ])
        detail_table = Table(data, colWidths=[5 * cm, 5 * cm, 5 * cm])
        detail_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(detail_table)

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
