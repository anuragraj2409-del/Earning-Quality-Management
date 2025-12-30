from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_file
import pandas as pd
from analytics import analyze_entity
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

app = Flask(
    __name__,
    template_folder="../Frontend/templates",
    static_folder="../Frontend/Static"
)


# REQUIRED for login sessions
app.secret_key = "vigilance-secret-key"

# -------------------------------------------------
# LOGIN & AUTHENTICATION
# -------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Demo credentials
        if username == "admin" and password == "admin123":
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------

@app.route("/")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

# -------------------------------------------------
# ANALYSIS API
# -------------------------------------------------

@app.route("/analyze", methods=["POST"])
def analyze():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    try:
        # Read ALL sheets (supports Benford and Data Sheet extraction)
        workbook = pd.read_excel(file, sheet_name=None)
    except Exception:
        return jsonify({"error": "Invalid Excel file"}), 400

    # Locate the primary data sheet
    data_sheet = workbook.get("Data Sheet", list(workbook.values())[0])

    # Run the forensic engine
    result = analyze_entity(
        df_data_sheet=data_sheet,
        workbook_dict=workbook,
        entity_name=file.filename.split(".")[0]
    )

    return jsonify(result)

# -------------------------------------------------
# PDF EXPORT (COMPREHENSIVE SAAS REPORT)
# -------------------------------------------------

@app.route("/export-pdf", methods=["POST"])
def export_pdf():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

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
    
    # Verdict Highlight
    signal = data.get('earnings_manipulation_signal', 'LOW')
    verdict_color = colors.red if signal == "HIGH" else colors.green
    c.setFillColor(verdict_color)
    c.drawString(50, height - 130, f"Manipulation Risk: {signal}")
    
    c.setFillColor(colors.black)
    c.line(50, height - 145, width - 50, height - 145)

    # Section 1: Forensic Scores
    y = height - 180
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Key Forensic Indicators")
    y -= 25
    
    c.setFont("Helvetica", 11)
    forensic_lines = [
        f"Beneish M-Score: {data.get('beneish_m_score', 'N/A')}",
        f"Accruals Gap: {data.get('accruals_gap', 'N/A')}%",
        f"Tax Discrepancy Gap: {data.get('tax_gap', 'N/A')}%",
        f"Debt/Asset Stress Ratio: {data.get('debt_asset_stress', 'N/A')}%",
        f"Revenue vs Cash Flow Quality: {data.get('cash_quality', 'N/A')}%"
    ]
    
    for line in forensic_lines:
        c.drawString(60, y, f"• {line}")
        y -= 18

    # Section 2: Raw Financial Extraction (Data Explorer View)
    y -= 20
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Extracted Financial Values")
    y -= 25
    
    c.setFont("Helvetica", 11)
    raw_values = [
        f"Reported Revenue: {data.get('revenue', 0):,.2f}",
        f"Trade Receivables: {data.get('receivables', 0):,.2f}",
        f"Total Calculated Assets: {data.get('total_assets', 0):,.2f}",
        f"Operating Cash Flow (OCF): {data.get('ocf', 0):,.2f}",
        f"Total Borrowings: {data.get('borrowings', 0):,.2f}"
    ]
    
    for val in raw_values:
        c.drawString(60, y, f"• {val}")
        y -= 18

    # Footer/Note
    y -= 40
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.grey)
    notes = [
        "This report is generated by the Vigilance AI Forensic Engine.",
        "Analysis is based on automated extraction; please verify raw values in the Data Explorer tab.",
        "A 'HIGH' risk signal suggests the need for a manual investigative audit."
    ]
    for note in notes:
        c.drawString(50, y, note)
        y -= 12

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
# RUN SERVER
# -------------------------------------------------

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
