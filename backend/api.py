from fastapi import FastAPI, Request, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

import json

import sqlite3 

from agent_graph import graph

import fitz  # PyMuPDF
import io

import vector_db

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    pdf_stream = io.BytesIO(pdf_bytes)
    doc = fitz.open(stream=pdf_stream, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

load_dotenv()

app = FastAPI(title="Website Lead Generation Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
conn = sqlite3.connect("chatbot_logs.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS chatbot_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        user_message TEXT,
        bot_response TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

@app.get("/")
@app.get("/health")
def check_health():
    return {"status": "ok"}


@app.get("/call-graph")
async def call_agent(request: Request):
    
    query = request.query_params.get("query")
    thread_id = request.query_params.get("thread_id")
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required.")

    config = {"configurable": {"thread_id": thread_id}}
    response = await graph.ainvoke({"user_input": query}, config=config)

    decoded_str = response["messages"][-1].decode('utf-8')

    # Load the JSON
    data = json.loads(decoded_str)

    # Get the last item's parts, and then the last part's content
    assistant_message = data[-1]['parts'][-1]['content']

    # Store chat in database
    cursor.execute(
        "INSERT INTO chatbot_logs (session_id, user_message, bot_response) VALUES (?, ?, ?)",
        (thread_id, query, assistant_message)
    )
    conn.commit()

    return assistant_message


@app.post("/call-graph-file")
async def call_graph(request: Request, file: UploadFile = File(...)):

    query = request.query_params.get("query")
    thread_id = request.query_params.get("thread_id")
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required.")

    pdf_bytes = await file.read()
    extracted_text = extract_text_from_pdf_bytes(pdf_bytes)

    input = "User query: \n" + query + "\n CV: \n" + extracted_text
    
    config = {"configurable": {"thread_id": thread_id}}
    response = await graph.ainvoke({"user_input": input}, config=config)

    decoded_str = response["messages"][-1].decode('utf-8')

    # Load the JSON
    data = json.loads(decoded_str)

    # Get the last item's parts, and then the last part's content
    assistant_message = data[-1]['parts'][-1]['content']

    # Store chat in database
    cursor.execute(
        "INSERT INTO chatbot_logs (session_id, user_message, bot_response) VALUES (?, ?, ?)",
        (thread_id, query, assistant_message)
    )
    conn.commit()

    return assistant_message



if __name__ == "__main__":
    SOURCES = [
        "https://www.linkedin.com/jobs/search/?currentJobId=3363425295&geoId=104677530&keywords=Sword%20Group&location=Gr%C3%A8ce&refresh=true",
        "https://www.linkedin.com/jobs/search/?currentJobId=3366796081&geoId=100565514&keywords=Sword%20Group&location=Belgique&refresh=true",
        "https://www.linkedin.com/jobs/search/?currentJobId=3342529388&geoId=101174742&keywords=Sword%20Group&location=Canada&refresh=true",
        "https://www.linkedin.com/jobs/search/?currentJobId=4195462375&geoId=105015875&keywords=Sword%20Group&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true",
        "https://www.linkedin.com/jobs/search/?currentJobId=4203618701&geoId=101834488&keywords=Sword%20Group&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true",
        "https://www.linkedin.com/jobs/search/?currentJobId=4202859244&geoId=104042105&keywords=Sword%20Group&origin=JOB_SEARCH_PAGE_LOCATION_AUTOCOMPLETE&refresh=true",
        "https://www.linkedin.com/jobs/search/?currentJobId=4204626167&geoId=105646813&keywords=Sword%20Group&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true",
        "https://www.linkedin.com/jobs/search/?currentJobId=4204766896&geoId=106693272&keywords=Sword%20Group&origin=JOB_SEARCH_PAGE_LOCATION_AUTOCOMPLETE&refresh=true",
        "https://www.linkedin.com/jobs/search/?currentJobId=4209519002&geoId=101165590&keywords=Sword%20Group&origin=JOB_SEARCH_PAGE_LOCATION_AUTOCOMPLETE&refresh=true",

]

    #Update vector database
    collection = vector_db.initialize_chroma("vacancies")
    chunks = []
    for source in SOURCES:
        try:
            doc = vector_db.parse_doc(source)
            chunks += vector_db.chunk(doc)
        except:
            print("Parsing failed. HTTP Error.")
    vector_db.update_database(collection, chunks)

    print("Running the FastAPI server on port")
    uvicorn.run("api:app", host="0.0.0.0")