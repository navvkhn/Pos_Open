from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
import io
from supabase_client import supabase


def generate_bill_pdf(order_id):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    els = []

    order = supabase.table("orders").select("*").eq("id", order_id).single().execute()
    tenant = supabase.table("tenants").select("*").eq("id", order.data["tenant_id"]).single().execute()

    els.append(Paragraph(f"<b>{tenant.data['name']}</b>", styles["Title"]))
    els.append(Paragraph(
        f"Invoice No: {tenant.data['name'][:3].upper()}-{order.data['order_number']}",
        styles["Normal"]
    ))

    doc.build(els)
    buf.seek(0)
    return buf
