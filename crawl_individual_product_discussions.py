from selenium import webdriver

from main import setup_google_sheet, save_to_google_sheet, crawl_product_launches_discussions

if __name__ == '__main__':
    sheet_name = 'ProductHunt Comments'
    sheet = setup_google_sheet(sheet_name, 1, False, header=['Launch', 'Launch Link', 'Comment Content'])

    products = [
        ('timeOS', 'https://www.producthunt.com/products/timeos'),
        ('Gryzzly Time and budget Tracking', 'https://www.producthunt.com/products/gryzzly-time-and-budget-tracking'),
        ('ActivityWatch', 'https://www.producthunt.com/products/activitywatch'),
        ('TickTick', 'https://www.producthunt.com/products/ticktick'),
        ('Magicflow', 'https://www.producthunt.com/products/magicflow'),
        ('Taskade', 'https://www.producthunt.com/products/taskade'),
        ('Wakatime', 'https://www.producthunt.com/products/wakatime'),
        ('MindMeister', 'https://www.producthunt.com/products/mindmeister'),
        ('Toggl', 'https://www.producthunt.com/products/toggl'),
        ('RescueTime', 'https://www.producthunt.com/products/rescuetime'),
        ('Toggl', 'https://www.producthunt.com/products/toggl'),
        ('RescueTime', 'https://www.producthunt.com/products/rescuetime'),
        ('Increaser', 'https://www.producthunt.com/products/increaser'),
    ]

    driver = webdriver.Chrome()  # Or another driver like Firefox
    for product_name, product_link in products:
        try:
            product_data = crawl_product_launches_discussions(driver, product_link)
            save_to_google_sheet(sheet, product_data)
        except Exception as e:
            print(f"Error crawling product '{product_name}' ({product_link}): {e}")

    driver.quit()

    print("Data has been saved to Google Sheets successfully.")
