from fastapi import APIRouter

from app.routers.admin import router as admin_router
from app.routers.audit_logs import router as audit_router
from app.routers.auth import router as auth_router
from app.routers.billing import router as billing_router
from app.routers.billing import webhooks_router
from app.routers.calendar import router as calendar_router
from app.routers.categories import router as categories_router
from app.routers.checklist import router as checklist_router
from app.routers.contracts import router as contracts_router
from app.routers.dashboard import router as dashboard_router
from app.routers.events import router as events_router
from app.routers.notifications import router as notifications_router
from app.routers.payments import router as payments_router
from app.routers.plans import router as plans_router
from app.routers.supplier_quotes import router as quotes_router
from app.routers.suppliers import router as suppliers_router
from app.routers.workspaces import router as workspaces_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(workspaces_router)
api_router.include_router(events_router)
api_router.include_router(categories_router)
api_router.include_router(suppliers_router)
api_router.include_router(quotes_router)
api_router.include_router(dashboard_router)
api_router.include_router(checklist_router)
api_router.include_router(calendar_router)
api_router.include_router(payments_router)
api_router.include_router(contracts_router)
api_router.include_router(audit_router)
api_router.include_router(notifications_router)
api_router.include_router(plans_router)
api_router.include_router(billing_router)
api_router.include_router(admin_router)
api_router.include_router(webhooks_router)
