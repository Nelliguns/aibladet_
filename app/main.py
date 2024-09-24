from fastapi import FastAPI
from routers.articles import router as articles_router
from database import SessionLocal, engine
import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(articles_router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI app!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)