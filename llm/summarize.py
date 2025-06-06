from dotenv import load_dotenv
import os
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage
import sqlite3
import datetime
import random

def load_env_variables():
    """
    Load environment variables from .env file.
    """
    load_dotenv()

    # Get the LLM_API_KEY from the environment
    llm_api_key = os.getenv('LLM_API_KEY')

    # Return a dictionary of environment variables
    return {
        'LLM_API_KEY': llm_api_key,
    }

def summarize_article(article_text: str) -> str:
    """
    Summarize a news article using Claude Sonnet.
    
    Args:
        article_text (str): The full text of the news article.
    
    Returns:
        str: A 3-4 sentence summary of the article.
    """
    env_vars = load_env_variables()
    chat = ChatAnthropic(
        anthropic_api_key=env_vars['LLM_API_KEY'],
        model="claude-3-sonnet-20240229"
    )

    summarize_template = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful AI assistant that summarizes news articles concisely and accurately. It's very important that your summary of the article is in Swedish as the summaries will be added to a swedish news paper website. You will provide a 3-4 sentence summary. The output should not include a discription of the summary like: here's the 3-4 sentence summary. Only output the summary back and nothing more."),
        ("human", "Please summarize the following news article:\n\n{article_text}")
    ])

    messages = summarize_template.format_messages(article_text=article_text)
    response = chat.invoke(messages)
    return response.content

def create_summary_table(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS summarized_posts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT,
                  date TEXT,
                  content TEXT,
                  url TEXT,
                  scraping_date TEXT,
                  summary TEXT,
                  summary_date TEXT,
                  img_id INTEGER)''')  # Added img_id column
    conn.commit()

def summarize_unsummarized_posts(db_path):
    """
    Summarize all unsummarized posts in the database and store the summaries.

    This function connects to the SQLite database, retrieves all posts that haven't
    been summarized yet, generates summaries using the summarize_article function,
    and stores the results in the summarized_posts table.

    Args:
        db_path (str): The file path to the SQLite database.

    Table Structure:
        summarized_posts
        - id (INTEGER): Primary key, auto-incrementing
        - title (TEXT): The title of the article
        - date (TEXT): The original publication date of the article
        - content (TEXT): The full content of the article
        - url (TEXT): The URL of the article
        - scraping_date (TEXT): The date when the article was scraped
        - summary (TEXT): The generated summary of the article
        - summary_date (TEXT): The date when the summary was generated
        - img_id (INTEGER): A random number between 0 and 7

    The function compares the posts table with the summarized_posts table
    to identify unsummarized articles, processes them, and inserts the results
    into the summarized_posts table.
    """
    conn = sqlite3.connect(db_path)
    create_summary_table(conn)
    c = conn.cursor()
    
    # Get all unsummarized posts
    c.execute('''SELECT p.title, p.date, p.content, p.url, p.scraping_date 
                 FROM posts p
                 LEFT JOIN summarized_posts sp ON p.title = sp.title
                 WHERE sp.title IS NULL''')
    
    unsummarized_posts = c.fetchall()
    
    for post in unsummarized_posts:
        title, date, content, url, scraping_date = post
        
        # Summarize the content
        summary = summarize_article(content)
        summary_date = datetime.date.today().isoformat()
        
        img_id = random.randint(0, 7)  # Generate a random img_id between 0 and 7
        
        # Insert into summarized_posts table
        c.execute('''INSERT INTO summarized_posts 
                     (title, date, content, url, scraping_date, summary, summary_date, img_id)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (title, date, content, url, scraping_date, summary, summary_date, img_id))  # Added img_id
        print(f"Summarized and stored: {title}")
    
    conn.commit()
    conn.close()

def display_sample_summaries(db_path, sample_size=5):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute('''SELECT title, summary, summary_date 
                 FROM summarized_posts 
                 ORDER BY summary_date DESC 
                 LIMIT ?''', (sample_size,))
    
    samples = c.fetchall()
    
    print(f"\nDisplaying {len(samples)} recent summaries:\n")
    for title, summary, summary_date in samples:
        print(f"Title: {title}")
        print(f"Summary Date: {summary_date}")
        print("Summary:")
        print(summary)
        print("-" * 50)
    
    conn.close()

def check_summarized_posts(db_path):
    """
    Check the summarized_posts table to ensure img_id numbers are present.

    Args:
        db_path (str): The file path to the SQLite database.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute('''SELECT title, img_id 
                 FROM summarized_posts 
                 WHERE img_id IS NOT NULL''')
    
    posts_with_img_id = c.fetchall()
    
    print(f"\nPosts with img_id:\n")
    for title, img_id in posts_with_img_id:
        print(f"Title: {title}, img_id: {img_id}")
    
    conn.close()

# Example usage
if __name__ == "__main__":
    db_path = 'blog_posts.db'  # Adjust this path as needed
    summarize_unsummarized_posts(db_path)
    print("All new posts have been summarized and stored in the database.")
    
    # Display sample summaries
    display_sample_summaries(db_path)
    
    # Check summarized posts for img_id
    check_summarized_posts(db_path)
