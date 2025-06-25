# Setup client with environment variables
from LLMGateway import LLMGateway
from Agent import Agent
import asyncio
import re


# Replace with your actual LLM API call function
def llm_api_call(system_prompt, user_prompt):
    client = LLMGateway(base_url='https://bot-svc-llm.sfproxy.einstein.aws-dev4-uswest2.aws.sfdc.cl', model='llmgateway__OpenAIGPT4OmniMini',
                    api_key='651192c5-37ff-440a-b930-7444c69f4422',
                    feature_id="EinsteinDocsAnswers",app_context='EinsteinGPT', core_tenant_id='core/prod1/00DDu0000008cuqMAA')
    # Initialize the agent with the LLM client
    myAgent = Agent(llm_client=client)

    # Use the agent to run a task
    response = asyncio.run(myAgent.run(user_prompt, system_prompt))
    print(response)


  

def analyze_conversation(transcript):
    
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
    Give the output in json format
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
    {transcript}
    ```
    """

    try:
        llm_output = llm_api_call(system_prompt, user_prompt)  # Call your LLM API
        print(llm_output)
        return llm_output

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def extract_leak_status(llm_output):
    if llm_output:
        match = re.search(r"Leak Detected:\s*(Yes|No)", llm_output)
        if match:
            return match.group(1)
    return "Unknown"

def extract_leak_type(llm_output):
    if llm_output:
        match = re.search(r"Type of Information Leaked:\s*(.*)", llm_output)
        if match:
            return match.group(1).strip()
    return "None"

def extract_leak_details(llm_output):
    leak_details = []
    if llm_output:
        # Example regex (adapt as needed):
        matches = re.findall(r"Specific Examples from Transcript.*?\"(.*?)\".*?(Internal|External) Employee (.*?):.*?(Internal|External) Employee (.*?):", llm_output, re.DOTALL)
        for match in matches:
            leaked_info, leaker_role, leaker_name, recipient_role, recipient_name = match
            leak_details.append({
                "leaked_info": leaked_info.strip(),
                "leaker_role": leaker_role.strip(),
                "leaker_name": leaker_name.strip(),
                "recipient_role": recipient_role.strip(),
                "recipient_name": recipient_name.strip()
            })
    return leak_details


# Example usage:
conversation1 = """
Internal Employee Alice: Hey, I'm working on the new "Project X" with John from marketing.
External Vendor Bob: Cool! What's Project X about?
Internal Employee Alice: It's top secret, but we're using the "phoenix" server for development. My email is alice@internal.example.com.
"""

conversation2 = """
Internal Employee Carol: We had a problem with the database yesterday.
External Consultant David: Oh no, what happened?
Internal Employee Carol: It was a minor issue. We just restarted the 'db-cluster-01' instance.
"""

output1 = analyze_conversation(conversation1)
leak_status1 = extract_leak_status(output1)
leak_type1 = extract_leak_type(output1)
leak_details1 = extract_leak_details(output1)
print(f"Leak status for conversation 1: {leak_status1}")
print(f"Leak type for conversation 1: {leak_type1}")
print(f"Leak details for conversation 1: {leak_details1}")

print("-" * 20)

output2 = analyze_conversation(conversation2)
leak_status2 = extract_leak_status(output2)
leak_type2 = extract_leak_type(output2)
leak_details2 = extract_leak_details(output2)
print(f"Leak status for conversation 2: {leak_status2}")
print(f"Leak type for conversation 2: {leak_type2}")
print(f"Leak details for conversation 2: {leak_details2}")