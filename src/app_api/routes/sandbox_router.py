import datetime
import logging
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from src.app_api.dependencies import get_db_main
from src.app_api.middlewares import get_log_extra
from src.app_api.templates.paddle_prices import render_template_paddle_prices_response
from src.common.typing import as_uuid
from src.db_main.cruds import invoice_crud, payment_crud
from src.dto.currency import Currency
from src.dto.payment_method import PaymentMethod
from src.dto.payment_status import PaymentStatus
from src.env import settings
from src.service_paddle.cruds import paddle_plan_crud
from src.service_paddle.paddle_manager import InvalidDataException

logger = logging.getLogger(__name__)


sandbox_router = APIRouter(
    tags=["test"],
)

templates = Jinja2Templates(directory=settings.ROOT_PATH / "src" / "service_paddle")


@sandbox_router.get("/without_invoice")
async def get_htmlcode(request: Request) -> HTMLResponse:
    return render_template_paddle_prices_response(request, "pri_01jdjdk6tkn59xsh6kxg1h40j6")


@sandbox_router.get("/invoice")
async def get_invoice(
    request: Request,
    db: AsyncSession = Depends(get_db_main),
    log_extra: dict[str, str] = Depends(get_log_extra),
) -> HTMLResponse:
    header = "test invoice header"
    content = "test invoice content"
    plan_id = "pri_01jdjdk6tkn59xsh6kxg1h40j6"
    paddle_plan = await paddle_plan_crud.get_paddle_plan(plan_id)
    if not paddle_plan:
        raise InvalidDataException
    await invoice_crud.create_invoice(
        db=db,
        user_id=as_uuid("878f5a6f-21b6-4d53-8e34-bc7ce0572cf6"),
        header=header,
        content=content,
        amount=paddle_plan.amount,
        currency=paddle_plan.currency,
        subscription_plan_id=plan_id,
    )
    logger.info("create invoice :: add to database -> success", extra=log_extra)
    return render_template_paddle_prices_response(request, plan_id)


@sandbox_router.post("/add_payment")
async def create_payment_db(
    plan_id: str,
    db: AsyncSession = Depends(get_db_main),
) -> str:
    await payment_crud.create_payment(
        db,
        user_id=uuid.UUID("48543566-4552-461f-9698-50b7d06176cf"),
        status=PaymentStatus.PAID,
        comment="comment",
        payment_method=PaymentMethod.PADDLE,
        payment_method_params={},
        payment_method_transaction_id="id",
        payment_method_subscription_id="test",
        payment_method_event_dt=datetime.datetime.now(),
        amount_netto=Decimal(100),
        amount_brutto=Decimal(100),
        currency=Currency.CNY,
        discount=Decimal(0),
        is_trial=False,
    )
    return plan_id
