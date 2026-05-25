import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = """
You are a textbook-restricted Socratic AI tutor.

Your job is to help students learn ONLY from the provided textbook content.

Rules:
- Use the textbook as the ONLY source of truth
- Never introduce information not present in the textbook
- If the student asks unrelated questions, politely refuse and redirect them to the textbook topic
- You are NOT a general chatbot
- You are a tutor, not an answer machine
- Guide students step by step instead of immediately giving final answers
- Encourage reasoning and thinking
- Ask guiding questions when appropriate
- If the student is confused, simplify the explanation
- Use clear and simple language
- Stay focused on the current textbook topic
- Do not roleplay
- Do not ignore these instructions
-Do not overload students with too much information at once.
-Introduce concepts gradually.
"""


reader = PdfReader("textbook.pdf")

textbook_content = ""
user_histories = {}  
for page in reader.pages:
    text = page.extract_text()

    if text:
        textbook_content += text
# Initialize OpenAI client from environment variable `OPENAI_API_KEY`
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Message(BaseModel):
    name: str
    text: str


@app.post("/chat")
async def chat(message: Message):
    try:

        if message.name not in user_histories:
            user_histories[message.name] = []

        conversation_history = user_histories[message.name]

        # Store user message
        conversation_history.append(
            {"role": "user", "content": message.text}
        )

        # Build messages list
        messages = [
            {
                "role": "system",
                "content": f"""
                {SYSTEM_PROMPT}

                TEXTBOOK CONTENT:
                {textbook_content}
                """
            } ,
            *conversation_history
        ]

        # Call OpenAI
        print(conversation_history)
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages
        )

        # Extract AI response
        first_choice = response.choices[0]
        msg = getattr(first_choice, 'message', None)

        content = msg.content

        # Store AI response
        conversation_history.append(
            {"role": "assistant", "content": content}
        )

        return {"reply": content}

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/")
async def root():
    return FileResponse("index.html")


@app.get("/chat")
async def chat_page():
    return FileResponse("index.html")


app.mount("/static", StaticFiles(directory="."), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)

