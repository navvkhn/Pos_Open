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
from supabase_client import supabase
import requests


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
    # Branding colors
    # --------------------------------------------------
    primary_color = HexColor(tenant.data.get("primary_color", "#000000"))
    accent_color = HexColor(tenant.data.get("accent_color", "#DDDDDD"))

    # --------------------------------------------------
    # Logo
    # --------------------------------------------------
    if tenant.data.get("logo_url"):
        try:
            img_data = requests.get(tenant.data["logo_url"]).content
            logo = Image(io.BytesIO(img_data), width=45 * mm, height=18 * mm)
            logo.hAlign = "CENTER"
            elements.append(logo)
            elements.append(Spacer(1, 10))
        except Exception:
            pass

    # --------------------------------------------------
    # Cafe Name
    # --------------------------------------------------
    title_style = ParagraphStyle(
        "Title",
        fontSize=18,
        alignment=1,
        textColor=primary_color,
        spaceAfter=8
    )
    elements.append(Paragraph(f"<b>{tenant.data['name']}</b>", title_style))

    meta_style = ParagraphStyle(
        "Meta",
        fontSize=10,
        alignment=1
    )

    elements.append(Paragraph(f"Invoice No: {order_id}", meta_style))
    elements.append(Paragraph("Thank you for dining with us!", meta_style))
    elements.append(Spacer(1, 15))

    # --------------------------------------------------
    # Items table
    # --------------------------------------------------
    table_data = [["Item", "Qty", "Amount (₹)"]]

    for item in items.data:
        table_data.append([
            item["product_name"],
            str(item["quantity"]),
            f"{item['price']:.2f}"
        ])

    table = Table(table_data, colWidths=[90 * mm, 25 * mm, 35 * mm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, primary_color),
        ("BACKGROUND", (0, 0), (-1, 0), accent_color),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 15))

    # --------------------------------------------------
    # Totals
    # --------------------------------------------------
    totals_data = [
        ["Subtotal", f"₹ {order.data['total'] + order.data.get('discount_amount', 0):.2f}"]
    ]

    if order.data.get("discount_amount", 0) > 0:
        totals_data.append(["Discount", f"- ₹ {order.data['discount_amount']:.2f}"])

    totals_data.append(["Total Payable", f"₹ {order.data['total']:.2f}"])

    totals_table = Table(totals_data, colWidths=[115 * mm, 35 * mm])
    totals_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, primary_color),
        ("BACKGROUND", (-1, -1), (-1, -1), accent_color),
        ("FONT", (-1, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ]))

    elements.append(totals_table)
    elements.append(Spacer(1, 20))

    # --------------------------------------------------
    # Footer
    # --------------------------------------------------
    footer_style = ParagraphStyle(
        "Footer",
        fontSize=9,
        alignment=1,
        textColor=colors.grey
    )

    if tenant.data.get("address"):
        elements.append(Paragraph(tenant.data["address"], footer_style))

    if tenant.data.get("contact"):
        elements.append(Paragraph(f"Contact: {tenant.data['contact']}", footer_style))

    if tenant.data.get("instagram_handle"):
        elements.append(
            Paragraph(
                f"Follow us on Instagram 📸 @{tenant.data['instagram_handle']}",
                footer_style
            )
        )

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Powered by Superscale POS", footer_style))

    # --------------------------------------------------
    # Build PDF
    # --------------------------------------------------
    doc.build(elements)
    buffer.seek(0)
    return buffer
