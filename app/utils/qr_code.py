import os
from io import BytesIO

import qrcode
from PIL import Image
from pyzbar.pyzbar import decode

from app.utils.logger import logger

QR_OUTPUT_DIR = "generated_files/qr_codes"

os.makedirs(QR_OUTPUT_DIR, exist_ok=True)


# generates a real qr code image at registration time, encoding the
# registration's own reference - the real mechanism behind the qr
# check-in bonus feature
def generate_registration_qr_code(registration_id: int, reference: str) -> str:

    try:

        file_path = os.path.join(QR_OUTPUT_DIR, f"registration_{registration_id}.png")

        qr_image = qrcode.make(reference)
        qr_image.save(file_path)

        logger.info(f"QR code generated for registration {registration_id} : {file_path}")

        return file_path

    except Exception as error:

        logger.error(f"QR code generation failed for registration {registration_id} : {str(error)}")

        raise


# decodes an uploaded qr code image back into its original text - the
# real mechanism behind POST /check-in/verify-qr
def decode_qr_code(image_bytes: bytes) -> str | None:

    try:

        image = Image.open(BytesIO(image_bytes))

        decoded_results = decode(image)

        if not decoded_results:

            return None

        return decoded_results[0].data.decode("utf-8")

    except Exception as error:

        logger.error(f"QR code decoding failed : {str(error)}")

        return None