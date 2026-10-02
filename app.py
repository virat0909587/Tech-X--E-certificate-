"""
TECH X INNOVATION EVENT 2026 - E-Certificate Automation
Single-file FastAPI application with embedded frontend and SQLite database.
"""

import re
import sqlite3
import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

# PDF generation with reportlab
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# =========================================================
# LOGGING
# =========================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cert_app")

# =========================================================
# DATABASE SETUP (SQLite)
# =========================================================
DB_PATH = Path(__file__).resolve().parent / "certificates.db"

def init_db():
    """Create participants table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            certificate_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialised at %s", DB_PATH)

def save_participant(full_name: str, email: str, certificate_id: str):
    """Insert a new participant record."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO participants (full_name, email, certificate_id) VALUES (?, ?, ?)",
            (full_name, email, certificate_id)
        )
        conn.commit()
        logger.info("Saved participant: %s (%s) [%s]", full_name, email, certificate_id)
    except sqlite3.IntegrityError:
        logger.warning("Certificate ID already exists: %s", certificate_id)
    finally:
        conn.close()

# =========================================================
# PDF CERTIFICATE GENERATION
# =========================================================
def generate_pdf_certificate(full_name: str, email: str) -> bytes:
    """
    Generate a simple PDF certificate using reportlab.
    Returns the PDF as bytes.
    """
    from io import BytesIO

    buffer = BytesIO()
    # Landscape A4
    page_width, page_height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    # Background gradient (simulated with rectangles)
    c.setFillColor(colors.HexColor("#f7faff"))
    c.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    # Border
    c.setStrokeColor(colors.HexColor("#1d4ed8"))
    c.setLineWidth(8)
    c.rect(30, 30, page_width - 60, page_height - 60, fill=0, stroke=1)

    c.setStrokeColor(colors.HexColor("#f97316"))
    c.setLineWidth(3)
    c.rect(45, 45, page_width - 90, page_height - 90, fill=0, stroke=1)

    # Title
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(page_width / 2, page_height - 110, "CERTIFICATE")

    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.HexColor("#1d4ed8"))
    c.drawCentredString(page_width / 2, page_height - 155, "OF PARTICIPATION")

    # Subtitle
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawCentredString(page_width / 2, page_height - 195, "This is proudly presented to")

    # Name
    c.setFont("Helvetica-Bold", 34)
    c.setFillColor(colors.HexColor("#0b1220"))
    c.drawCentredString(page_width / 2, page_height - 260, full_name)

    # Line under name
    c.setStrokeColor(colors.HexColor("#f97316"))
    c.setLineWidth(2)
    c.line(page_width / 2 - 200, page_height - 275, page_width / 2 + 200, page_height - 275)

    # Event
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.HexColor("#1d4ed8"))
    c.drawCentredString(page_width / 2, page_height - 320, "TECH X INNOVATION EVENT 2026")

    # Description
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawCentredString(page_width / 2, page_height - 360, "For active participation and successful completion of the event.")

    # Email
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawCentredString(page_width / 2, page_height - 400, f"Participant Email: {email}")

    # Date and Certificate ID
    cert_id = str(uuid.uuid4())[:8].upper()
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(80, 80, f"Date: {datetime.now().strftime('%d %B %Y')}")
    c.drawString(80, 65, f"Certificate ID: {cert_id}")

    # Signature line
    c.setStrokeColor(colors.HexColor("#1d4ed8"))
    c.setLineWidth(1.5)
    c.line(page_width - 250, 100, page_width - 80, 100)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawCentredString(page_width - 165, 80, "Authorised Signatory")

    # Footer
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#94a3b8"))
    c.drawCentredString(page_width / 2, 40, "TECH X INNOVATION EVENT 2026 • All Rights Reserved")

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

