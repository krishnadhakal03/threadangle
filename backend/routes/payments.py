import os
import stripe
from fastapi import APIRouter, Depends, Request, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from auth import get_current_user
from models import User, Subscription
from datetime import datetime, timedelta

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Plan name → Stripe price ID mapping
STRIPE_PRICE_IDS = {
    "solo": os.getenv("STRIPE_STARTER_PRICE_ID"),
    "founder": os.getenv("STRIPE_PRO_PRICE_ID"),
}

@router.post("/create-checkout")
async def create_checkout(
    plan: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if plan not in STRIPE_PRICE_IDS:
        raise HTTPException(status_code=400, detail="Invalid plan")

    if os.getenv("ENVIRONMENT", "development") == "production":
        base_url = "https://kriangle.com"
    else:
        base_url = "http://localhost:5173"

    try:
        checkout_session = stripe.checkout.Session.create(
            ui_mode='embedded',
            customer=current_user.stripe_customer_id,
            customer_email=current_user.email if not current_user.stripe_customer_id else None,
            line_items=[{
                'price': STRIPE_PRICE_IDS[plan],
                'quantity': 1,
            }],
            mode='subscription',
            return_url=f"{base_url}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
            metadata={
                "user_id": current_user.id,
                "plan": plan
            }
        )
        print(f"\n✅ Embedded checkout session created: {checkout_session.id}")
        return {
            "clientSecret": checkout_session.client_secret,
            "sessionId": checkout_session.id
        }
    except Exception as e:
        print(f"❌ Checkout session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-session")
async def verify_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Called by frontend after embedded checkout completes.
    Retrieves the Stripe session, verifies payment, and updates
    the user's plan in the database directly — no webhook needed.
    """
    print(f"\n🔍 Verifying session {session_id} for user {current_user.email}")
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as e:
        print(f"❌ Stripe error retrieving session: {e}")
        raise HTTPException(status_code=400, detail="Could not retrieve session")

    # Security: ensure this session belongs to the requesting user
    meta_user_id = session.get("metadata", {}).get("user_id")
    if str(meta_user_id) != str(current_user.id):
        print(f"❌ Session user_id mismatch: {meta_user_id} vs {current_user.id}")
        raise HTTPException(status_code=403, detail="Session does not belong to this user")

    if session.get("payment_status") != "paid":
        print(f"⚠️ Payment not completed yet: {session.get('payment_status')}")
        return {"status": "pending", "plan": current_user.plan}

    plan = session.get("metadata", {}).get("plan")  # 'solo' or 'founder'
    if not plan:
        raise HTTPException(status_code=400, detail="Plan not found in session metadata")

    # Already upgraded — idempotent
    if current_user.plan == plan:
        print(f"✅ User already on {plan} plan")
        return {"status": "ok", "plan": plan}

    # Update user plan
    current_user.plan = plan
    current_user.usage_count = 0
    current_user.stripe_customer_id = session.get("customer")
    await db.commit()
    await db.refresh(current_user)

    print(f"✅ Plan updated: {current_user.email} → {plan.upper()}")
    return {"status": "ok", "plan": plan}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    # ── Visual separator ──────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("🔔 STRIPE WEBHOOK RECEIVED")
    print("=" * 80)
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    print(f"📦 Payload size: {len(payload)} bytes")
    print(f"🔐 Signature header present: {bool(sig_header)}")

    # ── Verify webhook signature ──────────────────────────────────────────────
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        print("❌ CRITICAL: STRIPE_WEBHOOK_SECRET not found in environment variables")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    print(f"🔑 Using webhook secret: {webhook_secret[:15]}...")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        print(f"✅ Webhook signature verified successfully")
        print(f"📋 Event type: {event['type']}")
        print(f"🆔 Event ID: {event['id']}")
        print(f"   Created: {event['created']} | Livemode: {event['livemode']}")
    except ValueError as e:
        print(f"❌ Invalid payload: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as e:
        print(f"❌ Signature verification failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # ── Handle events ─────────────────────────────────────────────────────────
    if event["type"] == "checkout.session.completed":
        print("\n💰 Processing successful payment...")
        session = event["data"]["object"]

        # Extract payment details
        user_id = session.get("metadata", {}).get("user_id")
        plan = session.get("metadata", {}).get("plan")  # 'solo' or 'founder'
        stripe_customer_id = session.get("customer")
        stripe_subscription_id = session.get("subscription")
        customer_email = session.get("customer_email")
        amount_total = session.get("amount_total", 0)  # cents

        print(f"📧 Customer email: {customer_email}")
        print(f"👤 Stripe customer ID: {stripe_customer_id}")
        print(f"🔄 Subscription ID: {stripe_subscription_id}")
        print(f"💵 Amount paid: ${amount_total / 100:.2f}")
        print(f"📋 Metadata — user_id: {user_id}, plan: {plan}")

        # Determine plan from metadata (primary) or amount (fallback)
        if not plan:
            if amount_total == 900:
                plan = "solo"
                print("📦 Plan detected from amount: SOLO ($9)")
            elif amount_total == 1900:
                plan = "founder"
                print("📦 Plan detected from amount: FOUNDER ($19)")
            else:
                print(f"⚠️ Cannot determine plan. Amount=${amount_total/100:.2f}, metadata plan=None")
                return {"status": "ok"}
        else:
            print(f"📦 Plan from metadata: {plan.upper()}")

        # Find user — by ID first (reliable), email as fallback
        user = None
        if user_id:
            result = await db.execute(select(User).where(User.id == int(user_id)))
            user = result.scalars().first()
            if user:
                print(f"✅ User found by ID: {user.email} (ID: {user.id})")
        if not user and customer_email:
            result = await db.execute(select(User).where(User.email == customer_email))
            user = result.scalars().first()
            if user:
                print(f"✅ User found by email: {user.email} (ID: {user.id})")

        if not user:
            print(f"❌ User not found (user_id={user_id}, email={customer_email})")
            return {"status": "error", "reason": "user_not_found"}

        print(f"   Current plan: {user.plan} | Current usage: {user.usage_count}")

        # Update user record
        user.plan = plan
        user.usage_count = 0
        user.stripe_customer_id = stripe_customer_id

        # Upsert subscription record
        sub_result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
        )
        existing_sub = sub_result.scalars().first()
        if existing_sub:
            existing_sub.plan = plan
            existing_sub.status = "active"
        else:
            db.add(Subscription(
                user_id=user.id,
                stripe_subscription_id=stripe_subscription_id,
                plan=plan,
                status="active",
            ))

        await db.commit()

        generation_limit = 30 if plan == "solo" else 100
        print(f"✅ DATABASE UPDATED:")
        print(f"   Plan: {plan.upper()} | Generations: 0/{generation_limit}")
        print(f"   Stripe customer ID: {stripe_customer_id}")

        # Send confirmation email (non-critical — don't fail webhook if email errors)
        print(f"\n📧 Sending subscription confirmation email to {user.email}...")
        try:
            from email_service import send_upgrade_confirmation
            plan_name = "Solo" if plan == "solo" else "Founder"
            amount = 9 if plan == "solo" else 19
            next_billing = (datetime.now() + timedelta(days=30)).strftime("%B %d, %Y")
            await send_upgrade_confirmation(user.email, plan_name, amount, next_billing)
            print(f"✅ Confirmation email sent to {user.email}")
        except Exception as e:
            print(f"⚠️ Email failed (non-critical): {str(e)}")

        print(f"\n🎉 PAYMENT PROCESSING COMPLETE")
        print(f"   User {user.email} upgraded to {plan.upper()}")

    elif event["type"] == "customer.subscription.deleted":
        print("\n🚫 Subscription cancelled — handling downgrade...")
        session = event["data"]["object"]
        stripe_customer_id = session.get("customer")
        if stripe_customer_id:
            result = await db.execute(select(User).where(User.stripe_customer_id == stripe_customer_id))
            user = result.scalars().first()
            if user:
                user.plan = "free"
                await db.commit()
                print(f"✅ User {user.email} downgraded to free plan")
            else:
                print(f"⚠️ No user found for Stripe customer: {stripe_customer_id}")

    else:
        print(f"\nℹ️ Unhandled event type: {event['type']} (this is normal)")

    print("=" * 80 + "\n")
    return {"status": "success"}

@router.post("/portal")
async def customer_portal(current_user: User = Depends(get_current_user)):
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No stripe customer found")
    
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=os.getenv("FRONTEND_URL", "http://localhost:5173") + "/dashboard"
        )
        return {"url": portal_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
