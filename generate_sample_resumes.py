"""
Generate Sample Resumes in PDF format for testing BitElevate Skill Gap Analyzer.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from pathlib import Path


def create_resume_pdf(filename: str, name: str, title: str, contact: str, summary: str, skills: list, experience: list, education: str):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    styles = getSampleStyleSheet()

    # Custom styles
    header_style = ParagraphStyle(
        'ResumeHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A')
    )
    subtitle_style = ParagraphStyle(
        'ResumeSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#4F46E5')
    )
    contact_style = ParagraphStyle(
        'ResumeContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#64748B')
    )
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'ResumeBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#334155')
    )
    bullet_style = ParagraphStyle(
        'ResumeBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155'),
        leftIndent=12
    )

    story = []

    # Header
    story.append(Paragraph(name, header_style))
    story.append(Paragraph(title, subtitle_style))
    story.append(Paragraph(contact, contact_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#E2E8F0'), spaceBefore=2, spaceAfter=10))

    # Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", section_title_style))
    story.append(Paragraph(summary, body_style))
    story.append(Spacer(1, 10))

    # Skills
    story.append(Paragraph("TECHNICAL SKILLS", section_title_style))
    skills_text = " • ".join(skills)
    story.append(Paragraph(skills_text, body_style))
    story.append(Spacer(1, 10))

    # Experience
    story.append(Paragraph("PROFESSIONAL EXPERIENCE", section_title_style))
    for exp in experience:
        story.append(Paragraph(f"<b>{exp['role']}</b> | {exp['company']} <i>({exp['period']})</i>", body_style))
        for point in exp['points']:
            story.append(Paragraph(f"• {point}", bullet_style))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 4))
    # Education
    story.append(Paragraph("EDUCATION", section_title_style))
    story.append(Paragraph(education, body_style))

    doc.build(story)
    print(f"Generated: {filename}")


def main():
    output_dir = Path(__file__).resolve().parent / "sample_resumes"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. AI Engineer Sample Resume (Alex Chen)
    create_resume_pdf(
        str(output_dir / "alex_chen_ai_engineer.pdf"),
        name="Alex Chen",
        title="Senior AI Engineer | Generative AI & LLM Systems",
        contact="alex.chen@cynbit-demo.com | +1 (555) 234-8901 | San Francisco, CA | github.com/alexchen-ai",
        summary="Results-driven AI Engineer with 4+ years of experience designing and deploying scalable deep learning architectures, Retrieval-Augmented Generation (RAG) pipelines, and autonomous LLM agents in production environments. Proficient in PyTorch, FastAPI, Vector Databases, and Dockerized microservices.",
        skills=[
            "Python", "PyTorch", "FastAPI", "Docker", "RAG", "LangChain", 
            "Vector Databases (ChromaDB, Pinecone)", "Git", "Hugging Face", 
            "Natural Language Processing (NLP)", "MLflow", "REST APIs", "PostgreSQL"
        ],
        experience=[
            {
                "role": "AI Systems Engineer",
                "company": "NeuralScale Tech",
                "period": "2023 - Present",
                "points": [
                    "Architected enterprise RAG system with LangChain and Pinecone vector databases, cutting support ticket resolution time by 48%.",
                    "Built asynchronous microservices in FastAPI and Docker serving PyTorch neural embeddings with <45ms p99 latency.",
                    "Implemented CI/CD pipelines with Git and Docker for automated model benchmarking and zero-downtime deployment."
                ]
            },
            {
                "role": "Machine Learning Associate",
                "company": "Cognitive Cloud Labs",
                "period": "2021 - 2023",
                "points": [
                    "Trained and fine-tuned Transformer-based NLP models using Hugging Face and PyTorch on multi-GPU nodes.",
                    "Integrated MLflow for experiment tracking, hyperparameter optimization, and model artifact governance.",
                    "Developed Python ETL scripts processing 15M+ text documents for downstream retrieval tasks."
                ]
            }
        ],
        education="<b>B.S. in Computer Science</b> — University of California, Berkeley (2017 - 2021)"
    )

    # 2. Data Analyst Sample Resume (Priya Sharma)
    create_resume_pdf(
        str(output_dir / "priya_sharma_data_analyst.pdf"),
        name="Priya Sharma",
        title="Senior Data Analyst | Business Intelligence & Analytics",
        contact="priya.sharma@cynbit-demo.com | +91 98765 43210 | Bengaluru, India | linkedin.com/in/priyasharma-data",
        summary="Detail-oriented Data Analyst with 3.5 years of experience delivering high-impact business insights, executive Tableau dashboards, and automated SQL reporting pipelines. Specialized in statistical modeling, cohort retention analysis, and large-scale tabular wrangling using Python and Pandas.",
        skills=[
            "SQL", "Python", "Tableau", "Pandas", "NumPy", "Excel (Advanced / Power Query)", 
            "Data Visualization", "Statistics", "Power BI", "A/B Testing", "PostgreSQL", "Git"
        ],
        experience=[
            {
                "role": "Lead Business Data Analyst",
                "company": "FinMetrix Global",
                "period": "2022 - Present",
                "points": [
                    "Engineered interactive Tableau and Power BI executive dashboards monitoring $20M+ MRR across 12 product lines.",
                    "Executed complex analytical SQL queries (window functions, CTEs) on PostgreSQL data warehouses to reduce customer churn by 14%.",
                    "Developed automated Python and Pandas pipelines to replace manual weekly Excel reporting, saving 18 engineering hours weekly."
                ]
            },
            {
                "role": "Junior Data Analyst",
                "company": "RetailPulse Insights",
                "period": "2020 - 2022",
                "points": [
                    "Conducted inferential statistical analysis and A/B testing evaluation for marketing campaign optimization.",
                    "Created advanced Excel financial models utilizing Power Query, XLOOKUP, and dynamic sensitivity tables.",
                    "Collaborated with cross-functional stakeholders to define core product KPIs and visual storytelling standards."
                ]
            }
        ],
        education="<b>B.Tech in Information Technology</b> — National Institute of Technology, Karnataka (2016 - 2020)"
    )

    # 3. Fresher / Web Developer Sample Resume (Rohit Verma)
    create_resume_pdf(
        str(output_dir / "rohit_verma_fresher.pdf"),
        name="Rohit Verma",
        title="Junior Software Developer / Recent Graduate",
        contact="rohit.verma@cynbit-demo.com | +91 91234 56789 | New Delhi, India | github.com/rohitverma-dev",
        summary="Enthusiastic and eager Computer Science graduate with strong foundational knowledge in Java, C++, HTML5, CSS3, and JavaScript. Seeking an entry-level software engineering role to leverage problem-solving capabilities and modern full-stack development skills.",
        skills=[
            "JavaScript", "HTML5", "CSS3", "Java", "C++", "Git", "REST APIs", "MySQL", "Bootstrap"
        ],
        experience=[
            {
                "role": "Web Development Intern",
                "company": "PixelCraft Studios",
                "period": "Summer 2023 (6 Months)",
                "points": [
                    "Designed and maintained responsive client landing pages using HTML5, CSS3, and modern JavaScript.",
                    "Integrated RESTful API endpoints for user authentication and submitted code reviews using Git and GitHub.",
                    "Assisted in database schema migrations and basic SQL querying for customer record management."
                ]
            },
            {
                "role": "Academic Project Lead",
                "company": "College Capstone Project",
                "period": "2023 - 2024",
                "points": [
                    "Developed an Online Student Management Portal using Java, MySQL, and HTML/CSS.",
                    "Implemented form validation, database CRUD operations, and session management."
                ]
            }
        ],
        education="<b>B.E. in Computer Science & Engineering</b> — Delhi Technological University (DTU) (2020 - 2024)"
    )


if __name__ == "__main__":
    main()
