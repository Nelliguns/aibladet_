from pydantic import BaseModel


class ArticleBase(BaseModel):
    id: int
    title: str

    class Config:
        orm_mode = True

class Article(ArticleBase):
    summary: str
    summary_date: str
    img_id: int

class ArticleFull(Article):
    date: str
    content: str
    url: str
    scraping_date: str
