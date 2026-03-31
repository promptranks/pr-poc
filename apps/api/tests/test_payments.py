import os
import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4
from app.services.stripe_service import StripeService
from app.models.user import User
from app.models.stripe_customer import StripeCustomer


@pytest.mark.asyncio
async def test_create_checkout_session():
    user_id = uuid4()
    mock_db = AsyncMock()

    mock_user = User(id=user_id, email="test@example.com", name="Test User")
    mock_db.execute.return_value.scalar_one.return_value = mock_user
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    with patch.dict(os.environ, {
        'STRIPE_SECRET_KEY': 'sk_test_123',
        'STRIPE_PREMIUM_PRICE_ID': 'price_test_123',
        'FRONTEND_URL': 'https://prk.promptranks.org',
    }, clear=False), \
         patch('stripe.Customer.create') as mock_customer, \
         patch('stripe.checkout.Session.create') as mock_session:
        mock_customer.return_value = Mock(id="cus_test123")
        mock_session.return_value = Mock(url="https://checkout.stripe.com/test")

        url = await StripeService.create_checkout_session(user_id, "premium_monthly", mock_db)

        assert url == "https://checkout.stripe.com/test"
        mock_customer.assert_called_once()
        mock_session.assert_called_once()


@pytest.mark.asyncio
async def test_create_portal_session():
    user_id = uuid4()
    mock_db = AsyncMock()

    mock_stripe_customer = StripeCustomer(
        user_id=user_id,
        stripe_customer_id="cus_test123"
    )
    mock_db.execute.return_value.scalar_one.return_value = mock_stripe_customer

    with patch.dict(os.environ, {
        'STRIPE_SECRET_KEY': 'sk_test_123',
        'FRONTEND_URL': 'https://prk.promptranks.org',
    }, clear=False), \
         patch('stripe.billing_portal.Session.create') as mock_portal:
        mock_portal.return_value = Mock(url="https://billing.stripe.com/portal")

        url = await StripeService.create_portal_session(user_id, mock_db)

        assert url == "https://billing.stripe.com/portal"
        mock_portal.assert_called_once()


@pytest.mark.asyncio
async def test_handle_checkout_completed():
    user_id = uuid4()
    mock_db = AsyncMock()

    mock_user = User(id=user_id, email="test@example.com", subscription_tier="free")
    mock_stripe_customer = StripeCustomer(user_id=user_id, stripe_customer_id="cus_test123")

    mock_db.execute.return_value.scalar_one.side_effect = [mock_user, mock_stripe_customer]

    session_data = {
        "metadata": {"user_id": str(user_id)},
        "subscription": "sub_test123"
    }

    await StripeService.handle_checkout_completed(session_data, mock_db)

    assert mock_user.subscription_tier == "premium"
    assert mock_stripe_customer.stripe_subscription_id == "sub_test123"
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_handle_subscription_deleted():
    user_id = uuid4()
    mock_db = AsyncMock()

    mock_user = User(id=user_id, email="test@example.com", subscription_tier="premium")
    mock_stripe_customer = StripeCustomer(
        user_id=user_id,
        stripe_customer_id="cus_test123",
        stripe_subscription_id="sub_test123"
    )

    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_stripe_customer
    mock_db.execute.return_value.scalar_one.return_value = mock_user

    subscription_data = {"id": "sub_test123"}

    await StripeService.handle_subscription_deleted(subscription_data, mock_db)

    assert mock_user.subscription_tier == "free"
    assert mock_stripe_customer.stripe_subscription_id is None
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_invalid_signature():
    from fastapi import HTTPException
    from app.routers.payments import stripe_webhook

    mock_request = Mock()
    mock_request.body = AsyncMock(return_value=b"test_payload")
    mock_request.headers.get.return_value = "invalid_signature"
    mock_db = AsyncMock()

    with patch('stripe.Webhook.construct_event') as mock_construct:
        mock_construct.side_effect = Exception("Invalid signature")

        with pytest.raises(Exception):
            await stripe_webhook(mock_request, mock_db)

