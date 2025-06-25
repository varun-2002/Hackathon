#!/usr/bin/env python3

import sys
import os

# Add the leakpatrol directory to the path
sys.path.append('/Users/arundhuti.naskar/slackBotHackathon/python/src/leakpatrol')

from LLMGateway import LLMGateway
from Agent import Agent
import asyncio

def test_llm():
    """Test the LLM functionality using the existing Tester.py approach"""
    
    # Test message
    test_message = "This is a test message to check if the LLM is working properly."
    
    print("Testing LLM functionality...")
    print(f"Test message: {test_message}")
    print("-" * 50)
    
    try:
        # Create LLM client using the same configuration as Tester.py
        client = LLMGateway(
            base_url='https://bot-svc-llm.sfproxy.einstein.aws-dev4-uswest2.aws.sfdc.cl', 
            model='llmgateway__OpenAIGPT4OmniMini',
            api_key='651192c5-37ff-440a-b930-7444c69f4422',
            ssl_ca_cert='/Users/arundhuti.naskar/slackBotHackathon/python/src/leakpatrol/Salesforce_Internal_Root_CA_3.pem',
            feature_id="EinsteinDocsAnswers",
            app_context='EinsteinGPT', 
            core_tenant_id='core/prod1/00DDu0000008cuqMAA'
        )
        
        # Initialize the agent with the LLM client
        myAgent = Agent(llm_client=client)
        
        # Simple system prompt for testing
        system_prompt = "You are a helpful assistant. Please analyze the following message and provide a brief response."
        
        # Use the agent to run a task
        print("Sending request to LLM...")
        response = asyncio.run(myAgent.run(test_message, system_prompt))
        
        print("LLM Response:")
        print(response)
        print("-" * 50)
        print("✅ LLM test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing LLM: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_llm() 