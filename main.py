import re
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator

from certificate import generate_pdf_certificate

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cert_app")

app = FastAPI(
    title="TECH X INNOVATION EVENT 2026 - E-Certificate Automation",
    description="FastAPI Backend for generating participant E-Certificates dynamically.",
    version="1.0.0"
)

# Enable CORS for cross-origin requests if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request schema
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

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

# Serve index.html at root
@app.get("/", response_class=HTMLResponse)
async def serve_home():
    html_file = TEMPLATES_DIR / "index.html"
    if not html_file.exists():
        raise HTTPException(status_code=404, detail="index.html not found.")
    with open(html_file, "r", encoding="utf-8") as f:
        return f.read()

# Health check endpoint for Render
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "TECH X INNOVATION E-Certificate API"}

# Certificate generation endpoint
@app.post("/generate-certificate")
async def generate_certificate(data: CertificateRequest):
    try:
        logger.info(f"Generating certificate for {data.fullName} ({data.email})")
        
        pdf_bytes = generate_pdf_certificate(data.fullName, data.email)
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
