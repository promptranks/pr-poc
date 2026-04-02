import inspect
import os
from datetime import datetime, timezone
from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stripe_customer import StripeCustomer
from app.models.user import User
from app.services.email_service import EmailService

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


async def _resolve(value):
    return await value if inspect.isawaitable(value) else value


class StripeService:
    @staticmethod
    async def create_checkout_session(user_id: UUID, plan: str, db: AsyncSession) -> str:
        secret_key = os.getenv("STRIPE_SECRET_KEY")
        frontend_url = os.getenv("FRONTEND_URL") or "http://localhost:5173"

        if plan == "premium_monthly":
            price_id = os.getenv("STRIPE_PREMIUM_PRICE_ID")
            if not price_id:
                raise ValueError("Stripe monthly premium price is missing. Set STRIPE_PREMIUM_PRICE_ID in .env.")
        elif plan == "premium_annual":
            price_id = os.getenv("STRIPE_YEARLY_PRICE_ID")
            if not price_id:
                raise ValueError("Stripe annual premium price is missing. Set STRIPE_YEARLY_PRICE_ID in .env.")
        else:
            raise ValueError("Unsupported subscription plan.")

        if not secret_key:
            raise ValueError("Stripe secret key is missing. Set STRIPE_SECRET_KEY in .env.")

        stripe.api_key = secret_key

        result = await db.execute(select(User).where(User.id == user_id))
        user = await _resolve(result.scalar_one())

        result = await db.execute(
            select(StripeCustomer).where(StripeCustomer.user_id == user_id)
        )
        stripe_customer = await _resolve(result.scalar_one_or_none())

        if not stripe_customer:
            customer = stripe.Customer.create(email=user.email, metadata={"user_id": str(user_id)})
            stripe_customer = StripeCustomer(
                user_id=user_id,
                stripe_customer_id=customer.id,
            )
            db.add(stripe_customer)
            await db.commit()

        session = stripe.checkout.Session.create(
            customer=stripe_customer.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=frontend_url + "/dashboard?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=frontend_url + "/?checkout=cancelled",
            metadata={"user_id": str(user_id), "plan": plan},
        )

        return session.url

    @staticmethod
    async def create_portal_session(user_id: UUID, db: AsyncSession) -> str:
        secret_key = os.getenv("STRIPE_SECRET_KEY")
        if not secret_key:
            raise ValueError("Stripe secret key is missing. Set STRIPE_SECRET_KEY in .env.")

        stripe.api_key = secret_key

        result = await db.execute(
            select(StripeCustomer).where(StripeCustomer.user_id == user_id)
        )
        stripe_customer = await _resolve(result.scalar_one())
        frontend_url = os.getenv("FRONTEND_URL") or "http://localhost:5173"

        session = stripe.billing_portal.Session.create(
            customer=stripe_customer.stripe_customer_id,
            return_url=frontend_url + "/dashboard",
        )

        return session.url

    @staticmethod
    async def handle_checkout_completed(session_data: dict, db: AsyncSession):
        import logging
        logger = logging.getLogger(__name__)

        user_id = UUID(session_data["metadata"]["user_id"])
        subscription_id = session_data["subscription"]

        logger.info(f"Webhook: checkout.session.completed for user {user_id}, subscription {subscription_id}")

        result = await db.execute(select(User).where(User.id == user_id))
        user = await _resolve(result.scalar_one())

        logger.info(f"Webhook: Updating user {user.email} from tier '{user.subscription_tier}' to 'premium'")

        user.subscription_tier = "premium"
        user.updated_at = datetime.now(timezone.utc)

        result = await db.execute(
            select(StripeCustomer).where(StripeCustomer.user_id == user_id)
        )
        stripe_customer = await _resolve(result.scalar_one())
        stripe_customer.stripe_subscription_id = subscription_id

        if hasattr(stripe_customer, "updated_at"):
            stripe_customer.updated_at = datetime.now(timezone.utc)

        await db.commit()

        logger.info(f"Webhook: Successfully updated user {user.email} to premium tier")

        EmailService.send_upgrade_email(user.email, user.name)

    @staticmethod
    async def handle_subscription_deleted(subscription_data: dict, db: AsyncSession):
        subscription_id = subscription_data["id"]

        result = await db.execute(
            select(StripeCustomer).where(StripeCustomer.stripe_subscription_id == subscription_id)
        )
        stripe_customer = await _resolve(result.scalar_one_or_none())

        if stripe_customer:
            result = await db.execute(select(User).where(User.id == stripe_customer.user_id))
            user = await _resolve(result.scalar_one())
            user.subscription_tier = "free"
            user.updated_at = datetime.now(timezone.utc)

            stripe_customer.stripe_subscription_id = None
            if hasattr(stripe_customer, "updated_at"):
                stripe_customer.updated_at = datetime.now(timezone.utc)

            await db.commit()
