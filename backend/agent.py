from typing import Optional, Literal

from dataclasses import dataclass

import requests

from pydantic import BaseModel, Field

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel

from dotenv import load_dotenv
import os

import chromadb

load_dotenv()

@dataclass
class LeadDeps:
    airtable_api: str | None
    airtable_app: str | None
    db: chromadb.Collection

openai_model = OpenAIModel('gpt-4o')

agent = Agent(
    openai_model,
    system_prompt=
        "You are an expert customer service representative in a software company called Sword Group."
        "Your job is to greet and assist the customer with any questions, but with an objective to get his details."
        "If you do not know the answer to any questions specific about the company, just make stuff up.",
    deps_type=LeadDeps
    )

@agent.tool
async def retrieve(ctx: RunContext[LeadDeps], search_query: str) -> str:
    """Retrieve documentation sections based on a search query.

    Args:
        context: The call context.
        search_query: The search query.
    """
    ctx.dp.collection.query(
        query_texts=search_query,
        n_results=2,
        include=["documents"]
    )

class ServiceRequest(BaseModel):
    name: str = Field(description="Full name of the lead")
    phone_number: str = Field(description="Contact phone number")
    email: str = Field(description="Email address")
    type: Literal['Website', 'Mobile App', 'AI Automation'] = Field(description="Type of service in interest")
    pages: Optional[str] = Field(description="An approximation of how many pages they expect, if they chose website or mobile app.", default="N/A")
    description: Optional[str] = Field(description="Additional description about what they expect to get.", default="")

@agent.tool
async def register_service_request(ctx: RunContext[LeadDeps], request: ServiceRequest) -> dict:
    """Registers a new service request in Airtable."""
    base_url: str = "https://api.airtable.com"

    url = f"{base_url}/v0/{ctx.deps.airtable_app}/SwordLeads"
    headers = {
        "Authorization": f"Bearer {ctx.deps.airtable_api}",
        "Content-Type": "application/json"
    }
    payload = {
        "fields": {
            "Name": request.name,
            "Phone": request.phone_number,
            "Email": request.email,
            "Type": request.type,
            "Pages": request.pages,
            "Description": request.description
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        return {
            "status": "success",
            "data": response.json()
        }
    except requests.RequestException as e:
        return {
            "status": "error",
            "error": str(e),
            "details": response.text if hasattr(response, 'text') else None
        }


chat_histories = {}

async def handle_user_message(user_id: str, message: str):
    airtable_api = os.getenv('AIR_TABLE_KEY')
    airtable_app = os.getenv('AIR_TABLE_APP')

    deps = LeadDeps(airtable_api=airtable_api, airtable_app=airtable_app)


    if user_id not in chat_histories:
        chat_histories[user_id] = []
    messages = chat_histories[user_id]
    response = await agent.run(message, deps=deps, message_history=messages)
    messages = response.all_messages()
    chat_histories[user_id] = messages
    return response