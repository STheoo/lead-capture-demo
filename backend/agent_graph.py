from pydantic_ai import Agent, RunContext
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, List, Dict
from dotenv import load_dotenv
import json
import asyncio
import os
from langgraph.types import interrupt

# Import the message classes from Pydantic AI
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter
)

from vector_db import initialize_chroma
from agent_client import agent_client, LeadDeps
from agent_hr import hr_agent, HRDeps
from agent_interview import interview_agent, InterviewDeps

import logfire

logfire.configure()

load_dotenv()

class AgentState(TypedDict):
    user_input: str
    messages: Annotated[List[bytes], lambda x, y: x + y]

    candidate_details: Dict[str, any]

router_agent = Agent(  
    'openai:gpt-4o-mini',
    system_prompt='Your job is to extract the user intent and route the user to either the client agent if it is looking for a service or the careers agent for employees if it is looking for a job.',  
    instrument=True
)

route_to_interview_agent = Agent(  
    'openai:gpt-4o-mini',
    system_prompt='Your job is to determine whether the user provided enough details to route the user to interview questions',  
    instrument=True
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

async def hr_assist(state: AgentState, writer):

    db = initialize_chroma("vacancies")

    deps = HRDeps(db=db)

    # Get the message history into the format for Pydantic AI
    message_history: list[ModelMessage] = []
    for message_row in state['messages']:
        message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

    result = await hr_agent.run(state["user_input"], deps=deps, message_history=message_history)

    return {
        "candidate_details": result.data.model_dump(),
        "messages": [result.new_messages_json()]
    }

async def interview_questions(state: AgentState):

    prompt=f"""
    use these details of the candidate
    {state["candidate_details"]}

    the user input:
    {state["user_input"]}
    """

    airtable_api = os.getenv('AIR_TABLE_KEY')
    airtable_app = os.getenv('AIR_TABLE_APP')

    deps = InterviewDeps(airtable_api=airtable_api, airtable_app=airtable_app)

    # Get the message history into the format for Pydantic AI
    message_history: list[ModelMessage] = []
    for message_row in state['messages']:
        message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

    result = await interview_agent.run(prompt, deps=deps, message_history=message_history)

    return {"messages": [result.new_messages_json()]}

async def route_user(state: AgentState):

    print(state["candidate_details"])

    candidate_details = state["candidate_details"]
    if candidate_details.get("all_details_given", False):
        return "interview_questions"

    prompt = f"""
    The user has sent a message: 
    
    {state['user_input']}

    Using the current message and the previous message history determine if it is a client or a potential employee.

    If the user is a client looking for a service, respond with just the text "client_assist".
    If the user is a potential employee looking for a job, respond with just the text "hr_assist".
    """

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
    candidate_details = state["candidate_details"]

    if not candidate_details.get("all_details_given", False):
        return "get_next_user_message"
    
    return "interview_questions"

graph_builder = StateGraph(AgentState)

graph_builder.add_node("client_assist", client_assist)
graph_builder.add_node("hr_assist", hr_assist)
graph_builder.add_node("interview_questions", interview_questions)

graph_builder.add_conditional_edges(
    START,
    route_user,
    {"hr_assist":"hr_assist", "client_assist":"client_assist","interview_questions":"interview_questions"}
)

graph_builder.add_edge(["hr_assist", "client_assist", "interview_questions"], END)
                                 



# Configure persistence
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

async def graph_invoke(user_input: str):
    config = {"configurable": {"thread_id": "1"}}
    response = await graph.ainvoke({"user_input": user_input, "candidate_details":{}}, config=config)
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