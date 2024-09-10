from playwright.sync_api import sync_playwright

def find_posts():
    BASE_URL = "https://huggingface.co/blog"
    XPATH_SELECTOR_1 = "/html/body/div/main/div/div[1]/div[3]/div"
    XPATH_SELECTOR_2 = "/html/body/div/main/div/div[1]/div[5]"

    href_list = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)
        
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

# Example usage
if __name__ == "__main__":
    posts = find_posts()
    print(f"Found {len(posts)} href attributes:")
    for href in posts:
        print(href)