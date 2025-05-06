from pydantic_ai import Agent
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, List
from dotenv import load_dotenv
import json
import asyncio
import os

# Import the message classes from Pydantic AI
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter
)
from pydantic import BaseModel, Field

from vector_db import initialize_chroma
from agents.agent_client import agent_client, LeadDeps
from agents.agent_hr import hr_agent, HRDeps
from agents.agent_interview import interview_agent

import logfire

logfire.configure()

load_dotenv()

class AgentState(TypedDict):
    user_input: str
    messages: Annotated[List[bytes], lambda x, y: x + y]
    role: str
    request: bool

router_agent = Agent(  
    'openai:gpt-4o-mini',
    system_prompt='Your job is to extract the user intent and route the user to either the client agent if it is looking for a service or the careers agent for employees if it is looking for a job.',  
    instrument=True
)

class Candidate(BaseModel):
    role: str = Field(description="The job role the user is interested in.")


extractor_agent = Agent(
    'openai:gpt-4o-mini',
    result_type=Candidate,  # type: ignore
    system_prompt=(
        "Extract me the prefered job role of the canidate looking for a job, make sure that you are extracting a job role and not anything else.",
        "The user will give a lot of irrelevant responses, your job is to identify if the user has specified a job role"
        "If the user has not specified the job role he is looking for, strictly respond with just the word 'None'"
    ),
)

async def client_assist(state: AgentState):

    airtable_api = os.getenv('AIR_TABLE_KEY')
    airtable_app = os.getenv('AIR_TABLE_APP')
    db = initialize_chroma("html")

    deps = LeadDeps(airtable_api=airtable_api, airtable_app=airtable_app, db=db)

    # Get the message history into the format for Pydantic AI
    message_history: list[ModelMessage] = []
    for message_row in state['messages']:
        message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

    result = await agent_client.run(state["user_input"], deps=deps, message_history=message_history)

    return {"messages": [result.new_messages_json()]}

async def hr_assist(state: AgentState):

    airtable_api = os.getenv('AIR_TABLE_KEY')
    airtable_app = os.getenv('AIR_TABLE_APP')
    db = initialize_chroma("vacancies")

    deps = HRDeps(airtable_api=airtable_api, airtable_app=airtable_app, db=db)

    # Get the message history into the format for Pydantic AI
    message_history: list[ModelMessage] = []
    for message_row in state['messages']:
        message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

    result = await hr_agent.run(state["user_input"], deps=deps, message_history=message_history)
    
    extractor_result = await extractor_agent.run(state["user_input"])

    decoded_data = result.new_messages_json().decode('utf-8')
    parsed = json.loads(decoded_data)

    tool_name = None

    for item in parsed:
        if 'parts' in item:
            for part in item['parts']:
                if 'tool_name' in part:
                    tool_name = part['tool_name']
                    break
        if tool_name:
            break

    if tool_name:
        print(f"Found tool_name: {tool_name}")
    else:
        print("No tool_name found.")

    if "register_candidate" == tool_name:
        print("making request true")
        return {
            "request": True,
            "role": extractor_result.data.role,
            "messages": [result.new_messages_json()]
        }
    
    if extractor_result.data.role != 'None':
        return {
            "role": extractor_result.data.role,
            "messages": [result.new_messages_json()]
        }

    return {
        "messages": [result.new_messages_json()]
    }

async def route_user(state: AgentState):

    prompt = f"""
    The user has sent a message: 
    
    {state['user_input']}

    Using the current message and the previous message history determine if it is a client or a potential employee.

    If the user is a client looking for a service, respond with just the text "client_assist".
    If the user is a potential employee looking for a job, respond with just the text "hr_assist".
    """

    request = None
    try: 
        request = state["request"]
    except:
        request = None
    
    if request:
        return "interview_questions"

    # Get the message history into the format for Pydantic AI
    message_history: list[ModelMessage] = []
    for message_row in state['messages']:
        message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

    result = await router_agent.run(prompt, message_history=message_history)
    next_action = result.data

    if next_action == "client_assist":
        return "client_assist"
    else:
        return "hr_assist"
    
async def route_to_interview(state: AgentState):
    request = None
    try: 
        request = state["request"]
    except:
        request = None
    
    if request:
        return "interview_questions"
    else:
        return "END"
    
async def interview_questions(state: AgentState):

    prompt = f"""The users role is {state['role']}.

    The user's reply:
    {state['user_input']}

    If the user's reply is an answer response to a question evaluate his answer otherwise ask an interview question related to his role.
    
    """

    # Get the message history into the format for Pydantic AI
    message_history: list[ModelMessage] = []
    for message_row in state['messages']:
        message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

    result = await interview_agent.run(prompt, message_history=message_history)
    

    return {
        "messages": [result.new_messages_json()]
    }
    

graph_builder = StateGraph(AgentState)

graph_builder.add_node("client_assist", client_assist)
graph_builder.add_node("hr_assist", hr_assist)
graph_builder.add_node("interview_questions", interview_questions)


graph_builder.add_conditional_edges(
    START,
    route_user,
    {"hr_assist": "hr_assist", "client_assist": "client_assist", "interview_questions": "interview_questions"}
)

graph_builder.add_conditional_edges(
    "hr_assist",
    route_to_interview,
    {"END": END, "interview_questions": "interview_questions"}
)

graph_builder.add_edge(["client_assist", "interview_questions"], END)
                                 



# Configure persistence
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

async def graph_invoke(user_input: str):
    config = {"configurable": {"thread_id": "1"}}

    snapshot = graph.get_state(config)

    snapshot = {k: v for k, v in snapshot.values.items() if k in ("role", "request")}

    job_role = ""
    if "role" in snapshot:
        job_role = snapshot['role']
    
    request = False
    if "request" in snapshot:
        request = snapshot['request']

    response = await graph.ainvoke({"user_input": user_input, "role": job_role, "request": request}, config=config)
    decoded_str = response["messages"][-1].decode('utf-8')

    # Load the JSON
    data = json.loads(decoded_str)

    # Get the last item's parts, and then the last part's content
    assistant_message = data[-1]['parts'][-1]['content']
    if(assistant_message != 'Final result processed.'):
        print("Assistant:", assistant_message)
    else:
        print("Assistant: ", response["candidate_details"]['response'])
    


async def main():
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            await graph_invoke(user_input)
        except:
            # fallback if input() is not available
            user_input = "What do you know about LangGraph?"
            print("User: " + user_input)
            await graph_invoke(user_input)
            break

if __name__ == "__main__":
    asyncio.run(main())