from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import stripe
import os

from app.database import get_db
from app.models.user import User
from app.models.stripe_customer import StripeCustomer
from app.services.stripe_service import StripeService
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/payments", tags=["payments"])


class CheckoutRequest(BaseModel):
    plan: Literal["premium_monthly", "premium_annual"]


class SyncSubscriptionRequest(BaseModel):
    session_id: str


@router.post("/sync-subscription")
async def sync_subscription(
    request: SyncSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually sync subscription status from Stripe (for sandbox/local testing)."""
    import logging
    from datetime import datetime, timezone

    logger = logging.getLogger(__name__)

    try:
        # Retrieve the checkout session from Stripe
        session = stripe.checkout.Session.retrieve(request.session_id)

        logger.info(f"Sync: Retrieved session {session.id}, status: {session.payment_status}, subscription: {session.subscription}")

        # Check if payment was successful and subscription exists
        if session.payment_status == "paid" and session.subscription:
            # Update user subscription
            current_user.subscription_tier = "premium"
            current_user.updated_at = datetime.now(timezone.utc)

            # Update or create stripe customer record
            result = await db.execute(
                select(StripeCustomer).where(StripeCustomer.user_id == current_user.id)
            )
            stripe_customer = result.scalar_one_or_none()

            if stripe_customer:
                stripe_customer.stripe_subscription_id = session.subscription
                if hasattr(stripe_customer, "updated_at"):
                    stripe_customer.updated_at = datetime.now(timezone.utc)

            await db.commit()

            logger.info(f"Sync: Updated user {current_user.email} to premium tier")

            return {
                "status": "success",
                "subscription_tier": "premium",
                "message": "Subscription synced successfully"
            }
        else:
            return {
                "status": "pending",
                "subscription_tier": current_user.subscription_tier,
                "message": "Payment not completed or subscription not found"
            }

    except stripe.error.StripeError as e:
        logger.error(f"Sync: Stripe error - {str(e)}")
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        logger.error(f"Sync: Unexpected error - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/create-checkout")
async def create_checkout(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        checkout_url = await StripeService.create_checkout_session(current_user.id, request.plan, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except stripe.error.StripeError as exc:
        message = getattr(exc, "user_message", None) or "Stripe checkout is not configured correctly yet."
        raise HTTPException(status_code=502, detail=message)

    return {"checkout_url": checkout_url}


@router.post("/create-portal")
async def create_portal(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    portal_url = await StripeService.create_portal_session(current_user.id, db)
    return {"portal_url": portal_url}


@router.get("/subscription")
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(StripeCustomer).where(StripeCustomer.user_id == current_user.id)
    )
    stripe_customer = result.scalar_one_or_none()

    if not stripe_customer or not stripe_customer.stripe_subscription_id:
        return {"subscription": None}

    subscription = stripe.Subscription.retrieve(stripe_customer.stripe_subscription_id)

    return {
        "subscription": {
            "id": subscription.id,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end
        }
    }


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    import logging
    logger = logging.getLogger(__name__)

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    logger.info(f"Webhook: Received Stripe webhook, signature present: {bool(sig_header)}")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        logger.info(f"Webhook: Event type: {event['type']}, ID: {event.get('id', 'unknown')}")
    except ValueError as e:
        logger.error(f"Webhook: Invalid payload - {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook: Invalid signature - {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        logger.info("Webhook: Processing checkout.session.completed")
        await StripeService.handle_checkout_completed(event["data"]["object"], db)
    elif event["type"] == "customer.subscription.deleted":
        logger.info("Webhook: Processing customer.subscription.deleted")
        await StripeService.handle_subscription_deleted(event["data"]["object"], db)
    elif event["type"] == "invoice.payment_failed":
        logger.info("Webhook: Processing invoice.payment_failed")
        await StripeService.handle_payment_failed(event["data"]["object"], db)
    elif event["type"] == "invoice.payment_succeeded":
        logger.info("Webhook: Processing invoice.payment_succeeded")
        await StripeService.handle_invoice_paid(event["data"]["object"], db)
    elif event["type"] == "customer.subscription.updated":
        logger.info("Webhook: Processing customer.subscription.updated")
        await StripeService.handle_subscription_updated(event["data"]["object"], db)
    else:
        logger.info(f"Webhook: Unhandled event type: {event['type']}")

    return {"status": "success"}
