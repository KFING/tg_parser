import logging
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Response
from paddle_billing.Entities.Notifications import NotificationEvent
from paddle_billing.Notifications import Requests, Secret, Verifier
from paddle_billing.Notifications.Entities.Transaction import Transaction
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from src.app_api.auth.auth import AuthUser, get_auth
from src.app_api.dependencies import get_db_main
from src.app_api.middlewares import get_log_extra
from src.common.moment import as_utc
from src.dto.currency import Currency
from src.dto.payment_status import PaymentStatus
from src.env import settings
from src.service_paddle import paddle_manager
from src.service_paddle.models.paddle_webhook_payment_paid import PaddleWebhookPaymentPaid
from src.service_paddle.models.request_paddle_models import RequestPaddleInvoice

logger = logging.getLogger(__name__)


paddle_router = APIRouter(
    tags=["paddle"],
)


@paddle_router.post("/create_paddle_invoice")
async def create_invoice_paddle_billing(
    paddle_invoice: RequestPaddleInvoice,
    db: AsyncSession = Depends(get_db_main),
    *,
    request: Request,
    auth_user: AuthUser = Depends(get_auth),
    log_extra: dict[str, str] = Depends(get_log_extra),
) -> Response:
    return await paddle_manager.invoice_paddle_billing(db, paddle_invoice, request=request, auth_user=auth_user, log_extra=log_extra)


async def _get_webhook_payment_paid(request: Request, *, log_extra: dict[str, str] = Depends(get_log_extra)) -> PaddleWebhookPaymentPaid | None:
    paddle_request = Requests.Request.Request(headers=request.headers, body=(await request.body()))
    webhook_model = Verifier().verify(paddle_request, Secret(settings.PADDLE_TRANSACTION_PAID_NOTIFICATION_SECRET.get_secret_value()))
    if webhook_model is True:
        logger.debug("get_webhook_payment_paid :: webhook verified", extra=log_extra)
        webhook_notification = NotificationEvent.from_request(paddle_request)
        transaction = webhook_notification.data

        if not isinstance(transaction, Transaction):
            return None
        if transaction.details.totals.grand_total is None:
            return None
        return PaddleWebhookPaymentPaid(
            method_params=paddle_request.body.decode("utf-8"),
            subtotal=Decimal(transaction.details.totals.subtotal),
            grand_total=Decimal(transaction.details.totals.grand_total),
            discount=Decimal(transaction.details.totals.discount),
            occurred_at=as_utc(webhook_notification.occurred_at),
            data_id=transaction.id,
            currency=Currency(transaction.currency_code),
            status=PaymentStatus.PAID,
            price_id=transaction.items[-1].price.id,
            is_trial=bool(transaction.items[-1].price.trial_period),
            price_name=str(transaction.items[-1].price.name),
            price_description=transaction.items[-1].price.description,
            line_item_id=transaction.details.lineItems[-1].id,
        )

    return None


@paddle_router.post("/webhook_payment_paid")
async def payment_paid(info: PaddleWebhookPaymentPaid = Depends(_get_webhook_payment_paid), db: AsyncSession = Depends(get_db_main)) -> None:
    await paddle_manager.create_payment_paid(db, info)


@paddle_router.post("/refund")
async def refund(
    user_id: uuid.UUID, refund_type: PaymentStatus, payment_id: int, reason: str, amount: Decimal, db: AsyncSession = Depends(get_db_main)
) -> str | None:
    return await paddle_manager.create_refund(db, user_id, refund_type, payment_id, reason, amount)


# инвойс хранит что я должен оплатить, паймент содержит и их нельзя изменить
# три вида платежа паймент тайп()
"""
 - разовая покупка по инвойсу, те я выставляю инвойс и по нему оплачиваю
 - рекурентная подписка, или покупка подписки
 - отмена рекурентой подписки
 - возврат средств от любого платежа
 - дата и время с таймзоной
 Инвойс:
 - заголовок
 - контент
 - дата экспирации
 - дата создания
 - дата модификации
 - дата отмены
 - айди: уид
 - эмаунт: нумерик
 - валюта: энам
 - айди юзера
 - айди пэймент: один инвойс = один пэймент, но пэймент может не быть
 - сабскриптион план айди, default = нулл
 Пэймент:
 - айди: инт
 - дата создания
 - комент: тхт
 - айди юзера
 - пэмент метод = энам (падл, ...)
 - пэймент метод парамс = джисон
 - пэмент метод транзактион айди
 - пэймент метод адйи подписки
 - пэймент метод дата и время ивента
 - эмаунт нетто
 - эмаунт брутто
 - каренси
 - дисконт: нумерик
 - из триал
 Refund:
 - link payment
 - user
 - payment methods ALL
 -
 Сабскриптион план:
сделать модели, скинуть, потом миграции и потом уже все остальное
"""
