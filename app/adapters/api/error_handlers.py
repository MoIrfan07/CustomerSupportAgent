import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    DomainError,
    OrderNotCancellableError,
    PaymentNotRefundableError,
)


logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register application-level exception handlers."""

    @app.exception_handler(OrderNotCancellableError)
    async def order_not_cancellable_handler(
        request: Request,
        exc: OrderNotCancellableError,
    ) -> JSONResponse:
        logger.warning(
            "Order cancellation rejected | order_id=%s status=%s",
            exc.order_id,
            exc.current_status,
        )

        return JSONResponse(
            status_code=409,
            content={
                "error": "order_not_cancellable",
                "message": str(exc),
            },
        )

    @app.exception_handler(PaymentNotRefundableError)
    async def payment_not_refundable_handler(
        request: Request,
        exc: PaymentNotRefundableError,
    ) -> JSONResponse:
        logger.warning(
            "Payment refund rejected | payment_id=%s status=%s",
            exc.payment_id,
            exc.current_status,
        )

        return JSONResponse(
            status_code=409,
            content={
                "error": "payment_not_refundable",
                "message": str(exc),
            },
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(
        request: Request,
        exc: DomainError,
    ) -> JSONResponse:
        logger.warning(
            "Domain error | error=%s",
            str(exc),
        )

        return JSONResponse(
            status_code=400,
            content={
                "error": "domain_error",
                "message": str(exc),
            },
        )
