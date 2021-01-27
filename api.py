import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from exporter import Exporter

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def home(user: str):
    exporter = Exporter(user)
    if not await exporter.valid_user():
        return {"error": "invalid user"}

    return {"hello": user}


if __name__ == "__main__":
    uvicorn.run(app)