import io
import hashlib
from datetime import datetime
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

def generate_pdf_certificate(full_name: str, email: str) -> bytes:
    """
    Generates a high-resolution, vector E-Certificate PDF for TECH X INNOVATION EVENT 2026.
    Matches SDGI Global University Certificate of Participation layout.
    """
    buffer = io.BytesIO()
    
    # Page dimensions (A4 Landscape: 841.89 x 595.27 pt)
    width, height = landscape(A4)
    
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    c.setTitle(f"TECH_X_2026_Certificate_{full_name}")
    
    # ================= 1. BACKGROUND & FRAMES =================
    # Clean light background fill
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.rect(0, 0, width, height, fill=True, stroke=False)
    
    # Outer navy border
    c.setLineWidth(4)
    c.setStrokeColor(colors.HexColor("#0f172a"))
    c.rect(20, 20, width - 40, height - 40)
    
    # Inner blue line
    c.setLineWidth(1.5)
    c.setStrokeColor(colors.HexColor("#1d4ed8"))
    c.rect(27, 27, width - 54, height - 54)
    
    # Gold accent inner frame line
    c.setLineWidth(1)
    c.setStrokeColor(colors.HexColor("#f97316"))
    c.rect(32, 32, width - 64, height - 64)
    
    # Background watermark text
    c.saveState()
    c.setFont("Helvetica-Bold", 65)
    c.setFillColor(colors.HexColor("#f1f5f9"))
    c.drawCentredString(width / 2.0, height / 2.0 - 15, "SDGI GLOBAL UNIVERSITY")
    c.restoreState()
    
    # ================= 2. EMBLEMS / LOGOS =================
    # Left Emblem - SDGI Global University Badge
    c.saveState()
    c.setFillColor(colors.HexColor("#1e3a8a"))
    c.circle(95, height - 95, 34, fill=True, stroke=False)
    c.setLineWidth(2)
    c.setStrokeColor(colors.HexColor("#f97316"))
    c.circle(95, height - 95, 34, fill=False, stroke=True)
    
    c.setFillColor(colors.HexColor("#ffffff"))
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(95, height - 90, "SDGI")
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(95, height - 102, "GHAZIABAD")
    c.restoreState()
    
    # Right Emblem - TECH X INNOVATION Badge
    c.saveState()
    c.setFillColor(colors.HexColor("#0f172a"))
    c.circle(width - 95, height - 95, 34, fill=True, stroke=False)
    c.setLineWidth(2)
    c.setStrokeColor(colors.HexColor("#3b82f6"))
    c.circle(width - 95, height - 95, 34, fill=False, stroke=True)
    
    c.setFillColor(colors.HexColor("#f97316"))
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(width - 95, height - 88, "TECH X")
    c.setFillColor(colors.HexColor("#ffffff"))
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(width - 95, height - 98, "INNOVATION")
    c.drawCentredString(width - 95, height - 107, "2026")
    c.restoreState()

    # ================= 3. UNIVERSITY HEADERS =================
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.HexColor("#1e3a8a"))
    c.drawCentredString(width / 2.0, height - 85, "SDGI GLOBAL UNIVERSITY")
    
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawCentredString(width / 2.0, height - 103, "GHAZIABAD, DELHI-NCR, INDIA")
    
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.HexColor("#d97706"))
    c.drawCentredString(width / 2.0, height - 122, "SCHOOL OF COMPUTER APPLICATIONS")
    
    # Decorative line under header
    c.setLineWidth(1)
    c.setStrokeColor(colors.HexColor("#f97316"))
    c.line(width / 2.0 - 160, height - 135, width / 2.0 + 160, height - 135)
    c.setFillColor(colors.HexColor("#f97316"))
    c.rect(width / 2.0 - 4, height - 137, 8, 4, fill=True, stroke=False)

    # ================= 4. CERTIFICATE TITLE =================
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawCentredString(width / 2.0, height - 175, "CERTIFICATE OF PARTICIPATION")
    
    c.setFont("Helvetica-Bold", 9.5)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawCentredString(width / 2.0, height - 198, "THIS CERTIFICATE IS PROUDLY PRESENTED TO")

    # ================= 5. PARTICIPANT NAME =================
    styles = getSampleStyleSheet()
    name_style = ParagraphStyle(
        'ParticipantNameStyle',
        parent=styles['Normal'],
        fontName='Helvetica-BoldOblique',
        fontSize=26,
        leading=30,
        textColor=colors.HexColor("#1d4ed8"),
        alignment=TA_CENTER
    )
    
    # Enclose name nicely
    display_name = f"&laquo; {full_name.strip()} &raquo;"
    name_p = Paragraph(display_name, name_style)
    w_p, h_p = name_p.wrap(width - 120, 50)
    name_p.drawOn(c, (width - w_p) / 2.0, height - 248)

    # ================= 6. CITATION BODY TEXT =================
    body_style = ParagraphStyle(
        'CertBodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#334155"),
        alignment=TA_CENTER
    )
    
    citation_html = (
        "for active and successful participation in the technical symposium "
        "<b>&ldquo;TECH X INNOVATION - 2026&rdquo;</b><br/>"
        "organized by the <b>School of Computer Applications, SDGI Global University, Ghaziabad</b>."
    )
    body_p = Paragraph(citation_html, body_style)
    wb_p, hb_p = body_p.wrap(width - 160, 60)
    body_p.drawOn(c, (width - wb_p) / 2.0, height - 295)

    # Subtext / Appreciation note
    note_style = ParagraphStyle(
        'CertNoteStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        alignment=TA_CENTER
    )
    note_html = "Their keen interest, innovative thinking, and commendable enthusiasm are highly appreciated."
    note_p = Paragraph(note_html, note_style)
    wn_p, hn_p = note_p.wrap(width - 160, 40)
    note_p.drawOn(c, (width - wn_p) / 2.0, height - 325)

    # ================= 7. SIGNATURES =================
    # Left Signature Line & Details
    left_x = 200
    sig_y = 170
    
    # Signature line
    c.setLineWidth(1)
    c.setStrokeColor(colors.HexColor("#94a3b8"))
    c.line(left_x - 90, sig_y + 15, left_x + 90, sig_y + 15)
    
    # Signature graphic / cursive representation
    c.setFont("Helvetica-BoldOblique", 14)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.drawCentredString(left_x, sig_y + 22, "Vipin Sharma")
    
    c.setFont("Helvetica-Bold", 10.5)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawCentredString(left_x, sig_y - 2, "Vipin Kumar Sharma")
    
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawCentredString(left_x, sig_y - 15, "Event Coordinator")
    c.drawCentredString(left_x, sig_y - 27, "School of Computer Applications")

    # Right Signature Line & Details
    right_x = width - 200
    
    c.line(right_x - 90, sig_y + 15, right_x + 90, sig_y + 15)
    
    c.setFont("Helvetica-BoldOblique", 14)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.drawCentredString(right_x, sig_y + 22, "Dr. S. K. Rathi")
    
    c.setFont("Helvetica-Bold", 10.5)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawCentredString(right_x, sig_y - 2, "Dr. Sudhir Kumar Rathi")
    
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawCentredString(right_x, sig_y - 15, "Head of Department")
    c.drawCentredString(right_x, sig_y - 27, "School of Computer Applications")

    # ================= 8. FOOTER METADATA (LIVE DATE & CERT ID) =================
    issue_date = datetime.now().strftime("%d/%m/%Y")
    
    # Generate unique ID based on email + timestamp
    hash_seed = f"{email}-{datetime.now().timestamp()}".encode('utf-8')
    unique_code = hashlib.md5(hash_seed).hexdigest()[:6].upper()
    cert_id = f"SGU/SCA/TXI-2026/{unique_code}"

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(55, 48, f"Date of Issue: {issue_date}")
    c.drawRightString(width - 55, 48, f"Certificate ID: {cert_id}")

    # Finalize PDF canvas
    c.showPage()
    c.save()
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
