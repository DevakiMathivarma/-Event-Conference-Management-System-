from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin
from app.database import get_db
from app.schemas.dashboard_schema import AdminDashboardResponse, TopEventsResponse, TopSpeakersResponse, MonthlyRegistrationsResponse, MonthlyRevenueResponse
from app.services.admin_dashboard_service import (
    get_admin_dashboard, get_top_events_report, get_top_speakers_report, get_monthly_registrations_report, get_monthly_revenue_report
)

router = APIRouter(prefix="/api/v1/admin/dashboard", tags=["Admin Analytics"], dependencies=[Depends(require_admin)])


@router.get("/summary", response_model=AdminDashboardResponse)
def admin_dashboard_summary(db: Session = Depends(get_db)):
    return get_admin_dashboard(db)


@router.get("/top-events", response_model=TopEventsResponse)
def top_events(db: Session = Depends(get_db)):
    return get_top_events_report(db)


@router.get("/top-speakers", response_model=TopSpeakersResponse)
def top_speakers(db: Session = Depends(get_db)):
    return get_top_speakers_report(db)


@router.get("/monthly-registrations", response_model=MonthlyRegistrationsResponse)
def monthly_registrations(db: Session = Depends(get_db)):
    return get_monthly_registrations_report(db)


@router.get("/monthly-revenue", response_model=MonthlyRevenueResponse)
def monthly_revenue(db: Session = Depends(get_db)):
    return get_monthly_revenue_report(db)


from app.schemas.dashboard_schema import DailyRegistrationsResponse, TicketSalesResponse, SessionPopularityResponse
from app.services.admin_dashboard_service import get_daily_registrations_report, get_ticket_sales_report, get_session_popularity_report, export_ticket_sales_excel, export_daily_registrations_excel

@router.get("/daily-registrations", response_model=DailyRegistrationsResponse)
def daily_registrations(db: Session = Depends(get_db)):
    return get_daily_registrations_report(db)

@router.get("/ticket-sales", response_model=TicketSalesResponse)
def ticket_sales(db: Session = Depends(get_db)):
    return get_ticket_sales_report(db)

@router.get("/session-popularity", response_model=SessionPopularityResponse)
def session_popularity(db: Session = Depends(get_db)):
    return get_session_popularity_report(db)

@router.get("/ticket-sales/export")
def export_ticket_sales(db: Session = Depends(get_db)):
    return export_ticket_sales_excel(db)

@router.get("/daily-registrations/export")
def export_daily_registrations(db: Session = Depends(get_db)):
    return export_daily_registrations_excel(db)