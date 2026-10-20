"""
End-to-End System Tests for BitElevate Skill Gap Analyzer
"""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(root_dir / "backend") not in sys.path:
    sys.path.insert(0, str(root_dir / "backend"))

from backend.main import app

client = TestClient(app)


def test_health():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["available_roles_count"] >= 5
    print("✓ Health check endpoint passed")


def test_roles():
    res = client.get("/roles")
    assert res.status_code == 200
    data = res.json()
    roles = data["roles"]
    assert len(roles) >= 5
    role_titles = [r["title"] for r in roles]
    assert "AI Engineer" in role_titles
    assert "Data Analyst" in role_titles
    print(f"✓ Roles endpoint passed ({len(roles)} roles available)")


def test_analyze_text():
    payload = {
        "text": "Alex Chen. Experienced AI Engineer skilled in Python, PyTorch, FastAPI, Docker, and Git.",
        "target_role": "AI Engineer"
    }
    res = client.post("/analyze-text", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["metrics"]["match_percentage"] > 50
    assert "FastAPI" in data["skills_breakdown"]["matched_skills"]
    assert "Python" in data["skills_breakdown"]["matched_skills"]
    print(f"✓ Text analysis passed: {data['metrics']['match_percentage']}% match")


def test_analyze_gap_pdf():
    pdf_path = root_dir / "sample_resumes" / "alex_chen_ai_engineer.pdf"
    assert pdf_path.exists(), "Sample PDF not found"

    with open(pdf_path, "rb") as f:
        files = {"file": ("alex_chen_ai_engineer.pdf", f, "application/pdf")}
        data = {"target_role": "AI Engineer"}
        res = client.post("/analyze-gap", files=files, data=data)

    assert res.status_code == 200
    data = res.json()
    assert data["metrics"]["match_percentage"] >= 90
    assert data["metrics"]["readiness_level"] == "Job Ready (High Match)"
    assert len(data["skills_breakdown"]["missing_skills"]) <= 1
    print(f"✓ PDF analysis (Alex Chen vs AI Engineer) passed: {data['metrics']['match_percentage']}% match")


def test_analyze_fresher_pdf():
    pdf_path = root_dir / "sample_resumes" / "rohit_verma_fresher.pdf"
    assert pdf_path.exists(), "Sample PDF not found"

    with open(pdf_path, "rb") as f:
        files = {"file": ("rohit_verma_fresher.pdf", f, "application/pdf")}
        data = {"target_role": "AI Engineer"}
        res = client.post("/analyze-gap", files=files, data=data)

    assert res.status_code == 200
    data = res.json()
    assert data["metrics"]["match_percentage"] < 35
    assert len(data["skills_breakdown"]["missing_skills"]) >= 5
    assert len(data["recommendations"]["learning_path"]) >= 5
    print(f"✓ PDF analysis (Fresher vs AI Engineer) passed: {data['metrics']['match_percentage']}% match, {len(data['skills_breakdown']['missing_skills'])} gaps identified")


if __name__ == "__main__":
    print("\nRunning BitElevate System Verification Suite...")
    test_health()
    test_roles()
    test_analyze_text()
    test_analyze_gap_pdf()
    test_analyze_fresher_pdf()
    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!\n")
