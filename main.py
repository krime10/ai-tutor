import hashlib
import json
import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel
from pypdf import PdfReader
import pandas as pd

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

## Source of Truth
Use ONLY the provided textbook content. Never introduce facts outside it. Stay focused on the Electricity chapter; politely redirect off-topic questions back to the chapter.

## Teaching Style
- Be a tutor, not an answer machine — ask guiding questions before giving explanations
- Ask only ONE question at a time; keep responses short and conversational
- Avoid long paragraphs; use relatable real-life examples when helpful
- Never roleplay

## Hint System (use in this order)
1. Guiding question
2. Small hint
3. Stronger hint
4. Full explanation only if the student is still stuck

If the student makes a mistake, ask diagnostic questions before correcting. If confused, step back to the prerequisite idea.

## Concept Sequencing
Use the knowledge graph to determine concept order, prerequisites, and dependencies. Always:
- Verify prerequisite understanding before introducing a new concept
- Teach in textbook dependency order — never skip ahead
- If a student asks about a future topic, briefly connect it to the current concept and return to the current lesson
- Use the prior knowledge checklist to recover any missing prerequisite understanding
- Do not advance to the next concept automatically — confirm the student is ready first
- Introduce new concepts gradually and naturally through conversation
## Wrapping Up Each Concept
Once understanding is achieved, briefly summarize the concept and ask whether the student is ready to continue.
"""

base_dir = Path(__file__).resolve().parent
textbook_path = base_dir / "textbook.pdf"
concepts_path = base_dir / "Electricity_Knowledge_Graph_v2.xlsx"
users_file = base_dir / "users.json"

textbook_content = ""
user_histories = {}
if textbook_path.exists():
    reader = PdfReader(textbook_path)
    for page in reader.pages:
        text = page.extract_text()
        if text:
            textbook_content += text
else:
    textbook_content = "Textbook content is unavailable."

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

concepts_content = ""
edges_content = ""
prior_content = ""
guidelines_content = ""

if concepts_path.exists():
    try:
        concepts_df = pd.read_excel(concepts_path, sheet_name="Concepts")
        edges_df = pd.read_excel(concepts_path, sheet_name="Edges (Prerequisite Map)")
        prior_df = pd.read_excel(concepts_path, sheet_name="Prior Knowledge Checklist")
        guidelines_df = pd.read_excel(concepts_path, sheet_name="AI Tutor Guidelines")

        concepts_content = concepts_df.to_string(index=False)
        edges_content = edges_df.to_string(index=False)
        prior_content = prior_df.to_string(index=False)
        guidelines_content = guidelines_df.to_string(index=False)
    except Exception:
        concepts_content = "Concepts data is unavailable."
        edges_content = "Prerequisite relationships are unavailable."
        prior_content = "Prior knowledge checklist is unavailable."
        guidelines_content = "AI tutor guidelines are unavailable."
else:
    concepts_content = "Concepts data is unavailable."
    edges_content = "Prerequisite relationships are unavailable."
    prior_content = "Prior knowledge checklist is unavailable."
    guidelines_content = "AI tutor guidelines are unavailable."


def load_users():
    if not users_file.exists():
        return []
    try:
        return json.loads(users_file.read_text())
    except json.JSONDecodeError:
        return []


def save_users(users):
    users_file.write_text(json.dumps(users, indent=2))


def hash_password(password: str):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def find_user(username: str):
    for user in load_users():
        if user.get("username", "").lower() == username.lower():
            return user
    return None


def sanitize_user(user: dict):
    return {
        "username": user.get("username", ""),
        "fullName": user.get("fullName", ""),
        "academicClass": user.get("academicClass", ""),
        "age": user.get("age", None),
        "favoriteSubjects": user.get("favoriteSubjects", ""),
        "interests": user.get("interests", []),
    }


def build_profile_summary(profile: Optional[dict]):
    if not profile:
        return "Student profile information is unavailable."

    interests = profile.get("interests") or []
    if isinstance(interests, str):
        interests = [interests]
    interests_string = ", ".join(interests) if interests else "None"

    return (
        f"Student profile:\n"
        f"- Name: {profile.get('fullName', 'Unknown')}\n"
        f"- Academic class: {profile.get('academicClass', 'Unknown')}\n"
        f"- Age: {profile.get('age', 'Unknown')}\n"
        f"- Favorite subjects: {profile.get('favoriteSubjects', 'None')}\n"
        f"- Interests / hobbies: {interests_string}\n"
        f"Use these interests and hobbies to personalize examples and explanations whenever appropriate."
    )


class RegisterRequest(BaseModel):
    fullName: str
    username: str
    password: str
    academicClass: str
    age: int
    favoriteSubjects: str
    interests: List[str]


class LoginRequest(BaseModel):
    username: str
    password: str


class Message(BaseModel):
    name: str
    text: str
    profile: Optional[dict] = None


@app.post("/api/register")
async def register(data: RegisterRequest):
    if find_user(data.username):
        raise HTTPException(status_code=400, detail="Username already exists.")

    users = load_users()
    users.append({
        "fullName": data.fullName,
        "username": data.username,
        "passwordHash": hash_password(data.password),
        "academicClass": data.academicClass,
        "age": data.age,
        "favoriteSubjects": data.favoriteSubjects,
        "interests": data.interests,
    })
    save_users(users)
    return {"message": "Registration successful"}


@app.post("/api/login")
async def login(data: LoginRequest):
    user = find_user(data.username)
    if not user or user.get("passwordHash") != hash_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return {"message": "Login successful", "user": sanitize_user(user)}


@app.post("/api/chat")
async def chat(message: Message):
    try:
        profile = find_user(message.name) or message.profile
        profile_summary = build_profile_summary(profile)

        if message.name not in user_histories:
            user_histories[message.name] = []

        conversation_history = user_histories[message.name]
        conversation_history.append({"role": "user", "content": message.text})

        messages = [
            {
                "role": "system",
                "content": f"""
                STUDENT PROFILE:
                {profile_summary}

                KNOWLEDGE GRAPH CONCEPTS:
                {concepts_content}

                PREREQUISITE RELATIONSHIPS:
                {edges_content}

                PRIOR KNOWLEDGE CHECKLIST:
                {prior_content}

                AI TUTOR GUIDELINES:
                {guidelines_content}
                {SYSTEM_PROMPT}

                Use the student's favorite subjects and interests/hobbies to personalize your examples and explanations whenever appropriate.

                TEXTBOOK CONTENT:
                {textbook_content}
                """
            },
            *conversation_history[-6:],
        ]

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
        )

        first_choice = response.choices[0]
        msg = getattr(first_choice, "message", None)
        content = msg.content

        conversation_history.append({"role": "assistant", "content": content})
        return {"reply": content}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/")
async def root():
    return FileResponse("login.html")


@app.get("/login")
async def login_page():
    return FileResponse("login.html")


@app.get("/register")
async def register_page():
    return FileResponse("register.html")


@app.get("/tutor")
async def tutor_page():
    return FileResponse("tutor.html")


@app.get("/chat")
async def chat_page():
    return FileResponse("tutor.html")


app.mount("/static", StaticFiles(directory="."), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
