from main import setup_google_sheet, crawl_product_comments, save_to_google_sheet

if __name__ == '__main__':
    sheet_name = 'ProductHunt Comments'
    sheet = setup_google_sheet(sheet_name, 1, False)

    product_name = 'Rize'
    product_link = 'https://www.producthunt.com/products/rizeio/reviews'

    product_data = []
    comments = crawl_product_comments(product_link)
    for (comment, stars_count) in comments:
        product_data.append([product_name, product_link, comment, stars_count])

    save_to_google_sheet(sheet, product_data)

    print("Data has been saved to Google Sheets successfully.")
