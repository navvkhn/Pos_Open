from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io
from supabase_client import supabase

def generate_bill_pdf(order_id):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()

    order = supabase.table("orders").select("*").eq("id", order_id).single().execute()
    tenant = supabase.table("tenants").select("*").eq("id", order.data["tenant_id"]).single().execute()

    elements = []
    elements.append(Paragraph(f"<b>{tenant.data['name']}</b>", styles["Title"]))
    elements.append(Paragraph(f"Order ID: {order_id}", styles["Normal"]))
    elements.append(Paragraph(f"Total: ₹{order.data['total']}", styles["Normal"]))
    elements.append(Paragraph(" ", styles["Normal"]))
    elements.append(Paragraph(tenant.data.get("address", ""), styles["Normal"]))
    elements.append(Paragraph(f"Contact: {tenant.data.get('contact','')}", styles["Normal"]))

    doc.build(elements)
    buf.seek(0)
    return buf
