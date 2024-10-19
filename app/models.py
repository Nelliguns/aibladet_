from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Article(Base):
    __tablename__ = "summarized_posts"

    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True, index=True)
    date = Column(String)
    content = Column(String)
    url = Column(String)
    scraping_date = Column(String)
    summary = Column(String)
    summary_date = Column(String)
    img_id = Column(Integer)

