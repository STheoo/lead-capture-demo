from typing import Optional, Literal

from dataclasses import dataclass

import requests

from pydantic import BaseModel, Field

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel

from dotenv import load_dotenv
import os

from chromadb import Collection

from vector_db import initialize_chroma
from utils import read_file

load_dotenv()



@dataclass
class LeadDeps:
    airtable_api: str | None
    airtable_app: str | None
    db: Collection | None

openai_model = OpenAIModel('gpt-4o')
agent_system_prompt = read_file("docs/system_prompt.MD")

agent_client = Agent(
    openai_model,
    system_prompt = agent_system_prompt,
    deps_type=LeadDeps,
    instrument=True
)

@agent_client.tool_plain
async def get_cost_estimate(project_type: str, description: str) -> str:
    """Retrieve the price list of all the projects types and sizes.
    
    Args:
        project_type: User's desired project type.
        description: User's desired project description.
    """
    price_list = read_file(f"./docs/price.MD").format(project_type=project_type, description=description)
    
    return price_list

@agent_client.tool
async def retrieve(ctx: RunContext[LeadDeps], search_query: str) -> str:
    """Retrieve documentation sections based on a search query.

    Args:
        ctx: The call context.
        search_query: The search query.
    """
    data = ctx.deps.db.query(
            query_texts=search_query,
            n_results=2,
            include=["documents"]
        )

    return '\n\n'.join(
        data["documents"][0]
    )

class ServiceRequest(BaseModel):
    name: str = Field(description="Full name of the lead")
    location: str = Field(description="The location as in the country the client is based in and would like the service to be based in.")
    phone_number: str = Field(description="Contact phone number")
    email: str = Field(description="Email address")
    type: Literal['Website', 'Mobile App', 'AI Automation', 'IT'] = Field(description="Type of service in interest")
    pages: Optional[str] = Field(description="An approximation of how many pages they expect, if they chose website or mobile app.", default="N/A")
    description: Optional[str] = Field(description="Additional description about what they expect to get.", default="")

@agent_client.tool
async def register_service_request(ctx: RunContext[LeadDeps], request: ServiceRequest) -> dict:
    """Registers a new service request in Airtable.
    
    Args:
        ctx: The call context.
        request: The user and service request details.
    """
    base_url: str = "https://api.airtable.com"

    url = f"{base_url}/v0/{ctx.deps.airtable_app}/SwordLeads"
    headers = {
        "Authorization": f"Bearer {ctx.deps.airtable_api}",
        "Content-Type": "application/json"
    }
    payload = {
        "fields": {
            "Name": request.name,
            "Location": request.location,
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
    
class BusinessInfo(BaseModel):
    industry: str = Field(description="The industry the business is in")
    objectives: str = Field(description="The business objectives and future goals")
    challenges: str = Field(description="The technological challenges the business is currently facing")

@agent_client.tool_plain
async def recommend_services(business_info: BusinessInfo) -> str:
    """Retrieves context on the companies service list and clear instructions on how to recommend a service to the client.

    Args:
        business_info: The user's business information to find fittings services.
    """
    service_list = read_file(f"./docs/recommendation.MD").format(industry=business_info.industry, objectives=business_info.objectives, challenges=business_info.challenges)
    return service_list

chat_histories = {}

async def handle_user_message(user_id: str, message: str):

    if user_id not in chat_histories:
        chat_histories[user_id] = []
    messages = chat_histories[user_id]


    airtable_api = os.getenv('AIR_TABLE_KEY')
    airtable_app = os.getenv('AIR_TABLE_APP')
    db = initialize_chroma()

    deps = LeadDeps(airtable_api=airtable_api, airtable_app=airtable_app, db=db)
    response = await agent_client.run(message, deps=deps, message_history=messages)
    messages = response.all_messages()
    chat_histories[user_id] = messages
    return response