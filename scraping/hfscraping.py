import re
import datetime
import sqlite3
from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError
import logging

# Set up logging
logging.basicConfig(filename='scraping_errors.log', level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(message)s')

BASE_URL = "https://huggingface.co/blog"

def find_posts(url):
    XPATH_SELECTOR_1 = "/html/body/div/main/div/div[1]/div[3]/div"
    XPATH_SELECTOR_2 = "/html/body/div/main/div/div[1]/div[5]"

    href_list = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        
        # First process: Get href from the first div
        element = page.wait_for_selector(f"xpath={XPATH_SELECTOR_1}")
        
        if element:
            a_tag = element.query_selector('a')
            if a_tag:
                href = a_tag.get_attribute('href')
                if href:
                    href_list.append(href)
        else:
            print("First element not found")

        # Second process: Get all hrefs from the second div
        parent_element = page.wait_for_selector(f"xpath={XPATH_SELECTOR_2}")
        
        if parent_element:
            div_elements = parent_element.query_selector_all('div')
            
            for div in div_elements:
                a_tag = div.query_selector('a')
                if a_tag:
                    href = a_tag.get_attribute('href')
                    if href:
                        href_list.append(href)
        else:
            print("Parent element not found")
        
        browser.close()

    return href_list

def scrape_blog_post(url):
    """
    Scrapes a blog post from the given URL and returns a dictionary with the following schema:
    {
        "Title": str,              # The main title of the blog post
        "Content": str,            # The full content of the blog post
        "Publication_Date": str    # The publication date of the blog post
    }
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        
        result = {}

        # Extract the main h1 title
        h1_element = page.query_selector('h1')
        if h1_element:
            result["Title"] = h1_element.inner_text().strip()
        else:
            result["Title"] = "Title not found"

        # Wait for the blog-content div to load
        content_div = page.wait_for_selector('div.blog-content')
        
        if content_div:
            # Extract all text nodes within the div, regardless of nesting
            result["Content"] = content_div.evaluate('''
                (element) => {
                    const extractText = (node) => {
                        let text = '';
                        if (node.nodeType === Node.TEXT_NODE) {
                            text = node.textContent.trim();
                            if (text) text += '\\n';
                        } else if (node.nodeType === Node.ELEMENT_NODE) {
                            for (const childNode of node.childNodes) {
                                text += extractText(childNode);
                            }
                            // Add extra newline for block-level elements
                            if (window.getComputedStyle(node).display === 'block') {
                                text += '\\n';
                            }
                        }
                        return text;
                    };
                    return extractText(element).trim();
                }
            ''')
            date_match = re.search(r'Published\s+(\w+ \d+, \d{4})', result["Content"])
            publication_date = date_match.group(1) if date_match else "Publication date not found"
            result["Publication_Date"] = publication_date
        else:
            result["Content"] = "Blog content not found"
            result["Publication_Date"] = "Publication date not found"
        
        browser.close()
        return result

def remove_blog_from_url(url):
    return url.replace('/blog', '') if '/blog' in url else url

def clean_blog_content(content):
    # Remove navigation elements
    content = re.sub(r'Back to Articles', '', content)

    # Remove publication date
    content = re.sub(r'Published\s+\w+ \d+, \d{4}', '', content)

    # Remove GitHub update link
    content = re.sub(r'Update on GitHub', '', content)

    # Remove upvote information
    content = re.sub(r'Upvote\s*\d+', '', content)

    # Remove author information
    content = re.sub(r'\+\s*\d+\s*\w+\s*\w+\s*\w+', '', content)

    # Remove extra whitespace and newlines
    content = re.sub(r'\s+', ' ', content)
    content = re.sub(r'\n\s*\n', '\n\n', content)

    # Trim leading and trailing whitespace
    content = content.strip()

    return content

def create_database():
    conn = sqlite3.connect('blog_posts.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS posts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT,
                  date TEXT,
                  content TEXT,
                  url TEXT,
                  scraping_date TEXT)''')
    conn.commit()
    return conn

def insert_post(conn, post):
    c = conn.cursor()
    
    # Check if the post already exists
    c.execute("SELECT * FROM posts WHERE title = ?", (post['Title'],))
    existing_post = c.fetchone()
    
    # Only insert if the post doesn't exist and has content
    if not existing_post and post['Title'] != "Title not found" and post['Content'] != "Blog content not found":
        c.execute('''INSERT INTO posts (title, date, content, url, scraping_date)
                     VALUES (?, ?, ?, ?, ?)''',
                  (post['Title'], post['Publication_Date'], post['Content'], post['URL'], post['scraping_date']))
        conn.commit()
        return True
    return False

# Example usage
if __name__ == "__main__":
    conn = create_database()
    post_urls = find_posts(BASE_URL)
    print(f"Found {len(post_urls)} href attributes:")
    
    for href in post_urls:
        print(href)
        if '/blog' not in href:
            print(f"Skipping non-blog URL: {href}")
            continue
        
        try:
            post = scrape_blog_post(BASE_URL + remove_blog_from_url(href))
            post["scraping_date"] = datetime.date.today().isoformat()
            post["Content"] = clean_blog_content(post["Content"])
            post["URL"] = BASE_URL + remove_blog_from_url(href)
            if insert_post(conn, post):
                print(f"Inserted post: {post['Title']}")
            else:
                print(f"Skipped post: {post['Title']}")
        except PlaywrightTimeoutError:
            error_url = BASE_URL + remove_blog_from_url(href)
            print(f"Timeout error occurred for URL: {error_url}")
            logging.error(f"Timeout error occurred for URL: {error_url}")
            continue
        except Exception as e:
            error_url = BASE_URL + remove_blog_from_url(href)
            print(f"An error occurred for URL {error_url}: {str(e)}")
            logging.error(f"Error for URL {error_url}: {str(e)}")
            continue

    conn.close()
    print("All new posts have been stored in the database.")