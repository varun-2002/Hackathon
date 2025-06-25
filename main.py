from fastapi import FastAPI, Request, HTTPException
from slack_sdk.signature import SignatureVerifier
from config import settings
from slack_handler import slack_handler
import json
import logging
# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)
# Reduce verbosity of other loggers
logging.getLogger('slack_sdk').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
app = FastAPI()
signature_verifier = SignatureVerifier(settings.SLACK_SIGNING_SECRET)
@app.post("/slack/events")
async def slack_events(request: Request):
    # Get the raw body
    body = await request.body()
    body_str = body.decode("utf-8")
    # Verify Slack signature
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")
    if not signature_verifier.is_valid(
        body=body_str,
        timestamp=timestamp,
        signature=signature
    ):
        logger.error("Invalid Slack signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    # Parse the event
    event_data = json.loads(body_str)
    # Handle URL verification
    if event_data.get("type") == "url_verification":
        logger.info("URL verification successful")
        return {"challenge": event_data["challenge"]}
    # Handle events
    event = event_data.get("event", {})
    event_id = event_data.get("event_id")  # Extract event ID for idempotency
    if event.get("type") == "message":
        await slack_handler.handle_message(event, event_id)
    else:
        logger.debug(f"Ignoring event type: {event.get('type')}")
    return {"status": "ok"}
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)






