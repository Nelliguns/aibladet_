from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import crud, schemas
# from .. import crud, schemas
from database import get_db, SessionLocal, engine

router = APIRouter()

# @router.get("/articles")
# def get_articles():
#     return {"message": "Articles"}

@router.get("/articles/", response_model=list[schemas.Article])
def read_articles(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    articles = crud.get_articles(db, skip=skip, limit=limit)
    return articles

@router.get("/articles/{article_id}", response_model=schemas.Article)
def read_article(article_id: int, db: Session = Depends(get_db)):
    print(f"Received request for article_id: {article_id}, type: {type(article_id)}")
    db_article = crud.get_article_by_id(db, article_id=article_id)
    if db_article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return db_article