"""
BitElevate NLP Engine
Author: Cynbit AI Team
Description: Extracts text from resumes (PDF/text), parses skills using canonical taxonomy,
             tokenization, phrase matching, and spaCy linguistic processing, then calculates
             skill gaps, match percentages, and structured learning roadmaps.
"""

import io
import os
import re
import json
from typing import Dict, List, Set, Tuple, Optional, Any
from pathlib import Path

# Try loading spaCy with graceful fallback
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        # Fallback to blank model if en_core_web_sm not downloaded
        nlp = spacy.blank("en")
except ImportError:
    nlp = None

# PDF parsing imports with multiple fallback layers
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False


# Comprehensive Canonical Skill Map: Aliases / variations -> Canonical Display Name
SKILL_TAXONOMY: Dict[str, str] = {
    # AI / ML / Data Science
    "python": "Python",
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "tensorflow": "TensorFlow",
    "keras": "TensorFlow",
    "scikit-learn": "Scikit-Learn",
    "scikit learn": "Scikit-Learn",
    "sklearn": "Scikit-Learn",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "rag": "RAG",
    "retrieval augmented generation": "RAG",
    "retrieval-augmented generation": "RAG",
    "langchain": "LangChain",
    "llamaindex": "LlamaIndex",
    "llama index": "LlamaIndex",
    "hugging face": "Hugging Face",
    "huggingface": "Hugging Face",
    "transformers": "NLP",
    "vector databases": "Vector Databases",
    "vector database": "Vector Databases",
    "vector db": "Vector Databases",
    "chromadb": "Vector Databases",
    "pinecone": "Vector Databases",
    "qdrant": "Vector Databases",
    "milvus": "Vector Databases",
    "weaviate": "Vector Databases",
    "prompt engineering": "Prompt Engineering",
    "mlops": "MLOps",
    "mlflow": "MLflow",
    "feature engineering": "Feature Engineering",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "computer vision": "Computer Vision",
    "opencv": "Computer Vision",
    "llm": "NLP",
    "llms": "NLP",
    "large language models": "NLP",
    "onnx": "ONNX",
    "kubeflow": "Kubeflow",

    # Data & Analytics
    "sql": "SQL",
    "mysql": "SQL",
    "sqlite": "SQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "tableau": "Tableau",
    "power bi": "Power BI",
    "powerbi": "Power BI",
    "excel": "Excel",
    "ms excel": "Excel",
    "microsoft excel": "Excel",
    "data visualization": "Data Visualization",
    "data analysis": "Data Visualization",
    "matplotlib": "Data Visualization",
    "seaborn": "Data Visualization",
    "statistics": "Statistics",
    "statistical modeling": "Statistics",
    "a/b testing": "A/B Testing",
    "ab testing": "A/B Testing",
    "snowflake": "Snowflake",
    "bigquery": "Data Warehousing",
    "redshift": "Data Warehousing",
    "data warehousing": "Data Warehousing",
    "apache spark": "Apache Spark",
    "spark": "Apache Spark",
    "pyspark": "Apache Spark",
    "airflow": "Airflow",
    "apache airflow": "Airflow",
    "kafka": "Kafka",
    "apache kafka": "Kafka",
    "dbt": "dbt",
    "databricks": "Databricks",

    # Web & Full Stack
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "node": "Node.js",
    "express": "Node.js",
    "express.js": "Node.js",
    "expressjs": "Node.js",
    "fastapi": "FastAPI",
    "fast-api": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "rest apis": "REST APIs",
    "rest api": "REST APIs",
    "restful": "REST APIs",
    "restful api": "REST APIs",
    "graphql": "GraphQL",
    "html": "HTML5",
    "html5": "HTML5",
    "css": "CSS3",
    "css3": "CSS3",
    "tailwind": "Tailwind CSS",
    "tailwind css": "Tailwind CSS",
    "bootstrap": "Bootstrap",
    "mongodb": "MongoDB",
    "redis": "Redis",

    # DevOps, Cloud & Tools
    "docker": "Docker",
    "dockerfile": "Docker",
    "docker compose": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "linux": "Linux",
    "ubuntu": "Linux",
    "ci/cd": "CI/CD",
    "ci cd": "CI/CD",
    "continuous integration": "CI/CD",
    "continuous deployment": "CI/CD",
    "github actions": "CI/CD",
    "gitlab ci": "CI/CD",
    "jenkins": "CI/CD",
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "GCP",
    "google cloud": "GCP",
    "azure": "Azure",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "git": "Git",
    "github": "Git",
    "gitlab": "Git",
    "bash": "Bash",
    "shell scripting": "Bash",
    "prometheus": "Prometheus",
    "grafana": "Grafana",
    "argocd": "ArgoCD",

    # Core Programming Languages
    "c++": "C++",
    "cpp": "C++",
    "java": "Java",
    "golang": "Go",
    "go": "Go",
    "rust": "Rust",
    "c#": "C#",
    "scala": "Scala"
}


