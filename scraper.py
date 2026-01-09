import requests
from bs4 import BeautifulSoup

def scrape_prices(product):
    # ⚠️ مثال نظيف – لا scraping عدواني
    # يمكنك لاحقًا إضافة Amazon / Noon / AliExpress APIs

    dummy_data = [
        {
            "store": "Store A",
            "base_price": 100,
            "shipping": 10,
            "tax": 5,
            "rating": 4.6,
            "reviews": 1200,
            "store_age": 5,
            "return_policy": True
        },
        {
            "store": "Store B",
            "base_price": 85,
            "shipping": 25,
            "tax": 8,
            "rating": 3.8,
            "reviews": 300,
            "store_age": 1,
            "return_policy": False
        }
    ]

    return dummy_data
