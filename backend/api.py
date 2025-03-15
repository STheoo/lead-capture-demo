from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import sqlite3 

import agent

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


@app.get("/call-agent")
async def call_agent(request: Request):
    
    query = request.query_params.get("query")
    user_id = request.query_params.get("user_id")
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required.")

    response = await agent.handle_user_message(user_id=user_id, message=query)

    # Store chat in database
    cursor.execute(
        "INSERT INTO chatbot_logs (session_id, user_message, bot_response) VALUES (?, ?, ?)",
        (user_id, query, response.data)
    )
    conn.commit()

    return response.data


if __name__ == "__main__":
    print("Running the FastAPI server on port")
    uvicorn.run("api:app", host="0.0.0.0")