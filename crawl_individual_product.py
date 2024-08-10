from selenium import webdriver

from main import setup_google_sheet, crawl_product_reviews, save_to_google_sheet

if __name__ == '__main__':
    sheet_name = 'ProductHunt Comments'
    sheet = setup_google_sheet(sheet_name, 0, False)

    products = [
        ('timeOS', 'https://www.producthunt.com/products/timeos/reviews'),
        ('Gryzzly Time and budget Tracking',
         'https://www.producthunt.com/products/gryzzly-time-and-budget-tracking/reviews'),
        ('ActivityWatch', 'https://www.producthunt.com/products/activitywatch/reviews'),
        ('TickTick', 'https://www.producthunt.com/products/ticktick/reviews'),
        ('Magicflow', 'https://www.producthunt.com/products/magicflow/reviews'),
        ('Taskade', 'https://www.producthunt.com/products/taskade/reviews'),
        ('Wakatime', 'https://www.producthunt.com/products/wakatime/reviews'),
        ('MindMeister', 'https://www.producthunt.com/products/mindmeister/reviews'),
        ('Toggl', 'https://www.producthunt.com/products/toggl/reviews'),
        ('RescueTime', 'https://www.producthunt.com/products/rescuetime/reviews'),
        ('Toggl', 'https://www.producthunt.com/products/toggl/reviews'),
        ('RescueTime', 'https://www.producthunt.com/products/rescuetime/reviews'),
    ]

    driver = webdriver.Chrome()  # Or another driver like Firefox
    for product_name, product_link in products:
        product_data = []
        comments = crawl_product_reviews(driver, product_link)
        for (comment, stars_count) in comments:
            product_data.append([product_name, product_link, comment, stars_count])

        save_to_google_sheet(sheet, product_data)
    driver.quit()

    print("Data has been saved to Google Sheets successfully.")
