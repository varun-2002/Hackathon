from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config import settings
import sys
import os
import asyncio
import re
import time

# Add the leakpatrol directory to the path
sys.path.append('/Users/vvarunraju/Documents/Projects/slackBotHackathon/python/src/leakpatrol')

from LLMGateway import LLMGateway
from Agent import Agent
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

class SlackHandler:
    def __init__(self):
        self.client = WebClient(token=settings.SLACK_BOT_TOKEN)
        
        # Track processed event IDs to prevent duplicate processing
        self.processed_events = set()
        
        # Get bot user ID to prevent self-response loops
        try:
            auth_response = self.client.auth_test()
            self.bot_user_id = auth_response["user_id"]
            logger.info(f"Bot user ID: {self.bot_user_id}")
        except Exception as e:
            logger.error(f"Error getting bot user ID: {e}")
            self.bot_user_id = None
        
        # Initialize LLM client using the same configuration as Tester.py
        self.llm_client = LLMGateway(
            base_url='https://bot-svc-llm.sfproxy.einstein.aws-dev4-uswest2.aws.sfdc.cl', 
            model='llmgateway__OpenAIGPT4OmniMini',
            api_key='651192c5-37ff-440a-b930-7444c69f4422',
            feature_id="EinsteinDocsAnswers",
            app_context='EinsteinGPT', 
            core_tenant_id='core/prod1/00DDu0000008cuqMAA'
        )
        
        # Initialize the agent with the LLM client
        self.agent = Agent(llm_client=self.llm_client)

    async def handle_message(self, event: dict, event_id: str = None) -> None:
        """
        Handle incoming Slack messages
        """
        try:
            # Check if we've already processed this event (idempotency)
            if event_id and event_id in self.processed_events:
                logger.debug(f"Event {event_id} already processed, skipping")
                return
            
            # Ignore messages from bots to prevent loops
            if event.get("bot_id"):
                logger.debug("Ignoring bot message")
                return

            # Ignore messages from our own bot to prevent loops
            if event.get("user") == self.bot_user_id:
                logger.debug("Ignoring message from our own bot")
                return

            # Ignore very old messages (older than 5 minutes) to prevent processing historical messages
            event_ts = float(event.get('ts', 0))
            current_ts = time.time()
            if current_ts - event_ts > 300:  # 5 minutes = 300 seconds
                logger.debug(f"Ignoring old message (age: {current_ts - event_ts:.1f}s)")
                return

            # Get the message text
            text = event.get("text", "")
            channel = event.get("channel")
            user_id = event.get("user")
            
            # Skip empty messages
            if not text.strip():
                logger.debug("Skipping empty message")
                return
            
            logger.info(f"📝 Processing: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            # Process text through LLM for leak detection
            llm_response = await self.analyze_for_leaks(text)
            
            # Only respond if a leak is detected
            if "error" in llm_response:
                logger.error(f"LLM error: {llm_response['error']}")
            elif llm_response.get("leak_detected", False):
                # Leak detected - send threaded response with mention
                response_text = self._format_leak_alert(llm_response, user_id)
                
                logger.warning(f"🚨 LEAK DETECTED: {llm_response.get('leak_type', 'Unknown')} - {llm_response.get('severity', 'Unknown')}")
                #await self.chat_postEphemeral(channel, response_text, event.get("ts"))
                self.client.chat_postEphemeral(channel=channel, text=response_text, user=user_id)
                logger.info("✅ Leak alert sent")
            else:
                # No leak detected - just log it silently
                logger.info("✅ No leak detected")
            
            # Mark this event as processed
            if event_id:
                self.processed_events.add(event_id)

        except SlackApiError as e:
            logger.error(f"Slack API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()

    async def analyze_for_leaks(self, text: str) -> dict:
        """
        Analyze text for potential information leaks using the LLM
        """
        try:
            start_time = time.time()
            
            # System prompt for leak detection (same as Tester.py)
            system_prompt = """
            Objective: To identify instances where users are potentially leaking sensitive information, such as Personally Identifiable Information (PII), internal server details, confidential project information, or other restricted data, during conversations with external employees or parties.

            Instructions: Analyze the following conversation transcript and determine if any sensitive information has been shared. Pay close attention to the speaker labels (Internal/External) to determine the context and sensitivity of the information shared. Consider the relationship between the speakers (internal employee vs. external party). Pay close attention to keywords and phrases that might indicate a leak.

            Criteria for Identifying Sensitive Information Leaks:

            * Personally Identifiable Information (PII): This includes, but is not limited to:
                * Full names
                * Addresses (physical and email)
                * Phone numbers
                * Social Security numbers (or equivalent national ID)
                * Credit card numbers
                * Passport numbers
                * Dates of birth
                * Medical information
                * Biometric data

            * Internal Server Details: Information about internal systems, infrastructure, or network configurations, such as:
                * Server names or IP addresses
                * Domain names
                * Internal URLs
                * Database details
                * API keys or credentials
                * Firewall rules

            * Confidential Project Information: Details about ongoing or planned projects that are not yet publicly released, including:
                * Project names
                * Code names
                * Technical specifications
                * Financial details
                * Marketing plans
                * Strategic discussions

            * Company-Specific Sensitive Information: This may include:
                * Internal policies or procedures
                * Legal documents (unless explicitly approved for external sharing)
                * Financial reports (unless publicly available)
                * Customer lists or data (unless anonymized and permitted)
                * Employee information (salaries, performance reviews, etc.)

            * Other Restricted Data: Any other information that is marked as confidential or restricted by the company.

            Output Format:

            * Leak Detected: (Yes/No)
            * Type of Information Leaked (if applicable): (PII, Internal Server Details, Confidential Project Information, Company-Specific Sensitive Information, Other Restricted Data, None)
            * Specific Examples from Transcript (with context): Provide specific excerpts from the transcript that demonstrate the leak, including the surrounding conversation for context. Highlight the sensitive information.
            * Severity of Leak (if applicable): (Low, Medium, High, None)
            * Explanation of Severity: Briefly explain why the leak is considered the assigned severity.
            * Recommendations (if applicable): Suggest actions to mitigate the risk or prevent future leaks.
            """

            user_prompt = f"""
            Conversation Transcript:
            ```
            {text}
            ```
            """

            # Use the agent to run the task
            response = await self.agent.run(user_prompt, system_prompt)
            
            llm_time = time.time() - start_time
            logger.debug(f"LLM response in {llm_time:.2f}s")
            
            # Check if response is None or empty
            if response is None:
                logger.error("LLM returned None response")
                return {"error": "LLM returned None response"}
            
            if not isinstance(response, str):
                logger.error(f"LLM returned unexpected type: {type(response)}")
                return {"error": f"LLM returned unexpected type: {type(response)}"}
            
            if not response.strip():
                logger.error("LLM returned empty response")
                return {"error": "LLM returned empty response"}
            
            # Extract information from the response
            leak_status = self.extract_leak_status(response)
            leak_type = self.extract_leak_type(response)
            severity = self.extract_severity(response)
            recommendations = self.extract_recommendations(response)
            
            return {
                "leak_detected": leak_status == "Yes",
                "leak_status": leak_status,
                "leak_type": leak_type,
                "severity": severity,
                "recommendations": recommendations,
                "full_response": response,
                "status": "success"
            }
                
        except Exception as e:
            logger.error(f"Error analyzing for leaks: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": f"Error analyzing for leaks: {str(e)}"}

    def extract_leak_status(self, llm_output):
        """Extract leak detection status from LLM response"""
        if llm_output:
            match = re.search(r"Leak Detected:\s*(Yes|No)", llm_output)
            if match:
                return match.group(1)
        return "Unknown"

    def extract_leak_type(self, llm_output):
        """Extract leak type from LLM response"""
        if llm_output:
            match = re.search(r"Type of Information Leaked.*?:\s*(.*?)(?:\n|$)", llm_output, re.DOTALL)
            if match:
                return match.group(1).strip()
        return "None"

    def extract_severity(self, llm_output):
        """Extract severity from LLM response"""
        if llm_output:
            match = re.search(r"Severity of Leak.*?:\s*(Low|Medium|High|None)", llm_output)
            if match:
                return match.group(1)
        return "None"

    def extract_recommendations(self, llm_output):
        """Extract recommendations from LLM response"""
        if llm_output:
            match = re.search(r"Recommendations.*?:\s*(.*?)(?:\n\n|$)", llm_output, re.DOTALL)
            if match:
                return match.group(1).strip()
        return "None"

    async def send_message(self, channel: str, text: str) -> None:
        """
        Send a message to a Slack channel
        """
        try:
            self.client.chat_postMessage(
                channel=channel,
                text=text
            )
            logger.info(f"Message sent to channel {channel}")
        except SlackApiError as e:
            logger.error(f"Error sending message: {str(e)}")

    def _format_leak_response(self, response: dict) -> str:
        """
        Format the leak detection response for Slack
        """
        if not response.get("leak_detected", False):
            return "✅ **No information leaks detected** in this message. The content appears to be safe for sharing."
        
        # Format response for detected leaks
        formatted_response = "🚨 **INFORMATION LEAK DETECTED** 🚨\n\n"
        
        if response.get("leak_type"):
            formatted_response += f"**Type of Leak:** {response['leak_type']}\n"
        
        if response.get("severity"):
            severity_emoji = {
                "Low": "🟡",
                "Medium": "🟠", 
                "High": "🔴"
            }.get(response['severity'], "⚪")
            formatted_response += f"**Severity:** {severity_emoji} {response['severity']}\n"
        
        if response.get("recommendations"):
            formatted_response += f"\n**Recommendations:**\n{response['recommendations']}\n"
        
        formatted_response += "\n⚠️ **Please review this message and consider removing sensitive information before sharing.**"
        
        return formatted_response

    def _format_leak_alert(self, response: dict, user_id: str) -> str:
        """
        Format the leak detection alert for Slack with user mention
        """
        if not response.get("leak_detected", False):
            return "✅ *No information leaks detected* in this message. The content appears to be safe for sharing."
        
        # Mention the user who posted the message
        user_mention = f"<@{user_id}>"
        
        # Format response for detected leaks
        formatted_response = f"{user_mention} 🚨 *INFORMATION LEAK DETECTED* 🚨\n\n"
        
        if response.get("leak_type"):
            formatted_response += f"*🔍 Type of Leak:* {response['leak_type']}\n"
        
        if response.get("severity"):
            severity_emoji = {
                "Low": "🟡",
                "Medium": "🟠", 
                "High": "��"
            }.get(response['severity'], "⚪")
            formatted_response += f"*⚠️ Severity:* {severity_emoji} {response['severity']}\n"
        
        if response.get("recommendations"):
            formatted_response += f"\n*🛠️ Immediate Actions:*\n{response['recommendations']}\n"
        
        formatted_response += f"\n*📋 Next Steps:*\n"
        formatted_response += f"• Review and edit the message to remove sensitive information\n"
        formatted_response += f"• Consider if this information should be shared in a private channel\n"
        formatted_response += f"• Report to your security team if this was unintentional\n"
        
        formatted_response += f"\n💡 *Tip:* When sharing information, consider if it contains PII, internal systems, or confidential project details."
        
        return formatted_response

    async def send_threaded_message(self, channel: str, text: str, thread_ts: str) -> None:
        """
        Send a threaded message to a Slack channel
        """
        try:
            self.client.chat_postMessage(
                channel=channel,
                text=text,
                thread_ts=thread_ts
            )
            logger.info(f"Threaded message sent to channel {channel}")
        except SlackApiError as e:
            logger.error(f"Error sending threaded message: {str(e)}")

slack_handler = SlackHandler() 