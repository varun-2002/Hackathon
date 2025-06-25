import llmgateway_api
from llmgateway_api.rest import ApiException
from pprint import pprint

# See docs/APIKey.md
API_KEY = "651192c5-37ff-440a-b930-7444c69f4422"

# Defining the host is optional and defaults to https://bot-svc-llm.sfproxy.einstein.dev1-uswest2.aws.sfdc.cl
# See configuration.py for a list of all supported configuration parameters.
configuration = llmgateway_api.Configuration(
    host="https://bot-svc-llm.sfproxy.einstein.dev1-uswest2.aws.sfdc.cl",
    ssl_ca_cert='Salesforce_Internal_Root_CA_3.pem'
)

# Define request headers
headers = {
    "Authorization": f"API_KEY {API_KEY}",
    "x-client-feature-id": "api-key-exploratory",
    "x-client-trace-id": "optional-trace-id",
    "x-request-id": "optional-request-id",
    "x-sfdc-core-tenant-id": "core/falcontest1-core4sdb6/00DOA0000008bMR2AY",
}

# Enter a context with an instance of the API client
with llmgateway_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = llmgateway_api.DefaultApi(api_client)

    embedding_request = llmgateway_api.EmbeddingRequest(
        input=["hello world"],
        model="sfdc_ai__DefaultAzureOpenAITextEmbeddingAda_002",
    )

    generation_request = llmgateway_api.GenerationRequest(
        prompt="Please complete the following movie line: Do not go gentle into that good night",
        model="llmgateway__OpenAIGPT4OmniMini",
    )

    try:
        embeddings_response = api_instance.embeddings(embedding_request, _headers=headers)
        print("The response of DefaultApi->embeddings:\n")
        pprint(embeddings_response)
        print()

        generations_response = api_instance.generations(generation_request, _headers=headers)
        print("The response of DefaultApi->generations:\n")
        pprint(generations_response)
        print()

    except ApiException as e:
        print("Exception when calling DefaultApi: %s\n" % e)