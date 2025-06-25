from typing import Dict, Any, List

class Agent:
    """
    Integrates LLM client, tools, and memory.
    """
    def __init__(self, llm_client=None, tools=None, memory=None):
        self.llm_client = llm_client
        self.tools = tools
        self.memory = memory

    async def run(self,  user_message, system_message):
        """
        Placeholder for the agent's main execution logic.
        """
        response = await self.llm_client.chat_generate(user_message, system_message)
        
        # Extract the content from the response object
        if response and hasattr(response, 'generation_details') and response.generation_details:
            if hasattr(response.generation_details, 'generations') and response.generation_details.generations:
                if len(response.generation_details.generations) > 0:
                    generation = response.generation_details.generations[0]
                    if hasattr(generation, 'content'):
                        return generation.content
        
        # Fallback: return the raw response if we can't extract content
        return str(response) if response else "No response from LLM"