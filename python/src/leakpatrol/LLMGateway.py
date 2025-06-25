from typing import Dict, Any, List
import asyncio
import os
import typing
import json
import uuid

import llmgateway_api
from llmgateway_api.rest import ApiException
from pprint import pprint

#from llmgateway_api.models.chat_message_request import ChatMessageRequest
from models_api.models.chat_message_request import ChatMessageRequest
from llmgateway_api.models.embedding_request import EmbeddingRequest
from llmgateway_api.models.generation_request import GenerationRequest
from llmgateway_api.models.chat_messages_request import ChatMessagesRequest
from llmgateway_api.models.generation_settings import GenerationSettings
from llmgateway_api.models.chat_messages_generation_response import (
    ChatMessagesGenerationResponse,
)
import models_api
import models_extensions
from models_api.rest import ApiException
from pprint import pprint


def create_chat_message(role: str, content: str) -> dict[str, str]:
    """
    Returns chat_message dict
    """
    return {"role": role, "content": content}



class LLMGateway:
    """
    Interacts with OpenAI's API for chat completions.
    """
    def __init__(self, model: str, api_key: str = None, base_url: str = None, ssl_ca_cert:str = None, feature_id:str = None, app_context:str = None, core_tenant_id:str = None):
        """
        Initialize with model, API key, and base URL.
        """
        
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.ssl_ca_cert = ssl_ca_cert
        self.feature_id = feature_id
        self.app_context = app_context
        self.core_tenant_id = core_tenant_id

        self.headers = {
            "Authorization": f"API_KEY {self.api_key}",
            "x-client-feature-id": self.feature_id,
            "x-client-trace-id": "optional-trace-id",
            "x-request-id": "optional-request-id",
            "x-sfdc-core-tenant-id": self.core_tenant_id,
        }
       

        self.configuration = llmgateway_api.Configuration(host=base_url,ssl_ca_cert=ssl_ca_cert)
        #api_client = llmgateway_api.ApiClient(configuration)
        # Create an instance of the API class
        #self.api_instance = llmgateway_api.DefaultApi(api_client)

        #print(self.api_instance)

    @staticmethod
    def chat_messages_request(model, user_message, system_message, **kwargs):
        """
        Method to create chat_message_request
        """
        chat_message_requests = []
        if system_message:
            system_message_request = ChatMessageRequest(**create_chat_message(role='system', content=system_message))
            chat_message_requests.append(system_message_request)

        if user_message:
            user_message_request = ChatMessageRequest(**create_chat_message(role='user', content=user_message))
            chat_message_requests.append(user_message_request)

        generation_settings_dict = {
            "num_generations": 1,
            "stop_sequences": [],
            "parameters": {
                "top_p": 0.1,
                "temperature": 0.1,
            }
        }
        generation_settings_dict.update(**kwargs)
        generation_settings = GenerationSettings(**generation_settings_dict)


        chat_generation_request_dict = {
            "model": model,
            "messages": chat_message_requests,
            "user_message": user_message,
            "generation_settings": generation_settings
        }

        if "tools" in kwargs:
            chat_generation_request_dict["tools"] = kwargs["tools"]

        if "tool_config" in kwargs:
            chat_generation_request_dict["tool_config"] = kwargs["tool_config"]

        return ChatMessagesRequest(**chat_generation_request_dict)
    
    async def chat_generate(self, user_message, system_message, **kwargs):
        """
        Returns LLM gateway response for chat generation
        """
        with models_api.ApiClient(self.configuration) as api_client:
            # Create an instance of the API class
            api_instance = models_api.DefaultApi(api_client)

            chat_message_requests = []
            if system_message:
                system_message_request = ChatMessageRequest(**create_chat_message(role='system', content=system_message))
                chat_message_requests.append(system_message_request)

            if user_message:
                user_message_request = ChatMessageRequest(**create_chat_message(role='user', content=user_message))
                chat_message_requests.append(user_message_request)


            chat_generations_request = models_api.ChatGenerationsRequest(
                messages=chat_message_requests
            )

            try:
                chat_generations_response = api_instance.create_chat_generations(
                    self.model, chat_generations_request, _headers=self.headers
                )
                print("The response of DefaultApi->create_chat_generations:\n")
                pprint(chat_generations_response)
                print()
                
                content_value = chat_generations_response.generation_details.generations[0].content
                print(content_value)

                return chat_generations_response

            except ApiException as e:
                print("Exception when calling DefaultApi->create_chat_generations: %s\n" % e)
                raise e
    
    def generate(self, prompt, max_new_tokens=None, num_generations=1, temperature=None, parameters=None):
        """
        LLM Gateway prompt generation method
        """
        with llmgateway_api.ApiClient(self.configuration) as api_client:
            # Create an instance of the API class
            api_instance = llmgateway_api.DefaultApi(api_client)
            generation_request_dict = {
                "prompt": prompt,
                "model": self.model,
                "enable_output_safety_scoring": False,
                "num_generations": num_generations,
            }
            if max_new_tokens:
                generation_request_dict['max_tokens'] = max_new_tokens
            if temperature:
                generation_request_dict['temperature'] = temperature
            if parameters:
                generation_request_dict['parameters'] = parameters

            try:
                generation_request = GenerationRequest(**generation_request_dict)

                print("Fetching generations response...")
                generations_api_response = api_instance.generations(generation_request, _headers=self.headers)
        
                generations = []
                for generation in generations_api_response.generations:
                   generations.append({"message": {"content": generation.text, "role": "assistant"}})
                
                print(generations)

                return {"choices": generations}
            except llmgateway_api.ApiException as exc:
                print("Exception when calling DefaultApi->generate: %s", exc)
                raise exc

    