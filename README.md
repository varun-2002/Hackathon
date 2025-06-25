# Slack LLM Bot

This is a Slack bot that processes messages through an LLM using FastAPI.

## Setup Instructions

1. Create a Slack App:
   - Go to https://api.slack.com/apps
   - Click "Create New App"
   - Choose "From scratch"
   - Name your app and select your workspace

2. Configure Bot Permissions:
   - Go to "OAuth & Permissions"
   - Add the following bot token scopes:
     - `channels:history`
     - `chat:write`
     - `app_mentions:read`
     - `channels:read`
     - `groups:read`
     - `im:read`
     - `mpim:read`

3. Subscribe to Events:
   - Go to "Event Subscriptions"
   - Enable events
   - Subscribe to the following bot events:
     - `message.channels`
     - `message.groups`
     - `message.im`
     - `message.mpim`

4. Environment Setup:
   - Create a `.env` file with the following variables:
     ```
     SLACK_BOT_TOKEN=xoxb-your-bot-token
     SLACK_SIGNING_SECRET=your-signing-secret
     EINSTEIN_API_KEY=your-einstein-api-key
     ```

5. Install Dependencies:
   ```bash
   pip install -r requirements.txt
   ```

6. Run the Server:
   ```bash
   uvicorn main:app --reload
   ```

## Project Structure

- `main.py`: FastAPI server and main application logic
- `config.py`: Configuration and environment variables
- `slack_handler.py`: Slack event handling and message processing
- `llm_client.py`: LLM integration with Einstein Gateway
- `requirements.txt`: Project dependencies
- `.env`: Environment variables (not tracked in git) 