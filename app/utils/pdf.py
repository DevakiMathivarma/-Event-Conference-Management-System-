import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from app.utils.logger import logger

CERTIFICATE_DIR = "generated_files/certificates"
TICKET_DIR = "generated_files/tickets"

os.makedirs(CERTIFICATE_DIR, exist_ok=True)
os.makedirs(TICKET_DIR, exist_ok=True)


# generates a real certificate of participation/completion pdf
def generate_certificate_pdf(
    certificate_id: int,
    certificate_number: str,
    attendee_name: str,
    event_name: str,
    certificate_type: str,
    issue_date: str
) -> str:

    try:

        file_path = os.path.join(CERTIFICATE_DIR, f"certificate_{certificate_id}.pdf")

        pdf = canvas.Canvas(file_path, pagesize=A4)

        pdf.setFont("Helvetica-Bold", 22)
        pdf.drawCentredString(4.13 * inch, 9 * inch, "Certificate of " + certificate_type.title())

        pdf.setFont("Helvetica", 14)
        pdf.drawCentredString(4.13 * inch, 7.8 * inch, "This certificate is proudly presented to")

        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawCentredString(4.13 * inch, 7.0 * inch, attendee_name)

        pdf.setFont("Helvetica", 13)
        pdf.drawCentredString(4.13 * inch, 6.0 * inch, f"for participating in {event_name}")

        pdf.setFont("Helvetica", 11)
        pdf.drawCentredString(4.13 * inch, 4.5 * inch, f"Certificate Number: {certificate_number}")
        pdf.drawCentredString(4.13 * inch, 4.1 * inch, f"Issued on: {issue_date}")

        pdf.save()

        logger.info(f"Certificate PDF generated : {file_path}")

        return file_path

    except Exception as error:

        logger.error(f"Certificate PDF generation failed for certificate {certificate_id} : {str(error)}")

        raise


# generates a real ticket pdf, given to the attendee once their
# purchase is confirmed
def generate_ticket_pdf(
    purchase_id: int,
    event_name: str,
    attendee_name: str,
    ticket_type: str,
    quantity: int,
    total_amount: str,
    event_start_date: str
) -> str:

    try:

        file_path = os.path.join(TICKET_DIR, f"ticket_{purchase_id}.pdf")

        pdf = canvas.Canvas(file_path, pagesize=A4)

        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(1 * inch, 10.5 * inch, "Event Ticket")

        pdf.setFont("Helvetica", 12)

        lines = [
            f"Event: {event_name}",
            f"Attendee: {attendee_name}",
            f"Ticket Type: {ticket_type}",
            f"Quantity: {quantity}",
            f"Total Amount Paid: {total_amount}",
            f"Event Date: {event_start_date}"
        ]

        y_position = 9.8 * inch

        for line in lines:

            pdf.drawString(1 * inch, y_position, line)
            y_position -= 0.35 * inch

        pdf.save()

        logger.info(f"Ticket PDF generated : {file_path}")

        return file_path

    except Exception as error:

        logger.error(f"Ticket PDF generation failed for purchase {purchase_id} : {str(error)}")

        raise