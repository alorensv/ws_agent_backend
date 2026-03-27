from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
import os

class PdfService:
    def __init__(self):
        self.output_dir = "/app/storage/quotes"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

    def generate_quote_pdf(self, quote_data: dict, client_info: dict) -> str:
        filename = f"quote_{quote_data['id']}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        c = canvas.Canvas(filepath, pagesize=letter)
        width, height = letter

        # --- Header ---
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1*inch, height - 1*inch, "COTIZACIÓN DE SERVICIOS")
        
        c.setFont("Helvetica", 10)
        c.drawString(1*inch, height - 1.25*inch, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}")
        c.drawString(1*inch, height - 1.4*inch, f"Cotización #: {quote_data['id'][:8]}")

        # --- Client Info ---
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1*inch, height - 2*inch, "DATOS DEL CLIENTE")
        c.setFont("Helvetica", 10)
        c.drawString(1*inch, height - 2.2*inch, f"Teléfono: {client_info['phone']}")
        if client_info.get('name'):
            c.drawString(1*inch, height - 2.35*inch, f"Nombre: {client_info['name']}")

        # --- Table Header ---
        c.line(1*inch, height - 2.6*inch, 7.5*inch, height - 2.6*inch)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1*inch, height - 2.8*inch, "Producto / Servicio")
        c.drawString(4.5*inch, height - 2.8*inch, "Cant.")
        c.drawString(5.5*inch, height - 2.8*inch, "Precio Unit.")
        c.drawString(6.5*inch, height - 2.8*inch, "Subtotal")
        c.line(1*inch, height - 2.9*inch, 7.5*inch, height - 2.9*inch)

        # --- Items ---
        y = height - 3.1*inch
        c.setFont("Helvetica", 10)
        total = 0
        for item in quote_data['items']:
            subtotal = item['qty'] * item['price']
            c.drawString(1*inch, y, item['name'])
            c.drawString(4.5*inch, y, str(item['qty']))
            c.drawString(5.5*inch, y, f"${item['price']}")
            c.drawString(6.5*inch, y, f"${subtotal}")
            total += subtotal
            y -= 0.25*inch

        # --- Total ---
        c.line(1*inch, y, 7.5*inch, y)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(5.5*inch, y - 0.3*inch, "TOTAL:")
        c.drawString(6.5*inch, y - 0.3*inch, f"${total}")

        # --- Footer ---
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(1*inch, 1*inch, "Esta cotización está sujeta a validación por el personal de la empresa.")
        
        c.save()
        return filepath
