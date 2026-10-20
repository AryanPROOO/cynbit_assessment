"""
BitElevate FastAPI Server
Author: Cynbit AI Team
Description: High-performance asynchronous REST API for resume parsing,
             skill extraction, and automated skill-gap analysis.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure backend directory is in python path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from nlp_engine import NLPEngine

# Initialize FastAPI App
app = FastAPI(
    title="Cynbit Studio - BitElevate Skill Gap Analyzer API",
    description="Automated AI Career Mapping and Skill Gap Analysis Engine for BitElevate.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for Streamlit / external clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize NLP Engine instance
nlp_engine = NLPEngine()


# Request / Response Schemas
class TextAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Raw plain text of the candidate's resume.")
    target_role: str = Field(..., description="Target role name (e.g., 'AI Engineer', 'Data Analyst').")


@app.get("/", tags=["Health & Info"])
def root_health_check() -> Dict[str, Any]:
    """Root endpoint for health checking and platform metadata."""
    roles = nlp_engine.get_available_roles()
    return {
        "status": "online",
        "service": "Cynbit Studio - BitElevate Skill Gap Analyzer",
        "version": "1.0.0",
        "available_roles_count": len(roles),
        "supported_roles": [r["title"] for r in roles],
        "endpoints": {
            "health": "/",
            "roles": "/roles",
            "analyze_gap": "/analyze-gap (POST Multipart)",
            "analyze_text": "/analyze-text (POST JSON)",
            "documentation": "/docs"
        }
    }


@app.get("/roles", tags=["Roles"])
def list_available_roles() -> Dict[str, Any]:
    """Retrieves all pre-configured target roles and required skills."""
    roles = nlp_engine.get_available_roles()
    return {
        "status": "success",
        "total_roles": len(roles),
        "roles": roles
    }


@app.get("/roles/{role_id_or_title}", tags=["Roles"])
def get_role_details(role_id_or_title: str) -> Dict[str, Any]:
    """Retrieves details of a specific target role."""
    role = nlp_engine.get_role_by_title_or_id(role_id_or_title)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_id_or_title}' not found in role database."
        )
    return {
        "status": "success",
        "role": role
    }


@app.post("/analyze-gap", tags=["Analysis"])
async def analyze_gap(
    file: UploadFile = File(..., description="Uploaded resume file (PDF or TXT)"),
    target_role: str = Form(..., description="Target role to compare against (e.g., 'AI Engineer')")
) -> Dict[str, Any]:
    """
    Primary endpoint: Parses an uploaded PDF resume and performs skill-gap analysis
    against the target role.
    """
    # 1. Validate file format
    filename = file.filename or "uploaded_resume.pdf"
    if not filename.lower().endswith((".pdf", ".txt", ".doc", ".docx")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload a PDF or TXT file."
        )

    # 2. Read file contents
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )

    if not content or len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty."
        )

    # 3. Extract text from PDF
    extracted_text = nlp_engine.extract_text_from_pdf(content)

    if not extracted_text or len(extracted_text.strip()) < 15:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract readable text from the uploaded document. Ensure it is not an image-only scanned PDF."
        )

    # 4. Perform skill-gap analysis
    try:
        result = nlp_engine.analyze_skill_gap(
            resume_text=extracted_text,
            target_role_query=target_role
        )
        result["filename"] = filename
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@app.post("/analyze-text", tags=["Analysis"])
def analyze_raw_text(payload: TextAnalyzeRequest) -> Dict[str, Any]:
    """
    Alternative endpoint: Analyzes resume text supplied directly in JSON format.
    Useful for testing, programmatic integrations, and non-PDF inputs.
    """
    try:
        result = nlp_engine.analyze_skill_gap(
            resume_text=payload.text,
            target_role_query=payload.target_role
        )
        result["filename"] = "direct_text_input"
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
