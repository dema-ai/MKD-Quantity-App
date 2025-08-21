\# Ethical Construction Quantity Takeoff App (Ethiopian Standards)



\## Purpose

This tool assists in generating \*\*transparent, auditable\*\* quantities and BoQs from construction drawings, tailored to Ethiopian unit conventions, material specs, and labor rates.



\### Scope

\- Assistive AI detection for drawing elements (walls, openings, etc.)

\- Deterministic formula engine for all quantity and cost calculations

\- Full traceability from source drawing → detected element → quantity → rate → BoQ

\- Offline-first, privacy by design



\### Non‑Goals

\- Does \*\*not\*\* replace professional review or sign-off

\- Does \*\*not\*\* provide legal building code approval

\- No AI “black box” calculations for contract-critical outputs



---



\## Ethical Principles

1\. \*\*Transparency\*\* – Every quantity is linked to its formula, assumptions, and data source.

2\. \*\*Data Privacy\*\* – All processing is local by default; project files are encrypted at rest.

3\. \*\*Consent\*\* – Only process drawings with confirmed rights or permissions.

4\. \*\*IP Compliance\*\* – Use only permissively licensed dependencies, with attribution.

5\. \*\*Human Oversight\*\* – Final BoQ requires professional approval.



---



\## MVP Features

\- PDF/DWG → image conversion

\- Scale calibration (two-point or title block)

\- Classical CV wall/edge detection with editable overlays

\- Transparent quantity formulas (m², m³, ETB cost)

\- BoQ export with assumptions log + audit trail



---



\## Stack

\- \*\*Language:\*\* Python

\- \*\*UI:\*\* PyQt5 or Flask (local web)

\- \*\*Libraries:\*\* OpenCV, Tesseract, Pandas, ReportLab



---



\## Quick Start

```bash

git clone <repo-url>

cd quantity-app

pip install -r requirements.txt

python app/main.py

