import time
import requests
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# 1. Create a sample research paper PDF
sample_pdf = Path("sample_research_paper.pdf")
try:
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page()
    content = """Attention Mechanisms and Multi-Task Loss Objectives
Vaswani, Goodfellow, Bengio et al. - Research Lab

Abstract
This work presents mathematical derivations of scaled dot-product attention and multi-task loss.
We resolve intermediate algebraic transitions skipped in standard literature.

1. Model Architecture
Scaled dot-product attention maps query and key-value pairs to output representations.
Attention(Q, K, V) = softmax(QK^T / sqrt(d_k))V

2. Multi-Task Objective
The combined loss objective optimizes classification and regression jointly.
L_total = alpha * L_cls + beta * L_reg
"""
    page.insert_text((72, 72), content, fontsize=12)
    doc.save(str(sample_pdf))
    doc.close()
except ImportError:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(str(sample_pdf), pagesize=letter)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, 740, "Attention Mechanisms and Multi-Task Loss Objectives")
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(72, 720, "Vaswani, Goodfellow, Bengio et al. - Research Lab")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, 690, "Abstract")
    c.setFont("Helvetica", 10)
    c.drawString(72, 675, "This work presents mathematical derivations of scaled dot-product attention and multi-task loss.")
    c.drawString(72, 660, "We resolve intermediate algebraic transitions skipped in standard literature.")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, 630, "1. Model Architecture")
    c.setFont("Helvetica", 10)
    c.drawString(72, 615, "Scaled dot-product attention maps query and key-value pairs to output representations.")
    c.setFont("Courier", 10)
    c.drawString(72, 595, "Attention(Q, K, V) = softmax(QK^T / sqrt(d_k))V")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, 560, "2. Multi-Task Objective")
    c.setFont("Helvetica", 10)
    c.drawString(72, 545, "The combined loss objective optimizes classification and regression jointly.")
    c.setFont("Courier", 10)
    c.drawString(72, 525, "L_total = alpha * L_cls + beta * L_reg")
    c.save()

print("Created sample_research_paper.pdf")

# 2. Upload via POST /api/v1/papers/upload
with open(sample_pdf, "rb") as f:
    files = {"file": ("sample_research_paper.pdf", f, "application/pdf")}
    res = requests.post("http://127.0.0.1:8000/api/v1/papers/upload", files=files)
    print("Upload status:", res.status_code)
    upload_data = res.json()
    print("Upload data:", upload_data)

paper_id = upload_data["paper_id"]
job_id = upload_data["job_id"]

# 3. Poll job until completion
for i in range(20):
    time.sleep(0.5)
    job_res = requests.get(f"http://127.0.0.1:8000/api/v1/jobs/{job_id}")
    job = job_res.json()
    print(f"Polling job {job['progress']}% - stage: {job.get('stage')} - status: {job['status']}")
    if job["status"] in ("completed", "failed"):
        break

# 4. Fetch the analyzed paper
paper_res = requests.get(f"http://127.0.0.1:8000/api/v1/papers/{paper_id}")
data = paper_res.json()
print("Paper Title:", data["paper"]["title"])
print("Equations Count:", len(data["equations"]))
print("Symbols Count:", len(data["symbols"]))
print("Artifacts Keys:", list(data["artifacts"].keys()) if data.get("artifacts") else "None")

for idx, eq in enumerate(data["equations"]):
    print(f"\n--- Equation {idx + 1}: {eq.get('paper_section')} ---")
    print("Latex:", eq.get("official_latex"))
    print("Conceptual Summary:", eq.get("conceptual_summary"))
    print("Steps count:", len(eq.get("step_by_step_derivation", [])))
    print("SymPy Verified:", eq.get("verification_note"))
