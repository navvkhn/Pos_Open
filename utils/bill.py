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
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
import io
import requests
from supabase_client import supabase


def generate_bill_pdf(order_id):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    styles = getSampleStyleSheet()
    elements = []

    # --------------------------------------------------
    # 🧾 FETCH ORDER (SAFE)
    # --------------------------------------------------
    order_res = supabase.table("orders") \
        .select("*") \
        .eq("id", order_id) \
        .limit(1) \
        .execute()

    if not order_res.data:
        elements.append(Paragraph("Order not found", styles["Normal"]))
        doc.build(elements)
        buffer.seek(0)
        return buffer

    order = order_res.data[0]

    # --------------------------------------------------
    # 🏪 FETCH TENANT (SAFE)
    # --------------------------------------------------
    tenant_res = supabase.table("tenants") \
        .select("*") \
        .eq("id", order["tenant_id"]) \
        .limit(1) \
        .execute()

    tenant = tenant_res.data[0] if tenant_res.data else {}

    # --------------------------------------------------
    # 🍽 FETCH ITEMS
    # --------------------------------------------------
    items = supabase.table("order_items") \
        .select("*") \
        .eq("order_id", order_id) \
        .execute()

    # --------------------------------------------------
    # 🎨 BRANDING
    # --------------------------------------------------
    primary_color = HexColor(tenant.get("primary_color", "#000000"))

    # --------------------------------------------------
    # 🖼 LOGO
    # --------------------------------------------------
    if tenant.get("logo_url"):
        try:
            img_data = requests.get(tenant["logo_url"], timeout=5).content
            logo = Image(io.BytesIO(img_data), width=45 * mm, height=18 * mm)
            logo.hAlign = "CENTER"
            elements.append(logo)
            elements.append(Spacer(1, 10))
        except Exception:
            pass

    # --------------------------------------------------
    # 🏷 TITLE
    # --------------------------------------------------
    title_style = ParagraphStyle(
        "Title",
        fontSize=17,
        alignment=1,
        textColor=primary_color,
        spaceAfter=6
    )

    elements.append(
        Paragraph(f"<b>{tenant.get('name', 'Restaurant')}</b>", title_style)
    )

    meta_style = ParagraphStyle("Meta", fontSize=10, alignment=1)

    invoice_no = order.get("order_number") or order_id
    elements.append(Paragraph(f"Invoice No: {invoice_no}", meta_style))
    elements.append(Paragraph("Thank you for dining with us!", meta_style))
    elements.append(Spacer(1, 15))

    # --------------------------------------------------
    # 📦 ITEMS TABLE
    # --------------------------------------------------
    table_data = [["Item", "Qty", "Amount (₹)"]]

    subtotal = 0.0
    for item in items.data:
        price = float(item.get("price", 0))
        subtotal += price
        table_data.append([
            item.get("product_name", ""),
            str(item.get("quantity", 1)),
            f"{price:.2f}"
        ])

    table = Table(table_data, colWidths=[90 * mm, 25 * mm, 35 * mm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, primary_color),
        ("BACKGROUND", (0, 0), (-1, 0), primary_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 15))

    # --------------------------------------------------
    # 💰 TOTALS (SAFE)
    # --------------------------------------------------
    discount = float(order.get("discount_amount", 0) or 0)
    total_payable = round(subtotal - discount, 2)

    totals_data = [
        ["Subtotal", f"₹ {subtotal:.2f}"]
    ]

    if discount > 0:
        totals_data.append(["Discount", f"- ₹ {discount:.2f}"])

    totals_data.append(["Total Payable", f"₹ {total_payable:.2f}"])

    totals_table = Table(totals_data, colWidths=[115 * mm, 35 * mm])
    totals_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, primary_color),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONT", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, -1), (-1, -1), primary_color),
    ]))

    elements.append(totals_table)
    elements.append(Spacer(1, 20))

    # --------------------------------------------------
    # 📌 FOOTER
    # --------------------------------------------------
    footer_style = ParagraphStyle(
        "Footer",
        fontSize=9,
        alignment=1,
        textColor=colors.grey
    )

    if tenant.get("address"):
        elements.append(Paragraph(tenant["address"], footer_style))

    if tenant.get("contact"):
        elements.append(Paragraph(f"Contact: {tenant['contact']}", footer_style))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Powered by Superscale POS", footer_style))

    # --------------------------------------------------
    # 🧾 BUILD PDF
    # --------------------------------------------------
    doc.build(elements)
    buffer.seek(0)
    return buffer
