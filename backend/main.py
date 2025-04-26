import asyncio
import os
from dotenv import load_dotenv
from typing import List

from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from agent_client import agent, LeadDeps

from vector_db import initialize_chroma

load_dotenv()

class CLI:
    def __init__(self):
        self.messages: List[ModelMessage] = []
        self.deps = LeadDeps(
            airtable_api = os.getenv('AIR_TABLE_KEY'),
            airtable_app = os.getenv('AIR_TABLE_APP'),
            db = initialize_chroma()
        )

    async def chat(self):        
        try:
            while True:
                user_input = input("You: ").strip()
                if user_input.lower() == 'quit':
                    break

                # Run the agent
                result = await agent.run(
                    user_input,
                    deps=self.deps,
                    message_history=self.messages
                )

                # Store the user message
                self.messages.append(
                    ModelRequest(parts=[UserPromptPart(content=user_input)])
                )

                # Store itermediatry messages like tool calls and responses
                filtered_messages = [msg for msg in result.new_messages() 
                                if not (hasattr(msg, 'parts') and 
                                        any(part.part_kind == 'user-prompt' or part.part_kind == 'text' for part in msg.parts))]
                self.messages.extend(filtered_messages)

                print("Agent: ", result.data)

                # Add the final response from the agent
                self.messages.append(
                    ModelResponse(parts=[TextPart(content=result.data)])
                )
        finally:
            await self.deps.client.aclose()

async def main():
    cli = CLI()
    await cli.chat()

if __name__ == "__main__":
    asyncio.run(main())