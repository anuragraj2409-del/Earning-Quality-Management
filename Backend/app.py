from flask import Flask, request, jsonify, render_template, send_file
import pandas as pd
from analytics import analyze_entity
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import os

app = Flask(
    __name__,
    template_folder="../Frontend/templates",
    static_folder="../Frontend/Static"
)

# -------------------------------------------------
# DASHBOARD (NO LOGIN)
# -------------------------------------------------

@app.route("/")
def dashboard():
    return render_template("index.html")

# -------------------------------------------------
# ANALYSIS API
# -------------------------------------------------

@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    try:
        # Read ALL sheets
        workbook = pd.read_excel(file, sheet_name=None)
    except Exception:
        return jsonify({"error": "Invalid Excel file"}), 400

    # Primary data sheet
    data_sheet = workbook.get("Data Sheet", list(workbook.values())[0])

    result = analyze_entity(
        df_data_sheet=data_sheet,
        workbook_dict=workbook,
        entity_name=file.filename.split(".")[0]
    )

    return jsonify(result)

# -------------------------------------------------
# PDF EXPORT
# -------------------------------------------------

@app.route("/export-pdf", methods=["POST"])
def export_pdf():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    c.setFillColor(colors.HexColor("#0f172a"))
    c.rect(0, height - 80, width, 80, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 45, "Earnings Quality Management – Forensic Audit")

    # Entity Info
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 110, f"Entity Name: {data.get('name', 'N/A')}")

    signal = data.get("earnings_manipulation_signal", "LOW")
    verdict_color = colors.red if signal == "HIGH" else colors.green
    c.setFillColor(verdict_color)
    c.drawString(50, height - 130, f"Manipulation Risk: {signal}")

    c.setFillColor(colors.black)
    c.line(50, height - 145, width - 50, height - 145)

    y = height - 180
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Key Forensic Indicators")
    y -= 25

    c.setFont("Helvetica", 11)
    indicators = [
        f"Beneish M-Score: {data.get('beneish_m_score', 'N/A')}",
        f"Accruals Gap: {data.get('accruals_gap', 'N/A')}%",
        f"Tax Gap: {data.get('tax_gap', 'N/A')}%",
        f"Debt / Asset Stress: {data.get('debt_asset_stress', 'N/A')}%",
        f"Cash Flow Quality: {data.get('cash_quality', 'N/A')}%"
    ]

    for i in indicators:
        c.drawString(60, y, f"• {i}")
        y -= 18

    c.showPage()
    c.save()

    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Forensic_Report_{data.get('name', 'Audit')}.pdf",
        mimetype="application/pdf"
    )

# -------------------------------------------------
# ENTRY POINT
# -------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
