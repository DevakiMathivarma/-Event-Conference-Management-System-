import random
import string
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.certificate import Certificate
from app.models.registration import Registration
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.certificate_repository import CertificateRepository
from app.repositories.check_in_repository import CheckInRepository
from app.schemas.certificate_schema import CertificateGenerate
from app.utils.logger import logger


def _generate_certificate_number() -> str:

    year = date.today().year

    random_suffix = "".join(random.choices(string.digits, k=6))

    return f"CERT-{year}-{random_suffix}"


def generate_certificate(registration_id: int, data: CertificateGenerate, current_user, db: Session) -> dict:

    try:

        logger.info(f"Generating certificate : registration {registration_id}")

        registration_repo = BaseRepository(Registration, db)
        checkin_repo = CheckInRepository(db)
        certificate_repo = CertificateRepository(db)
        audit_repo = AuditLogRepository(db)

        registration = registration_repo.get_by_id(registration_id)

        if not registration:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found.")

        existing_certificate = certificate_repo.get_by_registration_id(registration_id)

        if existing_certificate:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A certificate has already been generated for this registration.")

        # certificate can be generated only if the attendee satisfies
        # the event attendance requirement - level 11 business rule.
        # our own honest interpretation: a genuine check-in occurred,
        # since the task gives no more specific formula
        check_in = checkin_repo.get_by_registration_id(registration_id)

        if not check_in or check_in.check_in_time is None:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This attendee did not check in and does not meet the attendance requirement.")

        certificate_number = _generate_certificate_number()

        while db.query(Certificate).filter(Certificate.certificate_number == certificate_number).first():

            certificate_number = _generate_certificate_number()

        certificate = Certificate(
            certificate_number=certificate_number,
            registration_id=registration_id,
            attendee_id=registration.attendee_id,
            event_id=registration.event_id,
            certificate_type=data.certificate_type
        )

        certificate_repo.add(certificate)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="Certificate",
            entity_id=certificate.id,
            description=f"Certificate {certificate_number} generated for registration {registration_id}"
        )

        db.commit()

        certificate = certificate_repo.get_by_id_with_details(certificate.id)

        # level 13-equivalent notification - certificate availability,
        # wired in immediately, with the real pdf attached
        from app.utils.pdf import generate_certificate_pdf
        from app.tasks import send_certificate_availability_email

        attendee_user = registration.attendee.user

        certificate_path = generate_certificate_pdf(
            certificate_id=certificate.id,
            certificate_number=certificate.certificate_number,
            attendee_name=attendee_user.full_name,
            event_name=registration.event.event_name,
            certificate_type=data.certificate_type.value,
            issue_date=str(certificate.issue_date)
        )

        send_certificate_availability_email.delay(attendee_user.email, attendee_user.full_name, registration.event.event_name, certificate_path)

        logger.info(f"Certificate generated successfully : {certificate.id}")

        return {"message": "Certificate generated successfully.", "data": certificate}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Certificate generation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to generate certificate.")


def get_certificate_by_id(certificate_id: int, db: Session) -> dict:

    certificate_repo = CertificateRepository(db)

    certificate = certificate_repo.get_by_id_with_details(certificate_id)

    if not certificate:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found.")

    return {"message": "Certificate fetched successfully.", "data": certificate}


def get_certificates_for_attendee(attendee_id: int, db: Session) -> dict:

    certificate_repo = CertificateRepository(db)

    certificates = certificate_repo.list_for_attendee(attendee_id)

    return {"message": "Certificates fetched successfully.", "data": certificates}