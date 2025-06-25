import os

from langchain_einsteingpt import EinsteinGPTLLM

url = "https://bot-svc-llm.sfproxy.einstein.dev1-uswest2.aws.sfdc.cl"
# The certificate is not checked into git control.
# Please add your certificate with the right file path.
ssl_ca_cert = "Salesforce_Internal_Root_CA_3.pem"

# Get environment variables from .env file (for local dev only).

feature_id = 'EinsteinDocsAnswers'
app_context = 'EinsteinGPT'
core_tenant_id = 'core/prod1/00DDu0000008cuqMAA'
api_key='651192c5-37ff-440a-b930-7444c69f4422'

llm = EinsteinGPTLLM(
    access_token=f"API_KEY {api_key}",
    app_context=app_context,
    sfdc_core_tenant_id=core_tenant_id,
    model="llmgateway__OpenAIGPT35Turbo",
    ssl_ca_cert=ssl_ca_cert,
    url=url,
    x_client_feature_id=feature_id,
)
print(llm)
output = llm("Recommend 5 classic books on software engineering")
print(output)