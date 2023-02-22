import logging
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import scrapy
from scrapy.signals import spider_opened

from ..utils import date_string_transform, form_url


class AmurInfoSpider(scrapy.Spider):
    name = "amur_info"
    custom_settings = {
        "ITEM_PIPELINES": {"amur_info.pipelines.AmurInfoCSVPipeline": 300},
        "LOG_LEVEL": "INFO",
    }

    def start_requests(self):
        current_time = date_string_transform(datetime.today())
        time_period = date_string_transform(datetime.today() - timedelta(days=10))
        yield scrapy.Request(
            f"https://amur.info/category/%D0%B2%D1%81%D0%B5-%D0%BD%D0%BE%D0%B2%D0%BE%D1%81%D1%82%D0%B8/?article-category=1627&articles-date={quote_plus(time_period)}+-+{quote_plus(current_time)}",
            callback=self.parse,
            cb_kwargs={
                "search_word": self.search_word,
                "page": 1,
            },
        )

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AmurInfoSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=spider_opened)
        return spider

    def spider_opened(self, spider):
        self.search_word = "светофор"
        logging.info(
            f"Найдем количество упоминаний слова {self.search_word} в заголовках сайта amur.info"
        )
        self.all_items = []

    def parse(self, response, **kwargs):
        # Собираем заголовки и ссылки, если в них есть наше слово для поиска
        data = dict()
        header_selector = "//div[@class='long-news-grid']/div/a[@class='h2']"
        for i in response.xpath(header_selector):
            header = i.xpath("./text()").get()
            if kwargs["search_word"] in header.lower():
                link = i.xpath("./@href").get()
                data["Заголовок"] = header
                data["Ссылка"] = link
                self.all_items.append(data)
                yield data
        # Пагинация организована через нахождение последней страницы и прибавлением к каждой странице единицы, пока мы не достигнем последней страницы
        max_page = int(
            response.xpath(
                "//div[@class='pagination__pages']/a[@class='pagination__link']/text()"
            ).getall()[-1]
        )
        if kwargs["page"] < max_page:
            kwargs["page"] += 1
            yield scrapy.Request(
                form_url(kwargs["page"], response.url),
                callback=self.parse,
                cb_kwargs=kwargs,
                dont_filter=True,
            )
        else:
            # Останавливаемся если мы нашли ссылки в любом диапазоне, или не нашли ни одной ссылки даже за 20 дневный диапазон
            if len(self.all_items) != 0 or kwargs.get("20_days"):
                logging.info(
                    f"Пройдено страниц: {kwargs['page']} , найдено ссылок: {len(self.all_items)}"
                )
            else:
                # Расширяем диапазон до 20 дней и переходим сразу на следующую страницу
                kwargs["page"] += 1
                current_time = date_string_transform(datetime.today())
                time_period = date_string_transform(
                    datetime.today() - timedelta(days=20)
                )
                url = f"https://amur.info/category/%D0%B2%D1%81%D0%B5-%D0%BD%D0%BE%D0%B2%D0%BE%D1%81%D1%82%D0%B8/?article-category=1627&articles-date={quote_plus(time_period)}+-+{quote_plus(current_time)}"
                kwargs["20_days"] = True
                yield scrapy.Request(
                    form_url(kwargs["page"], url),
                    callback=self.parse,
                    dont_filter=True,
                    cb_kwargs=kwargs,
                )
