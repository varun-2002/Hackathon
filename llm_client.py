import requests
from config import settings
import os

class LLMClient:
    def __init__(self):
        self.api_key = settings.EINSTEIN_API_KEY
        self.base_url = "https://api.einstein.ai/v2/vision/predict"  # Replace with actual Einstein Gateway endpoint
        self.ssl_cert_path = "/Users/arundhuti.naskar/slackBotHackathon/python/src/leakpatrol/Salesforce_Internal_Root_CA_3.pem"

    async def process_text(self, text: str) -> dict:
        """
        Process text through Einstein Gateway LLM
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text,
                "model": "your-model-name"  # Replace with actual model name
            }
            
            # Use SSL certificate if it exists
            if os.path.exists(self.ssl_cert_path):
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    verify=self.ssl_cert_path
                )
            else:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"LLM API error: {response.status_code}", "details": response.text}
                
        except Exception as e:
            return {"error": f"Error processing text: {str(e)}"}

llm_client = LLMClient() 