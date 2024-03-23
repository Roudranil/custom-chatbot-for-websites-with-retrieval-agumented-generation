import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import Response
from unidecode import unidecode
from bs4 import BeautifulSoup

import utils

from typing import Any
import os
from urllib.parse import urljoin
import string
import logging
import json

CRAWLER_NAME = "chesspider"
SECTIONS = list(string.ascii_uppercase)
START_URLS = [
    f"https://en.wikibooks.org/w/index.php?title=Category:Recipes_with_metric_units&from={_}"
    for _ in SECTIONS
]
BASE_URL = "https://en.wikibooks.org"

RESULT = {}
RECIPE_URLS = []

root_directory = utils.find_root_directory()
DATA_DIR = os.path.join(root_directory, "data")

## setting up logging

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter("[%(name)s] %(levelname)s: %(message)s"))
file_handler = logging.FileHandler(os.path.join(root_directory, "log", "scraping.log"))
file_handler.setFormatter(logging.Formatter("[%(name)s] %(levelname)s: %(message)s"))

category_logger = logging.getLogger("category_logger")
category_logger.setLevel(logging.DEBUG)
category_logger.addHandler(file_handler)
category_logger.addHandler(stream_handler)

recipe_logger = logging.getLogger("recipe_logger")
recipe_logger.setLevel(logging.DEBUG)
recipe_logger.addHandler(file_handler)
recipe_logger.addHandler(stream_handler)

category_logger.info("Starting category logger.")
recipe_logger.info("Starting recipe logger.")


class PageSpider(scrapy.Spider):
    name = "pagespider"
    start_urls = START_URLS
    custom_settings = {"LOG_LEVEL": "ERROR"}

    def __init__(self, name: str | None = None, **kwargs: Any):
        utils.set_loggers_level(level=logging.ERROR)
        super().__init__(name, **kwargs)

    def parse(self, response: Response):
        categories = response.xpath('//div[@class="mw-category-group"]')
        for category in categories:
            category_name = category.xpath("h3/text()").get()
            recipes = category.xpath("ul/li/a")
            category_data = []
            for recipe in recipes:
                title = unidecode(recipe.xpath("@title").get())
                relative_url = recipe.xpath("@href").get()
                url = urljoin(BASE_URL, relative_url)
                recipe_data = {"title": title, "url": url}
                RECIPE_URLS.append(url)
                category_data.append(recipe_data)
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_recipe,
                    cb_kwargs={"recipe_name": title, "category_name": category_name},
                )
            RESULT[category_name] = category_data
            category_logger.info(f"Category {category_name} saved.")
            break

    def parse_recipe(self, response: Response, recipe_name: str, category_name: str):
        content = {}
        content["url"] = response.url
        desc = response.xpath("/html/body/div[3]/div[3]/div[5]/div[1]/p[2]").get()
        desc = BeautifulSoup(desc, "lxml").get_text() if desc else " "
        content["desc"] = unidecode(desc)
        h2_headings = response.xpath("//h2/span[@class='mw-headline']")
        h2_headings = [_.xpath("text()").get() for _ in h2_headings]
        for i, h2 in enumerate(h2_headings):
            selector_text = f"//h2[span[@class='mw-headline' and text()='{h2}']]/following-sibling::node()[not(self::h2)][preceding-sibling::h2[span[@class='mw-headline' and text()='{h2}']]]"

            content_text = response.xpath(selector_text)
            text_list = []
            for c in content_text:
                text = self._clean_text(BeautifulSoup(c.get(), "lxml").get_text())
                if text:
                    text_list.append(text)
            content[h2] = text_list

        n = len(content[h2_headings[-1]])
        content[h2_headings[-1]] = "\n".join(content[h2_headings[-1]])
        for i, h2 in enumerate(h2_headings[-2::-1]):
            new_n = len(content[h2])
            content[h2] = "\n".join(content[h2][:-n])
            n = new_n

        self._write_recipe(category_name, content, recipe_name)
        recipe_logger.info(f"Recipe written for {recipe_name}")

    def _write_recipe(self, category_name, content, recipe_name):
        json_file = os.path.join(DATA_DIR, f"{category_name}.json")
        if os.path.exists(json_file):
            with open(json_file, "r") as f:
                data = json.load(f)
        else:
            data = {}
        data[recipe_name] = content
        with open(json_file, "w") as f:
            json.dump(data, f, indent=4)

    def _clean_text(self, text):
        text = unidecode(text)
        text = text.strip("\n").strip(" ")
        text = text.replace("[edit | edit source]", "")
        return text


process = CrawlerProcess()
process.crawl(PageSpider)
process.start()


with open(os.path.join(DATA_DIR, "recipe-names.json"), "w") as f:
    json.dump(RESULT, f, indent=4)
