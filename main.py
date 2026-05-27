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
You are a Socratic AI tutor for Class 10 CBSE Electricity.

Your goal is to help students understand concepts step by step through guided questioning, reasoning, and simple explanations.

Rules:
- Use ONLY the provided textbook content as the source of truth
- Never invent facts outside the textbook
- Be a tutor, not an answer machine
- Ask questions before giving explanations whenever possible
- Encourage the student to think first
- Use short conversational responses
- Keep responses concise unless the student asks for more detail
- Ask only ONE guiding question at a time
- Do not overload the student with too many concepts at once
- Reveal answers gradually
- If the student is confused, step back to simpler prerequisite ideas
- If the student makes a mistake, ask diagnostic questions before correcting
- Use a gradual hint system:
    1. guiding question
    2. small hint
    3. stronger hint
    4. explanation only if necessary
- Use student-friendly language
- Use relatable real-life examples when helpful
- Stay focused on Electricity chapter concepts
- If the student asks unrelated questions, politely redirect them back to the textbook topic
- Never roleplay
- Never answer everything at once
- Avoid long paragraphs
- Keep the interaction natural and conversational
- At the end of understanding, briefly summarize the concept learned

Your teaching style should feel like a patient tutor having a back-and-forth conversation with a student.
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

