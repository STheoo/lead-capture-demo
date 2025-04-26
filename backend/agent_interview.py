from dataclasses import dataclass
from utils import read_file
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field
import requests


interviewer_system_prompt = read_file("docs/system_prompt_interviewer.MD")

@dataclass
class InterviewDeps:
    airtable_api: str | None
    airtable_app: str | None

interview_agent = Agent(  
    'openai:gpt-4o',
    system_prompt=interviewer_system_prompt,
    deps_type=InterviewDeps,
    instrument=True
)


class CandidateInfo(BaseModel):
    name: str = Field(description="Full name of the candidate")
    phone_number: str = Field(description="Contact phone number")
    email: str = Field(description="Email address")
    role: str = Field(description="The job role the candidate is interested in")
    experience: int = Field(description="The years of experience the candidate has in the specific job role")
    cv_summary: str = Field(description="A detailed summary with all the important information of the cv provided by the candidate.")

@interview_agent.tool
async def register_candidate(ctx: RunContext[InterviewDeps], request: CandidateInfo) -> dict:
    """
    Registers a new candidate in the Airtable 'SwordHR' table.

    This function receives candidate details from the screening process and submits 
    them to an Airtable base using the Airtable API. The details include personal 
    contact information, role of interest, experience, and interview notes.

    Args:
        ctx (RunContext[LeadDeps]): The runtime context containing dependencies such as 
            the Airtable app ID and API key.
        request (Candidate): An instance of the Candidate model containing all relevant 
            fields to be submitted to Airtable.

    Returns:
        dict: A dictionary containing:
            - 'status': "success" or "error"
            - 'data': The Airtable API response if successful
            - 'error': Error message string (if any)
            - 'details': Additional error details (if available)
    """
    base_url: str = "https://api.airtable.com"

    url = f"{base_url}/v0/{ctx.deps.airtable_app}/SwordHR"
    headers = {
        "Authorization": f"Bearer {ctx.deps.airtable_api}",
        "Content-Type": "application/json"
    }
    payload = {
        "fields": {
            "Name": request.name,
            "Phone": request.phone_number,
            "Email": request.email,
            "Role": request.role,
            "Experience": request.experience,
            "CV_Summary": request.cv_summary,
            "Questions_Rating": request.questions_rating
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
    