# =========================================================
# FASTAPI APP
# =========================================================
app = FastAPI(
    title="TECH X INNOVATION EVENT 2026 - E-Certificate Automation",
    description="FastAPI Backend for generating participant E-Certificates dynamically.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# PYDANTIC MODELS
# =========================================================
class CertificateRequest(BaseModel):
    fullName: str
    email: str

    @field_validator("fullName")
    @classmethod
    def validate_name(cls, v: str) -> str:
        name = v.strip()
        if not name:
            raise ValueError("Full Name is required.")
        if len(name) < 3:
            raise ValueError("Full Name must be at least 3 characters long.")
        if len(name) > 60:
            raise ValueError("Full Name cannot exceed 60 characters.")
        if not re.match(r"^[A-Za-z][A-Za-z\s.'-]*$", name):
            raise ValueError("Full Name contains invalid characters.")
        return name

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        email = v.strip().lower()
        if not email:
            raise ValueError("Email ID is required.")
        email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        if not re.match(email_regex, email):
            raise ValueError("Invalid email address format.")
        return email

# =========================================================
# EMBEDDED FRONTEND HTML
# =========================================================
FRONTEND_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="Generate and download your personalized E-Certificate for TECH X INNOVATION EVENT 2026." />
  <meta name="theme-color" content="#1d4ed8" />
  <title>E-Certificate Automation Web Application | TECH X INNOVATION EVENT 2026</title>

  <!-- Bootstrap 5 -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" />
  <!-- Bootstrap Icons -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet" />
  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800;1,500;1,600&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet" />

  <style>
    /* =========================================================
       TECH X INNOVATION EVENT 2026
       E-Certificate Automation Web Application
       Full UI + Animations (Single File)
       ========================================================= */

    /* ---------- ROOT VARIABLES ---------- */
    :root {
      --white: #ffffff;
      --off-white: #f7f9fc;
      --blue: #1d4ed8;
      --blue-dark: #1e3a8a;
      --blue-light: #3b82f6;
      --blue-soft: #dbeafe;
      --orange: #f97316;
      --orange-light: #fb923c;
      --orange-soft: #ffedd5;
      --red: #dc2626;
      --red-dark: #b91c1c;
      --navy: #0f172a;
      --text-dark: #0b1220;
      --text-mid: #475569;
      --text-light: #94a3b8;
      --border: #e2e8f0;

      --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.06);
      --shadow-md: 0 6px 18px rgba(15, 23, 42, 0.08);
      --shadow-lg: 0 20px 50px rgba(15, 23, 42, 0.12);
      --shadow-blue: 0 12px 30px rgba(29, 78, 216, 0.28);
      --shadow-red: 0 12px 26px rgba(220, 38, 38, 0.32);

      --radius-sm: 10px;
      --radius-md: 16px;
      --radius-lg: 24px;
      --radius-xl: 32px;

      --font-main: "Plus Jakarta Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      --font-mono: "JetBrains Mono", ui-monospace, Menlo, Consolas, monospace;

      --ease: cubic-bezier(0.22, 1, 0.36, 1);
    }

    /* ---------- RESET ---------- */
    *,
    *::before,
    *::after {
      box-sizing: border-box;
    }

    html {
      scroll-behavior: smooth;
      -webkit-text-size-adjust: 100%;
    }

    body {
      margin: 0;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      font-family: var(--font-main);
      color: var(--text-dark);
      background: var(--white);
      overflow-x: hidden;
      position: relative;
    }

    /* Soft ambient background gradients */
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      z-index: -3;
      background:
        radial-gradient(900px 500px at 12% -8%, rgba(59, 130, 246, 0.10), transparent 60%),
        radial-gradient(800px 480px at 92% 6%, rgba(249, 115, 22, 0.10), transparent 60%),
        radial-gradient(700px 500px at 50% 110%, rgba(29, 78, 216, 0.08), transparent 60%),
        linear-gradient(180deg, #ffffff 0%, #f7faff 45%, #fff7f1 100%);
      pointer-events: none;
    }

    /* Faint tech grid overlay */
    .grid-overlay {
      position: fixed;
      inset: 0;
      z-index: -2;
      pointer-events: none;
      opacity: 0.5;
      background-image:
        linear-gradient(rgba(29, 78, 216, 0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(29, 78, 216, 0.05) 1px, transparent 1px);
      background-size: 46px 46px;
      mask-image: radial-gradient(circle at 50% 40%, #000 20%, transparent 78%);
      -webkit-mask-image: radial-gradient(circle at 50% 40%, #000 20%, transparent 78%);
    }

    /* =========================================================
       FLOATING TECH BACKGROUND
       ========================================================= */
    .tech-bg {
      position: fixed;
      inset: 0;
      z-index: -1;
      overflow: hidden;
      pointer-events: none;
      contain: strict;
    }

    .tech-icon {
      position: absolute;
      top: 0;
      left: 0;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 6px 12px;
      font-family: var(--font-mono);
      font-weight: 700;
      color: #1d4ed8;
      background: rgba(255, 255, 255, 0.62);
      border: 1px solid rgba(29, 78, 216, 0.14);
      border-radius: 999px;
      box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
      white-space: nowrap;
      user-select: none;
      will-change: transform, opacity;
      backdrop-filter: blur(3px);
      -webkit-backdrop-filter: blur(3px);
    }

    .tech-icon.orange {
      color: #ea580c;
      border-color: rgba(249, 115, 22, 0.18);
    }

    .tech-icon.plain {
      background: transparent;
      border-color: transparent;
      box-shadow: none;
      font-size: 20px;
      color: #f97316;
    }

    /* Floating animation */
    @keyframes floatUp {
      0% {
        transform: translate3d(0, 0, 0) rotate(0deg);
        opacity: 0;
      }
      10% {
        opacity: 1;
      }
      50% {
        transform: translate3d(14px, -52vh, 0) rotate(6deg);
        opacity: 0.85;
      }
      90% {
        opacity: 0.6;
      }
      100% {
        transform: translate3d(-10px, -108vh, 0) rotate(-4deg);
        opacity: 0;
      }
    }

    @keyframes floatSide {
      0%   { transform: translate3d(0, 0, 0) rotate(0deg); }
      50%  { transform: translate3d(22px, -20px, 0) rotate(7deg); }
      100% { transform: translate3d(0, 0, 0) rotate(0deg); }
    }

    .tech-icon.bubble {
      animation: floatUp linear infinite;
    }

    .tech-icon.side {
      animation: floatSide ease-in-out infinite;
    }

    /* =========================================================
       PAGE HEADER
       ========================================================= */
    .page-header {
      padding: 46px 0 10px;
      text-align: center;
      position: relative;
      z-index: 2;
    }

    .main-title {
      margin: 0;
      font-size: clamp(1.5rem, 4.4vw, 3rem);
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #000000;
      line-height: 1.18;
      text-wrap: balance;
    }

    .main-title::after {
      content: "";
      display: block;
      width: 120px;
      height: 4px;
      margin: 18px auto 0;
      border-radius: 999px;
      background: linear-gradient(90deg, var(--blue), var(--orange));
      box-shadow: 0 4px 14px rgba(29, 78, 216, 0.28);
    }

    /* Subtitle */
    .subtitle-wrap {
      position: relative;
      display: inline-block;
      margin-top: 20px;
      padding: 10px 26px;
      border-radius: 999px;
      background: linear-gradient(120deg, rgba(29, 78, 216, 0.94), rgba(30, 64, 175, 0.96));
      box-shadow: var(--shadow-blue);
      overflow: hidden;
    }

    .subtitle-wrap::after {
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(110deg, transparent 20%, rgba(255, 255, 255, 0.34) 50%, transparent 80%);
      transform: translateX(-120%);
      animation: shimmer 3.6s var(--ease) infinite;
    }

    @keyframes shimmer {
      0%   { transform: translateX(-120%); }
      55%  { transform: translateX(120%); }
      100% { transform: translateX(120%); }
    }

    .sub-title {
      position: relative;
      z-index: 1;
      margin: 0;
      font-size: clamp(0.82rem, 2.2vw, 1.15rem);
      font-style: italic;
      font-weight: 600;
      letter-spacing: 0.3px;
      color: #ffffff;
      text-shadow: 0 2px 10px rgba(0, 0, 0, 0.22);
    }

    /* =========================================================
       MAIN SECTION
       ========================================================= */
    .page-main {
      flex: 1 0 auto;
      padding: 40px 0 60px;
      position: relative;
      z-index: 2;
    }

    /* =========================================================
       CERTIFICATE CARD
       ========================================================= */
    .cert-card {
      position: relative;
      border-radius: var(--radius-lg);
      background: rgba(255, 255, 255, 0.82);
      border: 1px solid rgba(255, 255, 255, 0.85);
      box-shadow:
        0 24px 60px rgba(15, 23, 42, 0.12),
        0 2px 0 rgba(255, 255, 255, 0.9) inset,
        0 0 0 1px rgba(29, 78, 216, 0.06);
      backdrop-filter: blur(18px) saturate(150%);
      -webkit-backdrop-filter: blur(18px) saturate(150%);
      overflow: hidden;
      animation: cardRise 0.9s var(--ease) both;
      transition: transform 0.4s var(--ease), box-shadow 0.4s var(--ease);
    }

    .cert-card:hover {
      transform: translateY(-4px);
      box-shadow:
        0 34px 80px rgba(15, 23, 42, 0.16),
        0 2px 0 rgba(255, 255, 255, 0.9) inset,
        0 0 0 1px rgba(29, 78, 216, 0.10);
    }

    @keyframes cardRise {
      from { opacity: 0; transform: translateY(26px) scale(0.98); }
      to   { opacity: 1; transform: translateY(0) scale(1); }
    }

    /* Top accent bar */
    .card-accent-bar {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 6px;
      background: linear-gradient(90deg, var(--blue) 0%, var(--blue-light) 35%, var(--orange) 70%, var(--orange-light) 100%);
      background-size: 220% 100%;
      animation: barSlide 6s linear infinite;
    }

    @keyframes barSlide {
      0%   { background-position: 0% 50%; }
      100% { background-position: 220% 50%; }
    }

    /* Corner glows */
    .glow {
      position: absolute;
      border-radius: 50%;
      filter: blur(58px);
      opacity: 0.5;
      pointer-events: none;
      z-index: 0;
    }

    .glow-blue {
      width: 240px;
      height: 240px;
      top: -110px;
      left: -100px;
      background: radial-gradient(circle, rgba(59, 130, 246, 0.55), transparent 70%);
      animation: glowPulse 7s ease-in-out infinite;
    }

    .glow-orange {
      width: 220px;
      height: 220px;
      bottom: -110px;
      right: -90px;
      background: radial-gradient(circle, rgba(249, 115, 22, 0.45), transparent 70%);
      animation: glowPulse 7s ease-in-out infinite 2s;
    }

    @keyframes glowPulse {
      0%, 100% { transform: scale(1);    opacity: 0.45; }
      50%      { transform: scale(1.18); opacity: 0.72; }
    }

    .card-inner {
      position: relative;
      z-index: 1;
      padding: 40px 38px 34px;
    }

    /* Badge */
    .event-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 18px;
      font-size: 0.72rem;
      font-weight: 800;
      letter-spacing: 1.4px;
      text-transform: uppercase;
      color: var(--blue-dark);
      background: linear-gradient(135deg, var(--blue-soft), #ffffff 70%, var(--orange-soft));
      border: 1px solid rgba(29, 78, 216, 0.16);
      border-radius: 999px;
      box-shadow: var(--shadow-sm);
    }

    .event-badge i {
      color: var(--orange);
      font-size: 0.9rem;
    }

    /* Card title */
    .card-title {
      margin: 20px 0 8px;
      text-align: center;
      font-size: clamp(1.25rem, 3.2vw, 1.7rem);
      font-weight: 800;
      letter-spacing: -0.015em;
      color: var(--navy);
    }

    .card-subtitle {
      margin: 0 auto;
      max-width: 420px;
      text-align: center;
      font-size: 0.9rem;
      line-height: 1.65;
      color: var(--text-mid);
    }

    .divider {
      height: 1px;
      margin: 26px 0 28px;
      background: linear-gradient(90deg, transparent, rgba(29, 78, 216, 0.22), rgba(249, 115, 22, 0.22), transparent);
    }

    /* =========================================================
       FORM FIELDS
       ========================================================= */
    .field-group {
      margin-bottom: 22px;
    }

    .form-label {
      display: block;
      margin-bottom: 9px;
      font-size: 0.83rem;
      font-weight: 700;
      letter-spacing: 0.3px;
      color: var(--text-dark);
      text-transform: uppercase;
    }

    .req {
      color: var(--red);
      font-weight: 800;
    }

    .input-wrap {
      position: relative;
    }

    .input-icon {
      position: absolute;
      top: 50%;
      left: 16px;
      transform: translateY(-50%);
      font-size: 1rem;
      color: var(--blue-light);
      pointer-events: none;
      transition: color 0.3s var(--ease), transform 0.3s var(--ease);
      z-index: 2;
    }

    .custom-input {
      width: 100%;
      height: 54px;
      padding: 0 18px 0 46px;
      font-family: var(--font-main);
      font-size: 0.95rem;
      font-weight: 500;
      color: var(--text-dark);
      background: rgba(255, 255, 255, 0.9);
      border: 1.8px solid var(--border);
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-sm);
      outline: none;
      transition:
        border-color 0.28s var(--ease),
        box-shadow 0.28s var(--ease),
        transform 0.28s var(--ease),
        background 0.28s var(--ease);
    }

    .custom-input::placeholder {
      color: var(--text-light);
      font-weight: 400;
    }

    .custom-input:hover {
      border-color: #cbd5e1;
    }

    .custom-input:focus {
      background: #ffffff;
      border-color: var(--blue);
      box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.16), var(--shadow-md);
      transform: translateY(-1px);
    }

    .input-wrap:focus-within .input-icon {
      color: var(--blue);
      transform: translateY(-50%) scale(1.12);
    }

    /* Valid / invalid states */
    .field-group.invalid .custom-input {
      border-color: var(--red);
      background: #fff5f5;
      box-shadow: 0 0 0 4px rgba(220, 38, 38, 0.10);
      animation: shake 0.42s var(--ease);
    }

    .field-group.invalid .input-icon {
      color: var(--red);
    }

    .field-group.valid .custom-input {
      border-color: #16a34a;
      background: #f4fff8;
    }

    .field-group.valid .input-icon {
      color: #16a34a;
    }

    @keyframes shake {
      0%, 100% { transform: translateX(0); }
      20%      { transform: translateX(-7px); }
      40%      { transform: translateX(7px); }
      60%      { transform: translateX(-4px); }
      80%      { transform: translateX(4px); }
    }

    /* Error text */
    .error-msg {
      display: block;
      min-height: 18px;
      margin-top: 6px;
      padding-left: 4px;
      font-size: 0.79rem;
      font-weight: 600;
      color: var(--red);
      opacity: 0;
      transform: translateY(-4px);
      transition: opacity 0.28s var(--ease), transform 0.28s var(--ease);
    }

    .field-group.invalid .error-msg {
      opacity: 1;
      transform: translateY(0);
    }

    /* =========================================================
       DOWNLOAD BUTTON
       ========================================================= */
    .download-btn {
      position: relative;
      width: 100%;
      height: 58px;
      margin-top: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: var(--font-main);
      font-size: 1.02rem;
      font-weight: 800;
      letter-spacing: 0.4px;
      color: #ffffff;
      background: linear-gradient(135deg, #ef4444 0%, var(--red) 55%, var(--red-dark) 100%);
      background-size: 180% 180%;
      border: none;
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-red);
      cursor: pointer;
      overflow: hidden;
      outline: none;
      transition:
        transform 0.28s var(--ease),
        box-shadow 0.28s var(--ease),
        background-position 0.6s var(--ease),
        filter 0.28s var(--ease);
    }

    .download-btn::before {
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(110deg, transparent 25%, rgba(255, 255, 255, 0.32) 50%, transparent 75%);
      transform: translateX(-130%);
      transition: transform 0.75s var(--ease);
    }

    .download-btn:hover:not(:disabled) {
      background-position: 100% 50%;
      transform: translateY(-3px);
      box-shadow: 0 18px 36px rgba(220, 38, 38, 0.42);
    }

    .download-btn:hover:not(:disabled)::before {
      transform: translateX(130%);
    }

    .download-btn:active:not(:disabled) {
      transform: translateY(-1px) scale(0.99);
      box-shadow: 0 8px 20px rgba(220, 38, 38, 0.36);
    }

    .download-btn:focus-visible {
      box-shadow: 0 0 0 4px rgba(220, 38, 38, 0.28), var(--shadow-red);
    }

    .download-btn:disabled {
      cursor: not-allowed;
      filter: saturate(0.75) brightness(0.96);
    }

    .btn-content,
    .btn-loading {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      position: relative;
      z-index: 1;
      transition: opacity 0.28s var(--ease), transform 0.28s var(--ease);
    }

    .btn-content i {
      font-size: 1.12rem;
      transition: transform 0.4s var(--ease);
    }

    .download-btn:hover:not(:disabled) .btn-content i {
      transform: translateY(2px);
    }

    /* Loading state */
    .btn-loading {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      transform: translateY(6px);
    }

    .download-btn.loading .btn-content {
      opacity: 0;
      transform: translateY(-8px);
    }

    .download-btn.loading .btn-loading {
      opacity: 1;
      transform: translateY(0);
    }

    /* Spinner */
    .spinner {
      width: 18px;
      height: 18px;
      border-radius: 50%;
      border: 2.4px solid rgba(255, 255, 255, 0.35);
      border-top-color: #ffffff;
      animation: spin 0.75s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    /* Note */
    .form-note {
      margin: 16px 0 0;
      text-align: center;
      font-size: 0.78rem;
      font-weight: 500;
      color: var(--text-mid);
    }

    .form-note i {
      color: var(--blue);
      margin-right: 5px;
    }

    /* =========================================================
       STEP STRIP
       ========================================================= */
    .step-strip {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: center;
      gap: 10px;
      margin-top: 26px;
      padding: 14px 18px;
      border-radius: var(--radius-md);
      background: rgba(255, 255, 255, 0.7);
      border: 1px solid rgba(29, 78, 216, 0.10);
      box-shadow: var(--shadow-sm);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      animation: cardRise 1s var(--ease) 0.15s both;
    }

    .step-item {
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }

    .step-num {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      font-size: 0.72rem;
      font-weight: 800;
      color: #ffffff;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--blue), var(--blue-dark));
      box-shadow: 0 4px 10px rgba(29, 78, 216, 0.3);
    }

    .step-item:nth-child(3) .step-num {
      background: linear-gradient(135deg, var(--orange), #ea580c);
      box-shadow: 0 4px 10px rgba(249, 115, 22, 0.32);
    }

    .step-text {
      font-size: 0.8rem;
      font-weight: 700;
      color: var(--text-mid);
    }

    .step-arrow {
      color: var(--text-light);
      font-size: 0.85rem;
    }

    /* =========================================================
       TOAST NOTIFICATIONS
       ========================================================= */
    .toast-stack {
      position: fixed;
      right: 20px;
      bottom: 20px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 12px;
      max-width: min(370px, calc(100vw - 40px));
      pointer-events: none;
    }

    .toast {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 14px 16px;
      border-radius: var(--radius-md);
      background: rgba(255, 255, 255, 0.97);
      border-left: 5px solid var(--blue);
      box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      pointer-events: auto;
      animation: toastIn 0.45s var(--ease) both;
    }

    .toast.hide {
      animation: toastOut 0.4s var(--ease) both;
    }

    .toast.success { border-left-color: #16a34a; }
    .toast.error   { border-left-color: var(--red); }
    .toast.info    { border-left-color: var(--orange); }

    .toast-icon {
      font-size: 1.15rem;
      line-height: 1;
      margin-top: 1px;
    }

    .toast.success .toast-icon { color: #16a34a; }
    .toast.error   .toast-icon { color: var(--red); }
    .toast.info    .toast-icon { color: var(--orange); }

    .toast-body {
      flex: 1;
      min-width: 0;
    }

    .toast-title {
      margin: 0 0 2px;
      font-size: 0.86rem;
      font-weight: 800;
      color: var(--navy);
    }

    .toast-msg {
      margin: 0;
      font-size: 0.79rem;
      font-weight: 500;
      line-height: 1.5;
      color: var(--text-mid);
      word-wrap: break-word;
    }

    .toast-close {
      background: transparent;
      border: none;
      color: var(--text-light);
      font-size: 1rem;
      line-height: 1;
      cursor: pointer;
      padding: 0 2px;
      transition: color 0.2s var(--ease), transform 0.2s var(--ease);
    }

    .toast-close:hover {
      color: var(--text-dark);
      transform: scale(1.15);
    }

    @keyframes toastIn {
      from { opacity: 0; transform: translateX(40px) scale(0.96); }
      to   { opacity: 1; transform: translateX(0) scale(1); }
    }

    @keyframes toastOut {
      from { opacity: 1; transform: translateX(0) scale(1); }
      to   { opacity: 0; transform: translateX(40px) scale(0.96); }
    }

    /* =========================================================
       FOOTER
       ========================================================= */
    .site-footer {
      position: relative;
      margin-top: auto;
      padding: 40px 0 34px;
      text-align: center;
      color: #e2e8f0;
      background:
        radial-gradient(600px 200px at 50% 0%, rgba(59, 130, 246, 0.22), transparent 70%),
        linear-gradient(160deg, #0f172a 0%, #111c34 55%, #1a1207 100%);
      border-top: 3px solid transparent;
      border-image: linear-gradient(90deg, var(--blue), var(--orange)) 1;
      overflow: hidden;
      z-index: 2;
    }

    .footer-glow {
      position: absolute;
      top: -70px;
      left: 50%;
      transform: translateX(-50%);
      width: 460px;
      height: 160px;
      background: radial-gradient(ellipse, rgba(249, 115, 22, 0.22), transparent 70%);
      filter: blur(30px);
      pointer-events: none;
    }

    .footer-lines {
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-bottom: 20px;
    }

    .footer-line {
      margin: 0;
      font-size: clamp(0.82rem, 2.2vw, 0.98rem);
      font-weight: 800;
      letter-spacing: 1.1px;
      color: #ffffff;
      text-transform: uppercase;
    }

    .footer-crown {
      font-size: clamp(0.95rem, 2.6vw, 1.15rem);
      background: linear-gradient(90deg, #fbbf24, #f97316, #fbbf24);
      background-size: 200% 100%;
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
      color: transparent;
      animation: crownShine 3.4s linear infinite;
    }

    @keyframes crownShine {
      0%   { background-position: 0% 50%; }
      100% { background-position: 200% 50%; }
    }

    .footer-divider {
      height: 1px;
      max-width: 620px;
      margin: 0 auto 18px;
      background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.55), rgba(249, 115, 22, 0.55), transparent);
    }

    .footer-note {
      margin: 0 auto;
      max-width: 620px;
      font-size: clamp(0.76rem, 1.9vw, 0.86rem);
      font-weight: 500;
      line-height: 1.7;
      color: #b6c2d9;
    }

    /* =========================================================
       WHATSAPP CHAT BUTTON (FOOTER — LEFT SIDE)
       ========================================================= */
    .wa-btn {
      position: absolute;
      top: 40px;
      left: 26px;
      z-index: 6;
      display: inline-flex;
      align-items: center;
      gap: 11px;
      padding: 10px 20px 10px 12px;
      font-family: var(--font-main);
      font-size: 0.84rem;
      font-weight: 800;
      letter-spacing: 0.3px;
      color: #ffffff !important;
      text-decoration: none;
      border-radius: 999px;
      background: linear-gradient(135deg, #25d366 0%, #1ebe5b 45%, #128c7e 100%);
      background-size: 190% 190%;
      border: 1px solid rgba(255, 255, 255, 0.24);
      box-shadow: 0 12px 26px rgba(18, 140, 126, 0.45);
      white-space: nowrap;
      transition:
        transform 0.3s var(--ease),
        box-shadow 0.3s var(--ease),
        background-position 0.6s var(--ease);
    }

    .wa-btn:hover,
    .wa-btn:focus-visible {
      color: #ffffff !important;
      transform: translateY(-3px) scale(1.03);
      background-position: 100% 50%;
      box-shadow: 0 18px 34px rgba(37, 211, 102, 0.55);
      outline: none;
    }

    .wa-btn .wa-ico {
      position: relative;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      flex: 0 0 auto;
      width: 32px;
      height: 32px;
      font-size: 1.15rem;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.22);
    }

    .wa-btn .wa-ico::after {
      content: "";
      position: absolute;
      inset: 0;
      border-radius: 50%;
      border: 2px solid rgba(37, 211, 102, 0.85);
      animation: waRing 2.2s ease-out infinite;
      pointer-events: none;
    }

    @keyframes waRing {
      0%   { transform: scale(1);    opacity: 0.9; }
      70%  { transform: scale(1.85); opacity: 0; }
      100% { transform: scale(1.85); opacity: 0; }
    }

    .wa-btn .wa-txt {
      display: flex;
      flex-direction: column;
      line-height: 1.18;
      text-align: left;
    }

    .wa-btn .wa-txt small {
      font-size: 0.62rem;
      font-weight: 700;
      letter-spacing: 0.7px;
      text-transform: uppercase;
      opacity: 0.9;
    }

    .wa-btn .wa-txt strong {
      font-size: 0.85rem;
      font-weight: 800;
      letter-spacing: 0.2px;
    }

    /* =========================================================
       RESPONSIVE
       ========================================================= */
    @media (max-width: 991.98px) {
      .wa-btn {
        position: static;
        margin: 0 auto 26px;
        width: max-content;
        max-width: calc(100% - 32px);
        padding: 10px 18px 10px 11px;
      }

      .site-footer {
        padding-top: 32px;
      }
    }

    @media (max-width: 575.98px) {
      .page-header {
        padding: 32px 0 6px;
      }

      .main-title::after {
        width: 90px;
        margin-top: 14px;
      }

      .subtitle-wrap {
        padding: 9px 18px;
        border-radius: 18px;
      }

      .card-inner {
        padding: 30px 20px 26px;
      }

      .custom-input {
        height: 52px;
        font-size: 0.92rem;
      }

      .download-btn {
        height: 54px;
        font-size: 0.96rem;
      }

      .step-strip {
        gap: 8px;
        padding: 12px;
      }

      .step-arrow {
        display: none;
      }

      .toast-stack {
        right: 12px;
        left: 12px;
        bottom: 12px;
        max-width: none;
      }

      .wa-btn {
        font-size: 0.8rem;
        gap: 9px;
      }

      .wa-btn .wa-ico {
        width: 30px;
        height: 30px;
        font-size: 1.05rem;
      }
    }

    @media (max-width: 359.98px) {
      .event-badge {
        font-size: 0.62rem;
        padding: 7px 12px;
      }

      .card-title {
        font-size: 1.12rem;
      }

      .wa-btn .wa-txt small {
        font-size: 0.56rem;
      }

      .wa-btn .wa-txt strong {
        font-size: 0.78rem;
      }
    }

    /* Reduce motion for accessibility */
    @media (prefers-reduced-motion: reduce) {
      *,
      *::before,
      *::after {
        animation-duration: 0.001ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.001ms !important;
        scroll-behavior: auto !important;
      }

      .tech-icon.bubble,
      .tech-icon.side {
        animation: none !important;
        opacity: 0.25;
      }
    }

    /* Hide decorative background animations on very small devices for performance */
    @media (max-width: 480px) {
      .grid-overlay {
        opacity: 0.28;
      }
    }
  </style>
</head>
<body>

  <!-- ================= FLOATING TECH BACKGROUND ================= -->
  <div class="tech-bg" id="techBg" aria-hidden="true"></div>
  <div class="grid-overlay" aria-hidden="true"></div>

  <!-- ================= PAGE HEADER ================= -->
  <header class="page-header">
    <div class="container">
      <h1 class="main-title">E-Certificate Automation Web Application</h1>

      <div class="subtitle-wrap">
        <span class="subtitle-glow" aria-hidden="true"></span>
        <p class="sub-title">
          Certificate for Participation in TECH X INNOVATION EVENT 2026
        </p>
      </div>
    </div>
  </header>

  <!-- ================= MAIN CONTENT ================= -->
  <main class="page-main">
    <section class="form-section">
      <div class="container">
        <div class="row justify-content-center">
          <div class="col-12 col-md-10 col-lg-7 col-xl-6">

            <!-- ============ CERTIFICATE CARD ============ -->
            <div class="cert-card">

              <!-- top accent bar -->
              <span class="card-accent-bar" aria-hidden="true"></span>

              <!-- corner glows -->
              <span class="glow glow-blue" aria-hidden="true"></span>
              <span class="glow glow-orange" aria-hidden="true"></span>

              <div class="card-inner">

                <!-- Card badge -->
                <div class="text-center">
                  <span class="event-badge">
                    <i class="bi bi-patch-check-fill"></i>
                    TECH X INNOVATION &nbsp;•&nbsp; 2026
                  </span>
                </div>

                <!-- Card heading -->
                <h2 class="card-title">Download Your Certificate</h2>
                <p class="card-subtitle">
                  Enter your details below and your personalized certificate will be
                  generated and downloaded instantly as a PDF.
                </p>

                <div class="divider"></div>

                <!-- ============ FORM ============ -->
                <form id="certificateForm" novalidate autocomplete="on">

                  <!-- Full Name -->
                  <div class="field-group">
                    <label for="fullName" class="form-label">
                      Full Name <span class="req">*</span>
                    </label>
                    <div class="input-wrap">
                      <i class="bi bi-person-fill input-icon" aria-hidden="true"></i>
                      <input
                        type="text"
                        id="fullName"
                        name="fullName"
                        class="form-control custom-input"
                        placeholder="Enter your full name"
                        autocomplete="name"
                        maxlength="60"
                        spellcheck="false"
                        aria-describedby="nameError"
                      />
                    </div>
                    <div class="error-msg" id="nameError" role="alert"></div>
                  </div>

                  <!-- Email -->
                  <div class="field-group">
                    <label for="email" class="form-label">
                      Email ID <span class="req">*</span>
                    </label>
                    <div class="input-wrap">
                      <i class="bi bi-envelope-fill input-icon" aria-hidden="true"></i>
                      <input
                        type="email"
                        id="email"
                        name="email"
                        class="form-control custom-input"
                        placeholder="Enter your email address"
                        autocomplete="email"
                        maxlength="80"
                        spellcheck="false"
                        aria-describedby="emailError"
                      />
                    </div>
                    <div class="error-msg" id="emailError" role="alert"></div>
                  </div>

                  <!-- Download Button -->
                  <button type="submit" class="download-btn" id="downloadBtn">
                    <span class="btn-content" id="btnContent">
                      <i class="bi bi-download"></i>
                      <span>Download Certificate</span>
                    </span>

                    <span class="btn-loading" id="btnLoading">
                      <span class="spinner" aria-hidden="true"></span>
                      <span>Generating Certificate...</span>
                    </span>
                  </button>

                  <!-- Helper note -->
                  <p class="form-note">
                    <i class="bi bi-shield-lock-fill"></i>
                    Your details are used only to generate your certificate.
                  </p>

                </form>
                <!-- ============ /FORM ============ -->

              </div>
            </div>
            <!-- ============ /CERTIFICATE CARD ============ -->

            <!-- Step strip -->
            <div class="step-strip">
              <div class="step-item">
                <span class="step-num">1</span>
                <span class="step-text">Enter Full Name</span>
              </div>
              <i class="bi bi-arrow-right step-arrow" aria-hidden="true"></i>
              <div class="step-item">
                <span class="step-num">2</span>
                <span class="step-text">Enter Email ID</span>
              </div>
              <i class="bi bi-arrow-right step-arrow" aria-hidden="true"></i>
              <div class="step-item">
                <span class="step-num">3</span>
                <span class="step-text">Download PDF</span>
              </div>
            </div>

          </div>
        </div>
      </div>
    </section>
  </main>

  <!-- ================= TOAST NOTIFICATION ================= -->
  <div class="toast-stack" id="toastStack" aria-live="polite" aria-atomic="true"></div>

  <!-- ================= FOOTER ================= -->
  <footer class="site-footer">
    <div class="footer-glow" aria-hidden="true"></div>

    <!-- ===== WHATSAPP CHAT BUTTON (LEFT SIDE OF FOOTER) ===== -->
    <a
      class="wa-btn"
      href="https://wa.me/917310927827?text=Hello%20TECH%20X%20INNOVATION%20EVENT%202026%20Team%2C%20I%20need%20help%20with%20my%20E-Certificate."
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Chat on WhatsApp with +91 73109 27827"
    >
      <span class="wa-ico" aria-hidden="true">
        <i class="bi bi-whatsapp"></i>
      </span>
      <span class="wa-txt">
        <small>Chat on WhatsApp</small>
        <strong>+91 73109 27827</strong>
      </span>
    </a>
    <!-- ===== /WHATSAPP CHAT BUTTON ===== -->

    <div class="container position-relative">

      <div class="footer-lines">
        <p class="footer-line">All Rights Reserved // 2026</p>
        <p class="footer-line">Web Developer</p>
        <p class="footer-line">TECH X INNOVATION EVENT</p>
        <p class="footer-line footer-crown">Virat King 👑</p>
      </div>

      <div class="footer-divider" aria-hidden="true"></div>

      <p class="footer-note">
        This website provides E-Certificate services for TECH X INNOVATION EVENT 2026.
      </p>
    </div>
  </footer>

  <!-- Bootstrap JS -->
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>

  <script>
    /* =========================================================
       TECH X INNOVATION EVENT 2026
       E-Certificate Automation Web Application
       Full Animation + Validation + PDF Download
       ========================================================= */

    (function () {
      "use strict";

      /* =========================================================
         1. FLOATING TECH BACKGROUND ICONS
         ========================================================= */
      const TECH_LABELS = [
        "C", "C++", "Python", "HTML", "CSS", "JS",
        "</>", "{ }", "<code>", "Java", "SQL", "Git",
        "React", "Node", "API", "AI", "ML", "Linux"
      ];

      const TECH_SYMBOLS = [
        "bi-cpu", "bi-diagram-3", "bi-braces", "bi-code-slash",
        "bi-terminal", "bi-cpu-fill", "bi-hdd-network", "bi-lightning-charge-fill"
      ];

      function rand(min, max) {
        return Math.random() * (max - min) + min;
      }

      function pick(arr) {
        return arr[Math.floor(Math.random() * arr.length)];
      }

      function createFloatingIcons() {
        const bg = document.getElementById("techBg");
        if (!bg) return;

        const width = window.innerWidth;
        let count = 22;
        if (width < 992) count = 16;
        if (width < 576) count = 9;
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) count = 6;

        const frag = document.createDocumentFragment();

        for (let i = 0; i < count; i++) {
          const el = document.createElement("span");
          const isSymbol = Math.random() < 0.22;

          if (isSymbol) {
            el.className = "tech-icon plain bubble";
            el.innerHTML = '<i class="bi ' + pick(TECH_SYMBOLS) + '"></i>';
            el.style.fontSize = rand(16, 30).toFixed(1) + "px";
            el.style.opacity = rand(0.10, 0.20).toFixed(2);
          } else {
            const useOrange = Math.random() < 0.35;
            el.className = "tech-icon bubble" + (useOrange ? " orange" : "");
            el.textContent = pick(TECH_LABELS);
            el.style.fontSize = rand(10, 19).toFixed(1) + "px";
            el.style.opacity = rand(0.12, 0.30).toFixed(2);
          }

          el.style.left = rand(-2, 98).toFixed(2) + "vw";
          el.style.top = rand(100, 140).toFixed(2) + "vh";

          const duration = rand(22, 46).toFixed(1);
          const delay = rand(0, 22).toFixed(1);
          el.style.animationDuration = duration + "s";
          el.style.animationDelay = "-" + delay + "s";

          const blur = rand(0, 1.1).toFixed(2);
          if (Math.random() < 0.4) {
            el.style.filter = "blur(" + blur + "px)";
          }

          frag.appendChild(el);
        }

        bg.appendChild(frag);
      }

      /* =========================================================
         2. TOAST NOTIFICATIONS
         ========================================================= */
      const TOAST_ICONS = {
        success: "bi-check-circle-fill",
        error: "bi-x-circle-fill",
        info: "bi-info-circle-fill"
      };

      function showToast(type, title, message, duration) {
        const stack = document.getElementById("toastStack");
        if (!stack) return;

        const toast = document.createElement("div");
        toast.className = "toast " + type;
        toast.setAttribute("role", "status");

        toast.innerHTML =
          '<i class="bi ' + (TOAST_ICONS[type] || TOAST_ICONS.info) + ' toast-icon"></i>' +
          '<div class="toast-body">' +
            '<p class="toast-title">' + escapeHTML(title) + '</p>' +
            '<p class="toast-msg">' + escapeHTML(message) + '</p>' +
          '</div>' +
          '<button class="toast-close" type="button" aria-label="Close notification">' +
            '<i class="bi bi-x-lg"></i>' +
          '</button>';

        stack.appendChild(toast);

        const remove = () => {
          toast.classList.add("hide");
          setTimeout(() => toast.remove(), 400);
        };

        toast.querySelector(".toast-close").addEventListener("click", remove);
        setTimeout(remove, duration || 5200);
      }

      function escapeHTML(str) {
        return String(str)
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;")
          .replace(/'/g, "&#039;");
      }

      /* =========================================================
         3. FORM VALIDATION
         ========================================================= */
      const form = document.getElementById("certificateForm");
      const nameInput = document.getElementById("fullName");
      const emailInput = document.getElementById("email");
      const nameError = document.getElementById("nameError");
      const emailError = document.getElementById("emailError");
      const downloadBtn = document.getElementById("downloadBtn");

      const EMAIL_RE = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;

      function setError(input, errorEl, group, message) {
        errorEl.textContent = message;
        group.classList.add("invalid");
        group.classList.remove("valid");
        input.setAttribute("aria-invalid", "true");
      }

      function setValid(input, errorEl, group) {
        errorEl.textContent = "";
        group.classList.remove("invalid");
        group.classList.add("valid");
        input.setAttribute("aria-invalid", "false");
      }

      function clearState(input, errorEl, group) {
        errorEl.textContent = "";
        group.classList.remove("invalid", "valid");
        input.removeAttribute("aria-invalid");
      }

      function getGroup(input) {
        return input.closest(".field-group");
      }

      function validateName(silent) {
        const group = getGroup(nameInput);
        const value = nameInput.value.trim();

        if (!value) {
          if (!silent) setError(nameInput, nameError, group, "Please enter your full name.");
          return false;
        }

        if (value.length < 3) {
          if (!silent) setError(nameInput, nameError, group, "Name must be at least 3 characters long.");
          return false;
        }

        if (!/^[A-Za-z][A-Za-z\s.'-]*$/.test(value)) {
          if (!silent) setError(nameInput, nameError, group, "Name can contain only letters, spaces, and . ' -");
          return false;
        }

        setValid(nameInput, nameError, group);
        return true;
      }

      function validateEmail(silent) {
        const group = getGroup(emailInput);
        const value = emailInput.value.trim();

        if (!value) {
          if (!silent) setError(emailInput, emailError, group, "Please enter your email address.");
          return false;
        }

        if (!EMAIL_RE.test(value)) {
          if (!silent) setError(emailInput, emailError, group, "Please enter a valid email address.");
          return false;
        }

        setValid(emailInput, emailError, group);
        return true;
      }

      nameInput.addEventListener("blur", () => validateName(false));
      emailInput.addEventListener("blur", () => validateEmail(false));

      nameInput.addEventListener("input", () => {
        const group = getGroup(nameInput);
        if (group.classList.contains("invalid")) validateName(false);
        else if (
          nameInput.value.trim().length >= 3 &&
          /^[A-Za-z][A-Za-z\s.'-]*$/.test(nameInput.value.trim())
        ) {
          setValid(nameInput, nameError, group);
        } else {
          clearState(nameInput, nameError, group);
        }
      });

      emailInput.addEventListener("input", () => {
        const group = getGroup(emailInput);
        if (group.classList.contains("invalid")) validateEmail(false);
        else if (EMAIL_RE.test(emailInput.value.trim())) {
          setValid(emailInput, emailError, group);
        } else {
          clearState(emailInput, emailError, group);
        }
      });

      /* =========================================================
         4. BUTTON LOADING STATE
         ========================================================= */
      function setLoading(isLoading) {
        if (isLoading) {
          downloadBtn.classList.add("loading");
          downloadBtn.disabled = true;
          downloadBtn.setAttribute("aria-busy", "true");
        } else {
          downloadBtn.classList.remove("loading");
          downloadBtn.disabled = false;
          downloadBtn.removeAttribute("aria-busy");
        }
      }

      /* =========================================================
         5. FILE DOWNLOAD HELPER
         ========================================================= */
      function triggerDownload(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filename || "TECHX_Certificate.pdf";
        link.style.display = "none";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setTimeout(() => window.URL.revokeObjectURL(url), 4000);
      }

      function buildFilename(fullName) {
        const safe = fullName
          .trim()
          .replace(/[^A-Za-z0-9]+/g, "_")
          .replace(/^_+|_+$/g, "")
          .slice(0, 40);
        return "TECHX_2026_Certificate_" + (safe || "Participant") + ".pdf";
      }

      /* =========================================================
         6. FORM SUBMIT → API CALL → PDF DOWNLOAD
         ========================================================= */
      form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const nameOk = validateName(false);
        const emailOk = validateEmail(false);

        if (!nameOk || !emailOk) {
          showToast("error", "Validation Failed", "Please correct the highlighted fields and try again.");
          if (!nameOk) nameInput.focus();
          else if (!emailOk) emailInput.focus();
          return;
        }

        const fullName = nameInput.value.trim();
        const email = emailInput.value.trim();

        setLoading(true);

        try {
          const response = await fetch("/generate-certificate", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Accept": "application/pdf, application/json"
            },
            body: JSON.stringify({
              fullName: fullName,
              email: email
            })
          });

          if (!response.ok) {
            let serverMsg = "Unable to generate certificate. Please try again.";
            try {
              const data = await response.json();
              if (data && data.message) serverMsg = data.message;
            } catch (_) { /* ignore */ }
            throw new Error(serverMsg);
          }

          const contentType = response.headers.get("Content-Type") || "";

          if (contentType.includes("application/pdf")) {
            const blob = await response.blob();
            triggerDownload(blob, buildFilename(fullName));
            showToast("success", "Certificate Ready!", "Your certificate for " + fullName + " has been downloaded.");
          } else {
            const data = await response.json();

            if (data && data.downloadUrl) {
              const pdfRes = await fetch(data.downloadUrl);
              if (!pdfRes.ok) throw new Error("Unable to retrieve the generated certificate.");
              const blob = await pdfRes.blob();
              triggerDownload(blob, buildFilename(fullName));
              showToast("success", "Certificate Ready!", "Your certificate for " + fullName + " has been downloaded.");
            } else if (data && data.pdfBase64) {
              const byteChars = atob(data.pdfBase64);
              const bytes = new Uint8Array(byteChars.length);
              for (let i = 0; i < byteChars.length; i++) {
                bytes[i] = byteChars.charCodeAt(i);
              }
              const blob = new Blob([bytes], { type: "application/pdf" });
              triggerDownload(blob, buildFilename(fullName));
              showToast("success", "Certificate Ready!", "Your certificate for " + fullName + " has been downloaded.");
            } else {
              throw new Error("Unable to generate certificate. Please try again.");
            }
          }
        } catch (err) {
          console.error("Certificate generation error:", err);
          showToast(
            "error",
            "Generation Failed",
            err && err.message ? err.message : "Unable to generate certificate. Please try again."
          );
        } finally {
          setLoading(false);
        }
      });

      /* =========================================================
         7. INIT
         ========================================================= */
      document.addEventListener("DOMContentLoaded", function () {
        createFloatingIcons();

        if (window.innerWidth >= 992) {
          setTimeout(() => nameInput.focus(), 450);
        }
      });

      let resizeTimer = null;
      window.addEventListener("resize", function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () {
          const bg = document.getElementById("techBg");
          if (!bg) return;
          bg.innerHTML = "";
          createFloatingIcons();
        }, 350);
      });

    })();
  </script>
</body>
</html>
"""

# =========================================================
# ROUTES
# =========================================================
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    return FRONTEND_HTML

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "TECH X INNOVATION E-Certificate API"}

@app.post("/generate-certificate")
async def generate_certificate(data: CertificateRequest):
    try:
        logger.info(f"Generating certificate for {data.fullName} ({data.email})")

        # Generate PDF
        pdf_bytes = generate_pdf_certificate(data.fullName, data.email)

        # Save to database with a unique certificate ID
        cert_id = str(uuid.uuid4())[:8].upper()
        save_participant(data.fullName, data.email, cert_id)

        # Format safe download filename
        safe_name = re.sub(r'[^A-Za-z0-9]+', '_', data.fullName.strip()).strip('_')[:40]
        filename = f"TECHX_2026_Certificate_{safe_name or 'Participant'}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error generating certificate: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the certificate. Please try again."
        )

# =========================================================
# RUN (for local development)
# =========================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
