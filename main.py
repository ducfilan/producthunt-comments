import requests
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time


# Set up Google Sheets API
def setup_google_sheet(sheet_name, worksheet: int = 0, is_add_header: bool = True, header=None):
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    creds = ServiceAccountCredentials.from_json_keyfile_name('lazy-vaccine-ad7c0afecddc.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).get_worksheet(worksheet)

    if is_add_header:
        if header is None:
            header = ['Product Name', 'Product Link', 'Comment Content', 'Number of Stars']
        sheet.append_row(header)

    return sheet


# Crawl Product Hunt for top products in a specific category
def crawl_producthunt_by_category(category_url):
    response = requests.get(category_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    most_loved_products = soup.find_all('div', class_=["my-2", "items-start"])
    best_products = soup.find_all('div', class_=['flex-col', 'mb-10', 'flex'])
    product_data = []
    seen_products = set()

    driver = webdriver.Chrome()  # Or another driver like Firefox
    for product in most_loved_products + best_products:
        try:
            product_name = product.findNext("strong").text.strip() if product.findNext(
                "strong") is not None else product.findNext(class_=['text-18', 'text-blue']).text.strip()
            product_link = product.findNext('a', class_='items-start')['href'] if product.findNext(
                'a', class_='items-start') is not None else product.findNext(
                'a', class_=['text-16', 'text-dark-gray'])['href']
            if product_name in seen_products:
                continue

            seen_products.add(product_name)

            if not product_link.startswith("https://www.producthunt.com"):
                product_link = f"https://www.producthunt.com{product_link.replace('/shoutouts', '')}"

            comments = crawl_product_reviews(driver, f'{product_link}/reviews')

            for (comment, stars_count) in comments:
                product_data.append([product_name, product_link, comment, stars_count])
        except Exception as e:
            print(f"Failed to scrape product: {product.prettify()}, error: {e}")
            continue
    driver.quit()

    return product_data


def crawl_product_reviews(driver: WebDriver, product_url: str) -> list[(str, int)]:
    driver.get(product_url)
    while True:
        try:
            # Wait until a button with text starting with "Show" and ending with "More" is clickable and click it
            show_more_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Show') and contains(text(), 'ore')]"))
            )

            show_more_button.click()
            time.sleep(10)  # Add delay to allow more content to load
        except Exception as e:
            print("No more 'Show [number] More' button found or failed to click it:", e)
            break

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    comments = soup.find_all(id=lambda x: x and x.startswith('review-'))

    comment_star_tuples = []

    for comment in comments:
        comment_content = comment.findNext(class_="text-18").text.strip()
        if not comment_content:
            continue

        star_labels = comment.find_all('label', attrs={'data-test': lambda x: x and x.startswith('star-')})
        stars_count = 0
        for label in star_labels:
            star_svg = label.find('svg')
            if star_svg and "styles_blueStar__ZkUiN" in star_svg.get('class', []):
                stars_count += 1

        comment_star_tuples.append((comment_content, stars_count))

    return comment_star_tuples


def crawl_product_launches_discussions(driver, product_url: str) -> list[(str, int)]:
    if not product_url.endswith("/launches"):
        product_url += "/launches"

    response = requests.get(product_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    launches = soup.find_all('div', class_='styles_item__Dk_nz')
    launch_data = []
    seen_launches = set()

    for launch in launches:
        try:
            launch_name = launch.findNext('strong').text.strip()
            if launch_name in seen_launches:
                continue

            seen_launches.add(launch_name)

            launch_link = launch.findNext('a', class_="text-14")['href']
            if not launch_link.startswith("https://www.producthunt.com"):
                launch_link = f"https://www.producthunt.com{launch_link}"

            discussions = crawl_product_single_launch_discussions(driver, launch_link)
            for discussion in discussions:
                launch_data.append((launch_name, launch_link, discussion))
        except:
            print(f"Failed to scrape launch discussions for launch: {launch_name}, link: {launch_link}")
            continue

    return launch_data


def crawl_product_single_launch_discussions(driver: WebDriver, launch_url: str) -> list[(str, int)]:
    driver.get(launch_url)
    try:
        launch_discussion_link = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Launch discussions')]"))
        )
        launch_discussion_link.click()
        time.sleep(3)  # Add delay to allow more content to load
    except Exception as e:
        print("No more 'Launch discussions' button:", e)

    while True:
        try:
            more_comments_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'more comments')]"))
            )

            more_comments_button.click()
            time.sleep(10)  # Add delay to allow more content to load
        except Exception as e:
            print("No more 'Show [number] More' button found or failed to click it:", e)
            break

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    comments = soup.find_all(lambda tag: tag.has_attr('data-test') and tag['data-test'].startswith('thread-'))

    comment_contents = []

    for comment in comments:
        try:
            comment_content = comment.findNext(class_="text-16").text.strip()
            if not comment_content:
                continue

            comment_contents.append(comment_content)
        except Exception as e:
            print(f"Failed to extract comment content: {e}")
            continue

    return comment_contents


# Save the data to Google Sheets
def save_to_google_sheet(sheet, data):
    for row in data:
        write_data_with_backoff(sheet, row)


def write_data_with_backoff(sheet, row):
    retries = 0
    while True:
        try:
            sheet.append_row(row)
            return  # Success
        except Exception as e:
            print(f"Failed to write data to Google Sheets: {e}")
            retries += 1
            wait_time = max(65, 2 ** retries)  # Exponential backoff, max 1 minute.
            print(f"Quota exceeded, retrying in {wait_time} seconds ({retries}th attempt)")
            time.sleep(wait_time)


# Main function to execute the script
if __name__ == '__main__':
    sheet_name = 'ProductHunt Comments'
    category_url = 'https://www.producthunt.com/categories/time-tracking'

    sheet = setup_google_sheet(sheet_name)
    product_data = crawl_producthunt_by_category(category_url)
    save_to_google_sheet(sheet, product_data)

    print("Data has been saved to Google Sheets successfully.")
