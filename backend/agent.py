from typing import Optional

import requests

from pydantic import BaseModel, Field

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from dotenv import load_dotenv
import os

load_dotenv()

openai_model = OpenAIModel('gpt-4o')

agent = Agent(
    openai_model,
    system_prompt=
        "You are an expert customer service representative in a software company called Sword Group."
        "Your job is to greet and assist the customer with any questions, but with an objective to get his details."
        "If you do not know the answer to any questions specific about the company, just make stuff up."
    )

class ServiceRequest(BaseModel):
    name: str = Field(description="Full name of the lead")
    phone_number: str = Field(description="Contact phone number")
    email: str = Field(description="Email address")
    description: Optional[str] = Field(description="Additional description", default="")

@agent.tool_plain
async def register_service_request(request: ServiceRequest):
    """Registers a new service request in Airtable."""
    base_url: str = "https://api.airtable.com"
    api_key: str = os.getenv("AIR_TABLE_KEY")
    app_id: str = os.getenv("AIR_TABLE_APP")
    url = f"{base_url}/v0/{app_id}/SwordLeads"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "fields": {
            "Name": request.name,
            "Phone": request.phone_number,
            "Email": request.email,
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
