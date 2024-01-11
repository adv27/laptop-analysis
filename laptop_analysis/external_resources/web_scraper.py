import json

import requests
from bs4 import BeautifulSoup


class WebScraperResource:
    BASE_URL = "https://webscraper.io"

    def get_laptops(self) -> list:
        url = f"{self.BASE_URL}/test-sites/e-commerce/more/computers/laptops"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        div_soup = soup.find(attrs={"class": "row ecomerce-items ecomerce-items-more"})
        items = json.loads(div_soup["data-items"])
        for item in items:
            item["price"] = float(item["price"])
            item["review_count"] = self.get_reviews(item["title"])
            item["storage"] = self.get_storage(item["description"])
            item["storage_in_gb"] = self.calculate_storage(item["storage"])
        return items

    @staticmethod
    def get_reviews(title: str) -> int:
        """"""
        '''
        Originally: Math.round(parseInt(e.title, 36)) % 15
        '''
        return int(title.split()[0].upper(), base=36) % 15

    @staticmethod
    def get_storage(description: str) -> str:
        specs = description.split(",")
        storages = [d.strip() for d in specs if any(word in d for word in ["GB", "TB"])]

        if len(storages) >= 2:
            return storages[1]

        '''
        Handling odd case "AMD A4-9120. 4GB. 128GB SSD"
        '''
        return storages[0].split(".")[-1].strip()

    @staticmethod
    def calculate_storage(storage: str) -> int:
        total = 0
        storages = storage.split("+")
        for stg in storages:
            stg = stg.split()[0]
            if stg.endswith("GB"):
                total += int(stg.rstrip("GB"))
            elif stg.endswith("TB"):
                total += int(stg.rstrip("TB")) * 1024
        return total


web_scraper_resource = WebScraperResource()
