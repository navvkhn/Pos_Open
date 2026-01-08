import qrcode
import io

def generate_qr(url: str):
    qr = qrcode.QRCode(
        version=1,
        box_size=8,
        border=2
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
