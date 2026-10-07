import csv
from io import BytesIO, StringIO
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER

def matrix_for_form(form):
    headers = ["No.", "Waktu Submit"] + [q.label for q in form.questions]
    rows = []
    for i, response in enumerate(sorted(form.responses, key=lambda r: r.submitted_at or 0), 1):
        mapping = {a.question_id: a.answer for a in response.answers}
        rows.append([i, response.submitted_at.strftime("%d/%m/%Y %H:%M") if response.submitted_at else ""] +
                    [mapping.get(q.id, "") for q in form.questions])
    return headers, rows

def xlsx_bytes(form):
    headers, rows = matrix_for_form(form)
    wb = Workbook()
    ws = wb.active
    ws.title = "Responses"
    ws.append(headers)
    for row in rows:
        ws.append(row)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for col in ws.columns:
        width = min(max(len(str(c.value or "")) for c in col) + 2, 45)
        ws.column_dimensions[col[0].column_letter].width = width
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio.getvalue()

def csv_text(form):
    headers, rows = matrix_for_form(form)
    s = StringIO()
    w = csv.writer(s)
    w.writerow(headers)
    w.writerows(rows)
    return "\ufeff" + s.getvalue()

def pdf_bytes(form):
    headers, rows = matrix_for_form(form)
    bio = BytesIO()
    doc = SimpleDocTemplate(bio, pagesize=landscape(A4), rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    title = Paragraph(form.title, styles["Title"])
    subtitle = Paragraph(f"Rekap respons — {len(rows)} respons", styles["Normal"])
    data = [[Paragraph(str(h), styles["BodyText"]) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(v or ""), styles["BodyText"]) for v in row])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0B1F5E")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("FONTSIZE", (0,0), (-1,-1), 7),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    doc.build([title, Spacer(1, 8), subtitle, Spacer(1, 12), table])
    bio.seek(0)
    return bio.getvalue()
