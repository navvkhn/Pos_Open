from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Table,
    TableStyle,
    Image,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
import io
from supabase_client import supabase
import requests

def generate_bill_pdf(order_id):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()
    elements = []

    # --------------------------------------------------
    # Fetch data
    # --------------------------------------------------
    order = supabase.table("orders") \
        .select("*") \
        .eq("id", order_id) \
        .single() \
        .execute()

    tenant = supabase.table("tenants") \
        .select("*") \
        .eq("id", order.data["tenant_id"]) \
        .single() \
        .execute()

    items = supabase.table("order_items") \
        .select("*") \
        .eq("order_id", order_id) \
        .execute()

    # --------------------------------------------------
    # Logo
    # --------------------------------------------------
    if tenant.data.get("logo_url"):
        try:
            img_data = requests.get(tenant.data["logo_url"]).content
            logo = Image(io.BytesIO(img_data), width=50*mm, height=20*mm)
            logo.hAlign = "CENTER"
            elements.append(logo)
            elements.append(Spacer(1, 10))
        except:
            pass

    # --------------------------------------------------
    # Cafe Name
    # --------------------------------------------------
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        alignment=1,
        fontSize=18,
        spaceAfter=10
    )
    elements.append(Paragraph(tenant.data["name"], title_style))

    elements.append(Spacer(1, 5))

    # --------------------------------------------------
    # Invoice Meta
    # --------------------------------------------------
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        alignment=1,
        fontSize=10
    )

    elements.append(Paragraph(f"Invoice No: {order_id}", meta_style))
    elements.append(Paragraph("Thank you for dining with us!", meta_style))
    elements.append(Spacer(1, 15))

    # --------------------------------------------------
    # Items Table
    # --------------------------------------------------
    table_data = [["Item", "Qty", "Amount (₹)"]]

    for item in items.data:
        table_data.append([
            item["product_name"],
            str(item["quantity"]),
            f"{item['price']:.2f}"
        ])

    table = Table(table_data, colWidths=[90*mm, 25*mm, 35*mm])
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.8, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("ALIGN", (1,1), (-1,-1), "CENTER"),
        ("FONT", (0,0), (-1,0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,0), 8),
        ("TOPPADDING", (0,0), (-1,0), 8),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 15))

    # --------------------------------------------------
    # Totals
    # --------------------------------------------------
    totals_data = [
        ["Subtotal", f"₹ {order.data['total'] + order.data.get('discount_amount', 0):.2f}"],
    ]

    if order.data.get("discount_amount", 0) > 0:
        totals_data.append(
            ["Discount", f"- ₹ {order.data['discount_amount']:.2f}"]
        )

    totals_data.append(
        ["Total Payable", f"₹ {order.data['total']:.2f}"]
    )

    totals_table = Table(totals_data, colWidths=[115*mm, 35*mm])
    totals_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.8, colors.black),
        ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ("FONT", (-1,-1), (-1,-1), "Helvetica-Bold"),
        ("BACKGROUND", (-1,-1), (-1,-1), colors.lightgrey),
    ]))

    elements.append(totals_table)
    elements.append(Spacer(1, 20))

    # --------------------------------------------------
    # Footer
    # --------------------------------------------------
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        alignment=1,
        fontSize=9,
        textColor=colors.grey
    )

    if tenant.data.get("address"):
        elements.append(Paragraph(tenant.data["address"], footer_style))

    if tenant.data.get("contact"):
        elements.append(Paragraph(f"Contact: {tenant.data['contact']}", footer_style))

    elements.append(Paragraph("Follow us on Instagram 📸 @yourcafename", footer_style))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph("Powered by Superscale POS", footer_style))

    # --------------------------------------------------
    # Build PDF
    # --------------------------------------------------
    doc.build(elements)
    buffer.seek(0)
    return buffer
