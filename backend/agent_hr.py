from chromadb import Collection
from utils import read_file
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field


hr_system_prompt = read_file("docs/system_prompt_hr.MD")

@dataclass
class HRDeps:
    db: Collection | None

class CandidateInfo(BaseModel):
    response: str = Field(description="The response to be given if all the necessary details have not been given.")
    name: str = Field(description="Full name of the candidate")
    phone_number: str = Field(description="Contact phone number")
    email: str = Field(description="Email address")
    role: str = Field(description="The job role the candidate is interested in")
    experience: int = Field(description="The years of experience the candidate has in the specific job role")
    cv_summary: str = Field(description="A detailed summary with all the important information of the cv provided by the candidate.")
    all_details_given: bool = Field(description='True if the user has given all the necessary details, otherwise false')

hr_agent = Agent(  
    'openai:gpt-4o',
    result_type=CandidateInfo,
    system_prompt=hr_system_prompt,
    deps_type=HRDeps,
    instrument=True
)

@hr_agent.tool
async def retrieve(ctx: RunContext[HRDeps], search_query: str) -> str:
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
