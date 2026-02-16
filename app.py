from flask import send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import io
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors


from flask import Flask, render_template, request

app = Flask(__name__)

SLABS = [
    (100, 10),
    (100, 15),
    (300, 20),
    (float("inf"), 25)
]

def calculate_bill(units):
    remaining = units
    energy_total = 0
    breakdown = []

    for limit, rate in SLABS:
        if remaining <= 0:
            break

        used = min(remaining, limit)
        cost = used * rate

        breakdown.append((used, rate, cost))
        energy_total += cost
        remaining -= used

    fixed_charge = 750
    vat = energy_total * 0.075
    grand_total = energy_total + vat + fixed_charge

    return energy_total, vat, fixed_charge, grand_total, breakdown


@app.route("/", methods=["GET", "POST"])
def home():

    energy_total = None
    vat = None
    fixed_charge = None
    grand_total = None
    breakdown = None
    message = None
    error = None

    if request.method == "POST":
        try:
            units = float(request.form["units"])
            if units < 0:
                raise ValueError

            energy_total, vat, fixed_charge, grand_total, breakdown = calculate_bill(units)
            message = "Bill calculated successfully."

        except ValueError:
            error = "Please enter a valid positive number."

    return render_template(
        "index.html",
        energy_total=energy_total,
        vat=vat,
        fixed_charge=fixed_charge,
        grand_total=grand_total,
        breakdown=breakdown,
        message=message,
        error=error
    )

@app.route("/download_pdf")
def download_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    title_style = styles["Heading1"]

    energy_total = request.args.get("energy_total", "0")
    vat = request.args.get("vat", "0")
    fixed_charge = request.args.get("fixed_charge", "0")
    grand_total = request.args.get("grand_total", "0")

    # ===== COMPANY HEADER =====
    elements.append(Paragraph("<b>POWERBILL PRO LTD</b>", title_style))
    elements.append(Paragraph("Electricity Billing & Energy Solutions", normal))
    elements.append(Paragraph("Email: support@powerbillpro.com", normal))
    elements.append(Paragraph("Phone: +234-000-000-0000", normal))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<b>INVOICE</b>", styles["Heading2"]))
    elements.append(Spacer(1, 15))

    # ===== BILL TABLE =====
    data = [
        ["Description", "Amount (₦)"],
        ["Energy Charge", energy_total],
        ["VAT (7.5%)", vat],
        ["Fixed Charge", fixed_charge],
        ["Total Payable", grand_total],
    ]

    table = Table(data, colWidths=[250, 150])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    ]))

    elements.append(table)

    elements.append(Spacer(1, 40))
    elements.append(Paragraph("Prepared by Okechukwu Favour", normal))

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="PowerBill_Invoice.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    app.run(debug=True)
