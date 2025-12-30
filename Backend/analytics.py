import numpy as np
import math

# -------------------------------------------------
# BENFORD'S LAW — ALL SHEETS
# -------------------------------------------------

def calculate_benford_from_workbook(workbook):
    nums = []

    for df in workbook.values():
        for v in df.values.flatten():
            try:
                n = abs(float(str(v).replace(",", "").strip()))
                if n >= 1:
                    nums.append(n)
            except:
                continue

    if not nums:
        return None

    digits = [int(str(n).replace(".", "").lstrip("0")[0]) for n in nums]
    counts = np.bincount(digits, minlength=10)[1:]
    total = counts.sum()

    actual = (counts / total) * 100
    theoretical = [math.log10(1 + 1 / d) * 100 for d in range(1, 10)]
    mad = np.mean(np.abs(actual / 100 - np.array(theoretical) / 100))

    return {
        "actual": actual.tolist(),
        "theoretical": theoretical,
        "mad": round(mad, 5),
        "hotspot": int(np.argmax(np.abs(actual - theoretical)) + 1)
    }

# -------------------------------------------------
# ROBUST HELPERS
# -------------------------------------------------

def get_single_value(df, keywords):
    for _, row in df.iterrows():
        label = str(row.iloc[0]).lower()
        if any(k in label for k in keywords):
            for v in row.iloc[1:]:
                try:
                    n = float(str(v).replace(",", "").strip())
                    if not math.isnan(n):
                        return n
                except:
                    continue
    return 0.0


def get_sum_value(df, keywords):
    total = 0.0
    for _, row in df.iterrows():
        label = str(row.iloc[0]).lower()
        if any(k in label for k in keywords):
            for v in row.iloc[1:]:
                try:
                    n = float(str(v).replace(",", "").strip())
                    if not math.isnan(n):
                        total += n
                        break
                except:
                    continue
    return total

# -------------------------------------------------
# MAIN FORENSIC ANALYSIS
# -------------------------------------------------

def analyze_entity(df_data_sheet, workbook_dict, entity_name):

    # ---- CORE METRICS EXTRACTION ----

    sales = get_single_value(df_data_sheet, [
        "revenue", "revenue from operations", "sales"
    ])

    receivables = get_single_value(df_data_sheet, [
        "receivables", "trade receivables", "debtors"
    ])

    total_assets = get_single_value(df_data_sheet, [
        "total assets",
        "total",
        "total assets (a)",
        "total assets as at",
        "total (assets)",
        "non-current assets",
        "current assets"
    ])

    borrowings = get_sum_value(df_data_sheet, [
        "borrowings",
        "total borrowings",
        "loans",
        "debt"
    ])

    tax = get_single_value(df_data_sheet, [
        "tax", "current tax", "provision for tax"
    ])

    pbt = get_single_value(df_data_sheet, [
        "profit before tax", "pbt"
    ])

    ocf = get_single_value(df_data_sheet, [
        "cash from operating", "cash flow from operating", "net cash from operating"
    ])

    # ---- BENEISH M-SCORE (SIMPLIFIED) ----

    dsri = (receivables / sales) if sales else 0
    beneish_m_score = -4.84 + (0.92 * dsri)

    # ---- ACCRUALS GAP ----

    accruals_gap = ((sales - ocf) / sales) * 100 if sales else 0

    # ---- TAX GAP ----

    tax_rate = (tax / pbt) * 100 if pbt else 0
    tax_gap = abs(25 - tax_rate)

    # ---- DEBT / ASSET STRESS ----

    debt_asset_stress = (borrowings / total_assets) * 100 if total_assets else 0

    # ---- REVENUE vs CASH QUALITY ----

    cash_quality = (ocf / sales) * 100 if sales else 0

    # ---- BENFORD ANALYTICS ----

    benford = calculate_benford_from_workbook(workbook_dict)

    # ---- FINAL MANIPULATION SIGNAL LOGIC ----

    red_flags = 0
    if beneish_m_score > -1.78:
        red_flags += 1
    if accruals_gap > 25:
        red_flags += 1
    if tax_gap > 10:
        red_flags += 1
    if benford and benford["mad"] > 0.012:
        red_flags += 1

    earnings_manipulation_signal = "HIGH" if red_flags >= 2 else "LOW"

    return {
        "name": entity_name.upper(),

        # Forensic Scores for Dashboard
        "beneish_m_score": round(beneish_m_score, 2),
        "accruals_gap": round(accruals_gap, 1),
        "tax_gap": round(tax_gap, 1),
        "debt_asset_stress": round(debt_asset_stress, 1),
        "cash_quality": round(cash_quality, 1),

        # Comprehensive Raw Financial Values for Data Explorer
        "revenue": round(sales, 2),
        "total_assets": round(total_assets, 2),
        "ocf": round(ocf, 2),
        "receivables": round(receivables, 2),
        "borrowings": round(borrowings, 2),
        "tax_paid": round(tax, 2),
        "pbt": round(pbt, 2),

        "earnings_manipulation_signal": earnings_manipulation_signal,
        "benford": benford
    }