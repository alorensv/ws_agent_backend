import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime

class PdfHelper:
    def generate_quote_pdf(self, quote_data: dict, client_info: dict) -> str:
        """Genera un archivo PDF de cotización profesional utilizando ReportLab."""
        os.makedirs("/tmp", exist_ok=True)
        file_path = f"/tmp/Cotizacion_{quote_data['id'][:8]}.pdf"
        
        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter

        # Cabecera
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "Lineas de Código - Alejandro Lorens")
        
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        c.drawString(50, height - 85, f"Referencia: {quote_data['id']}")

        # Datos Cliente
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 120, "Datos del Cliente:")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 135, f"Teléfono: {client_info['phone']}")
        c.drawString(50, height - 150, f"Nombre: {client_info['name']}")

        # Tabla de Items
        c.line(50, height - 170, width - 50, height - 170)
        c.drawString(50, height - 185, "Servicio/Producto")
        c.drawString(400, height - 185, "Cantidad")
        c.drawString(500, height - 185, "Precio")
        c.line(50, height - 190, width - 50, height - 190)

        y = height - 210
        for item in quote_data["items"]:
            c.drawString(50, y, item["name"])
            c.drawString(400, y, str(item["qty"]))
            c.drawString(500, y, f"${item['price']:,.0f}")
            y -= 20

        # Total
        c.line(50, y, width - 50, y)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(400, y - 25, "TOTAL CLP:")
        c.drawString(500, y - 25, f"${quote_data['total']:,.0f}")

        # Pie de página
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(50, 50, "Esta cotización es de carácter referencial y está sujeta a validación técnica.")
        
        c.showPage()
        c.save()
        return file_path
