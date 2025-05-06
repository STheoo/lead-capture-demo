from utils import read_file
from pydantic_ai import Agent, RunContext
from typing import List
import asyncio

from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart

import dotenv

dotenv.load_dotenv()

interviewer_system_prompt = read_file("docs/system_prompt_interviewer.MD")


interview_agent = Agent(  
    'openai:gpt-4o',
    system_prompt=interviewer_system_prompt,
    instrument=True
)

class CLI:
    def __init__(self):
        self.messages: List[ModelMessage] = []

    async def chat(self):        
        try:
            while True:
                user_input = input("You: ").strip()
                if user_input.lower() == 'quit':
                    break

                # Run the agent
                result = await interview_agent.run(
                    user_input,
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
            print()

async def main():
    cli = CLI()
    await cli.chat()

if __name__ == "__main__":
    asyncio.run(main())

