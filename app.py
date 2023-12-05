#!/usr/bin/env python

import os
from typing import List, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


class Message(BaseModel):
    role: str
    content: str


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


async def generate(messages: List[Message], model_type: str):
    try:
        response = await aclient.chat.completions.create(model=model_type,
        messages=[message.model_dump() for message in messages],
        stream=True)

        async for chunk in response:
            print(chunk)
            # print(chunk.choices[0].delta)
            content = chunk.choices[0].delta.content
            if content:
                yield content

    except Exception as e:
        yield f"{type(e).__name__}: {str(e)}"


class Gpt4Request(BaseModel):
    messages: List[Message]
    model_type: str


@app.post("/gpt4")
async def gpt4(request: Gpt4Request):
    assistant_response = generate(request.messages, request.model_type)
    return StreamingResponse(assistant_response, media_type='text/event-stream')


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host='0.0.0.0', port=8001, reload=True)