class NLPEngine:
    def __init__(self, role_db_path: Optional[str] = None):
        """Initializes the NLP engine with the role database and canonical taxonomy."""
        self.role_db_path = role_db_path or self._resolve_db_path()
        self.role_data: Dict[str, Any] = self._load_role_database()

    def _resolve_db_path(self) -> str:
        """Finds role_database.json across expected locations."""
        current_dir = Path(__file__).resolve().parent
        potential_paths = [
            current_dir / "role_database.json",
            current_dir.parent / "backend" / "role_database.json",
            Path.cwd() / "backend" / "role_database.json",
            Path.cwd() / "role_database.json"
        ]
        for p in potential_paths:
            if p.exists():
                return str(p)
        return str(current_dir / "role_database.json")

    def _load_role_database(self) -> Dict[str, Any]:
        """Loads target roles and required skills from JSON."""
        try:
            with open(self.role_db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception as e:
            # Fallback default roles if file read fails
            return {
                "roles": [
                    {
                        "id": "ai-engineer",
                        "title": "AI Engineer",
                        "category": "Artificial Intelligence",
                        "description": "Designs, builds, and deploys scalable AI applications and RAG systems.",
                        "required_skills": ["Python", "PyTorch", "FastAPI", "Docker", "NLP", "RAG", "LangChain", "Vector Databases", "Git"],
                        "preferred_skills": ["LlamaIndex", "Hugging Face", "MLflow", "Kubernetes"],
                        "capstone_project": "Build an Autonomous Multi-Document RAG Agent with FastAPI & Docker."
                    },
                    {
                        "id": "data-analyst",
                        "title": "Data Analyst",
                        "category": "Data & Analytics",
                        "description": "Extracts actionable insights via SQL, Python, and Tableau dashboards.",
                        "required_skills": ["SQL", "Excel", "Python", "Tableau", "Pandas", "Data Visualization", "Statistics"],
                        "preferred_skills": ["Power BI", "NumPy", "A/B Testing", "Snowflake"],
                        "capstone_project": "Build an Executive E-Commerce Cohort Analysis & Retention Dashboard."
                    }
                ]
            }

    def get_available_roles(self) -> List[Dict[str, Any]]:
        """Returns the list of available target roles."""
        return self.role_data.get("roles", [])

    def get_role_by_title_or_id(self, query: str) -> Optional[Dict[str, Any]]:
        """Look up role metadata by title (case-insensitive) or ID."""
        q = query.strip().lower()
        for role in self.get_available_roles():
            if role["title"].lower() == q or role.get("id", "").lower() == q:
                return role
        # Partial match fallback
        for role in self.get_available_roles():
            if q in role["title"].lower() or role["title"].lower() in q:
                return role
        return None

    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """
        Extracts clean plain text from uploaded PDF bytes.
        Uses pypdf as primary, PyPDF2 as fallback.
        """
        extracted_text = []

        # Attempt 1: pypdf
        if PYPDF_AVAILABLE:
            try:
                reader = pypdf.PdfReader(io.BytesIO(file_content))
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text.append(text)
                if extracted_text:
                    return self._clean_text("\n".join(extracted_text))
            except Exception:
                pass

        # Attempt 2: PyPDF2
        if PYPDF2_AVAILABLE:
            try:
                reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text.append(text)
                if extracted_text:
                    return self._clean_text("\n".join(extracted_text))
            except Exception:
                pass

        # Attempt 3: Direct text decode if it was an uploaded text file masquerading as bytes
        try:
            return self._clean_text(file_content.decode("utf-8", errors="ignore"))
        except Exception:
            return ""

    def _clean_text(self, text: str) -> str:
        """Normalizes text, strips carriage returns, non-ASCII artifacts, and extra whitespace."""
        if not text:
            return ""
        # Remove non-breaking spaces and irregular whitespace
        text = text.replace("\xa0", " ").replace("\r\n", "\n").replace("\r", "\n")
        # Collapse multiple spaces while preserving newlines
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()

    def extract_candidate_metadata(self, text: str) -> Dict[str, Optional[str]]:
        """Extracts candidate name, email, and phone number using NLP heuristics and regex."""
        metadata: Dict[str, Optional[str]] = {
            "name": None,
            "email": None,
            "phone": None
        }

        # 1. Email Regex
        email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        if email_match:
            metadata["email"] = email_match.group(0).strip()

        # 2. Phone Regex (International and standard formats)
        phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}", text)
        if phone_match:
            metadata["phone"] = phone_match.group(0).strip()

        # 3. Name heuristic (First 3 non-empty lines often contain the candidate's name)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:4]:
            # Skip lines with email or phone or headers
            if "@" in line or any(char.isdigit() for char in line) or len(line) > 40:
                continue
            if re.search(r"(resume|curriculum|vitae|page|contact|summary|profile)", line, re.I):
                continue
            # Plausible candidate name
            words = line.split()
            if 1 <= len(words) <= 4 and all(w[0].isupper() for w in words if w.isalpha()):
                metadata["name"] = line
                break

        # Fallback to spaCy PERSON entities if available and name still None
        if not metadata["name"] and nlp:
            doc = nlp(text[:500])
            for ent in doc.ents:
                if ent.label_ == "PERSON" and len(ent.text.split()) <= 4:
                    metadata["name"] = ent.text.strip()
                    break

        if not metadata["name"]:
            metadata["name"] = "Candidate"

        return metadata

    def extract_skills_from_text(self, text: str) -> Set[str]:
        """
        Extracts canonical skills from the provided text using multi-tier matching:
        1. Boundary-aware token and phrase regex matching against canonical skill taxonomy.
        2. Exact multi-word matching (e.g. 'Data Visualization', 'Vector Databases').
        3. spaCy linguistic token analysis.
        """
        extracted_canonical_skills: Set[str] = set()
        lowered_text = text.lower()

        # 1. Multi-word phrase matching first (longer matches prioritized)
        taxonomy_items = sorted(SKILL_TAXONOMY.items(), key=lambda x: len(x[0]), reverse=True)

        for alias, canonical in taxonomy_items:
            # Special regex escaping for symbols like C++, .NET, CI/CD
            escaped_alias = re.escape(alias)
            # Use word boundaries or start/end of line or punctuation boundaries
            pattern = rf"(?<![a-zA-Z0-9_]){escaped_alias}(?![a-zA-Z0-9_])"
            if re.search(pattern, lowered_text):
                extracted_canonical_skills.add(canonical)

        # 2. Tokenized validation via spaCy if available
        if nlp:
            doc = nlp(text[:8000])  # limit to first 8000 chars for efficiency
            for token in doc:
                t_lower = token.text.lower()
                if t_lower in SKILL_TAXONOMY:
                    extracted_canonical_skills.add(SKILL_TAXONOMY[t_lower])

        return extracted_canonical_skills

    def analyze_skill_gap(
        self,
        resume_text: str,
        target_role_query: str
    ) -> Dict[str, Any]:
        """
        Executes end-to-end skill gap analysis:
        1. Extract candidate skills.
        2. Fetch target role required & preferred skills.
        3. Calculate Matched Skills, Missing Skills (The Gap), and Additional Skills.
        4. Compute Match Percentage and Readiness Level.
        5. Generate personalized BitElevate learning roadmap.
        """
        role_meta = self.get_role_by_title_or_id(target_role_query)
        if not role_meta:
            raise ValueError(f"Role '{target_role_query}' not found in role database.")

        candidate_meta = self.extract_candidate_metadata(resume_text)
        extracted_skills = self.extract_skills_from_text(resume_text)

        required_skills = set(role_meta.get("required_skills", []))
        preferred_skills = set(role_meta.get("preferred_skills", []))

        # Skill Gap logic: Set operations
        matched_skills = sorted(list(required_skills.intersection(extracted_skills)))
        missing_skills = sorted(list(required_skills - extracted_skills))
        
        # Preferred skills matched
        matched_preferred = sorted(list(preferred_skills.intersection(extracted_skills)))
        missing_preferred = sorted(list(preferred_skills - extracted_skills))

        # Additional candidate skills outside target role
        all_role_skills = required_skills.union(preferred_skills)
        additional_skills = sorted(list(extracted_skills - all_role_skills))

        # Match calculation
        total_required = len(required_skills)
        match_count = len(matched_skills)
        
        if total_required > 0:
            match_percentage = round((match_count / total_required) * 100, 1)
        else:
            match_percentage = 0.0

        # Readiness classification
        if match_percentage >= 80:
            readiness_level = "Job Ready (High Match)"
            readiness_color = "green"
            verdict = "Excellent alignment! The candidate demonstrates the majority of core competencies required for this role."
        elif match_percentage >= 60:
            readiness_level = "Minor Gap (Competitive Candidate)"
            readiness_color = "blue"
            verdict = "Strong foundation! With a targeted 2 to 4-week upskilling sprint, candidate can reach full job readiness."
        elif match_percentage >= 40:
            readiness_level = "Moderate Gap (Upskilling Recommended)"
            readiness_color = "amber"
            verdict = "Partial alignment. Key technical skills are missing and recommended before interview shortlisting."
        else:
            readiness_level = "Foundational Gap (Extensive Training Needed)"
            readiness_color = "red"
            verdict = "Significant skill deficit. Candidate would benefit from a comprehensive BitElevate career transition track."

        # Generate Personalized Learning Roadmap for missing skills
        learning_map = role_meta.get("skill_learning_map", {})
        learning_path: List[Dict[str, Any]] = []
        total_estimated_weeks = 0

        for missing in missing_skills:
            if missing in learning_map:
                item = learning_map[missing].copy()
                item["skill"] = missing
                learning_path.append(item)
                total_estimated_weeks += item.get("estimated_weeks", 2)
            else:
                learning_path.append({
                    "skill": missing,
                    "module_title": f"Mastery of {missing}",
                    "description": f"Hands-on architectural and practical implementation of {missing}.",
                    "estimated_weeks": 2,
                    "difficulty": "Intermediate",
                    "recommended_cynbit_course": f"BitElevate: {missing} Professional Certificate"
                })
                total_estimated_weeks += 2

        # Sort learning path by difficulty (Beginner -> Intermediate -> Advanced)
        difficulty_order = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
        learning_path.sort(key=lambda x: difficulty_order.get(x.get("difficulty", "Intermediate"), 2))

        return {
            "status": "success",
            "candidate_metadata": candidate_meta,
            "target_role": {
                "id": role_meta.get("id"),
                "title": role_meta.get("title"),
                "category": role_meta.get("category"),
                "description": role_meta.get("description"),
                "capstone_project": role_meta.get("capstone_project")
            },
            "metrics": {
                "match_percentage": match_percentage,
                "readiness_level": readiness_level,
                "readiness_color": readiness_color,
                "matched_count": len(matched_skills),
                "total_required": total_required,
                "missing_count": len(missing_skills),
                "matched_preferred_count": len(matched_preferred),
                "estimated_upskill_weeks": total_estimated_weeks
            },
            "skills_breakdown": {
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "matched_preferred_skills": matched_preferred,
                "missing_preferred_skills": missing_preferred,
                "additional_skills": additional_skills,
                "all_extracted_skills": sorted(list(extracted_skills))
            },
            "recommendations": {
                "verdict": verdict,
                "learning_path": learning_path,
                "total_estimated_weeks": total_estimated_weeks,
                "recommended_capstone": role_meta.get("capstone_project"),
                "recommended_cynbit_tracks": list({
                    item.get("recommended_cynbit_course")
                    for item in learning_path
                    if item.get("recommended_cynbit_course")
                })
            },
            "raw_text_length": len(resume_text),
            "text_preview": resume_text[:300] + ("..." if len(resume_text) > 300 else "")
        }
