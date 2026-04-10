from fastapi import FastAPI
from .database import engine, Base
from .auth import router as auth_router

app = FastAPI(title="Auth Lab API")

# Create tables on startup
Base.metadata.create_all(bind=engine)

app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Auth Lab API. Visit /docs for documentation."}
