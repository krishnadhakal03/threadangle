from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

INSTAGRAM_WEBHOOK_VERIFY_TOKEN = os.getenv("INSTAGRAM_WEBHOOK_VERIFY_TOKEN", "threadangle_webhook_verify_token_2026")

@router.get("/instagram")
async def verify_instagram_webhook(request: Request):
    """
    Webhook verification endpoint for Instagram
    Meta will call this with hub.challenge to verify the webhook
    
    Expected query params:
    - hub.mode: "subscribe"
    - hub.challenge: challenge token to echo back
    - hub.verify_token: token we defined in Meta Dashboard
    """
    try:
        hub_mode = request.query_params.get("hub.mode")
        hub_challenge = request.query_params.get("hub.challenge")
        hub_verify_token = request.query_params.get("hub.verify_token")

        logger.info(f"📍 Webhook verification request received")
        logger.info(f"   Mode: {hub_mode}")
        logger.info(f"   Challenge: {hub_challenge}")
        logger.info(f"   Verify Token: {hub_verify_token}")

        # Verify the webhook
        if hub_mode != "subscribe":
            logger.warning(f"❌ Invalid webhook mode: {hub_mode}")
            raise HTTPException(status_code=403, detail="Invalid mode")

        if hub_verify_token != INSTAGRAM_WEBHOOK_VERIFY_TOKEN:
            logger.warning(f"❌ Invalid verify token: {hub_verify_token}")
            logger.warning(f"   Expected: {INSTAGRAM_WEBHOOK_VERIFY_TOKEN}")
            raise HTTPException(status_code=403, detail="Invalid verify token")

        logger.info(f"✅ Webhook verified successfully!")
        return JSONResponse(content=hub_challenge)

    except HTTPException as e:
        logger.error(f"❌ HTTP error: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Webhook verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instagram")
async def handle_instagram_webhook(request: Request):
    """
    Handle incoming Instagram webhook events
    
    Expected events:
    - feed: New posts from subscribed accounts
    - story: New stories from subscribed accounts
    - comments: New comments on posts
    - mentions: New mentions of accounts
    """
    try:
        body = await request.json()
        
        logger.info(f"📨 Received webhook event")
        logger.info(f"   Body: {body}")
        
        # Extract events from webhook
        if "entry" in body:
            for entry in body["entry"]:
                logger.info(f"📮 Processing entry: {entry.get('id')}")
                
                # Handle changes (posts, stories, comments, mentions)
                if "changes" in entry:
                    for change in entry["changes"]:
                        field = change.get("field")
                        value = change.get("value", {})
                        
                        logger.info(f"📝 Field: {field}")
                        logger.info(f"   Value: {value}")
                        
                        # Process based on field type
                        if field == "feed":
                            logger.info(f"   → New post from subscriber")
                            # TODO: Handle new posts
                            # - Update user's feed
                            # - Trigger notifications
                            
                        elif field == "story":
                            logger.info(f"   → New story from subscriber")
                            # TODO: Handle new stories
                            
                        elif field == "comments":
                            logger.info(f"   → New comment on post")
                            # TODO: Handle new comments
                            # - Notify user
                            # - Add to moderation queue
                            
                        elif field == "mentions":
                            logger.info(f"   → New mention")
                            # TODO: Handle mentions
                            # - Notify user
                            # - Store mention data

        logger.info(f"✅ Webhook processed successfully")
        return JSONResponse(content={"status": "ok"})

    except Exception as e:
        logger.error(f"❌ Error processing webhook: {str(e)}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
