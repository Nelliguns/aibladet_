from sqlalchemy.orm import Session
import models, schemas


def get_article_by_id(db: Session, article_id: int):
    return db.query(models.Article).filter(models.Article.id == article_id).first()


def get_articles(db: Session, skip: int = 0, limit: int = 100):
    # return db.query(models.Article).offset(skip).limit(limit).all()
    return db.query(models.Article).order_by(models.Article.id.desc()).offset(skip).limit(limit).all()

def create_article(db: Session, article: schemas.ArticleBase):
    db_article = models.Article(**article.model_dump())
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

