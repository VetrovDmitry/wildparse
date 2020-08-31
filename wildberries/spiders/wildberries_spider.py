import scrapy
import time
import re
from urllib.parse import urljoin
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from wildberries.items import WildberriesItem


class WildberriesSpyder(scrapy.spiders.Spider):
    name = 'wildberries'
    start_urls = [
        'https://www.wildberries.ru/catalog/igrushki/interaktivnye',
    ]
    custom_settings = {
        'FEED_FORMAT': "json"
    }
    # rules = (Rule(LinkExtractor(allow=(), restrict_css=('a.pagination-next::attr(href)', )), callback="parse_page", follow=True)

    def price_to_integer(self, price):
        clear_price = re.findall(r"\d", price)
        a_string = ''.join(clear_price)
        an_integer = int(a_string)
        return an_integer

    def from_table_to_dict(self, column_1, column_2):
        new_form = dict()
        for spec_name in column_1:
            i = column_1.index(spec_name)
            value = column_2[i]
            new_form[spec_name] = value
        return new_form

    def parse(self, response):
        for post_link in response.xpath(
                "//div[@class='dtList-inner']/span/span/span/a/@href").extract():
            url = urljoin(response.url, post_link)
            yield response.follow(url, callback=self.parse_page)

        next_page = response.css('a.pagination-next::attr(href)').extract()
        next_page_url = urljoin(response.url, next_page)

        yield scrapy.Request(next_page_url, callback=self.parse)

    def parse_page(self, response):
        item = WildberriesItem()
        timestamp = time.time()
        item['timestamp'] = timestamp
        RPC = 1
        item['RPC'] = RPC
        url = response.url
        item['url'] = url
        title = response.css('span.name::text').extract()
        item['title'] = title
        marketing_tags = response.css(
            'li.tags-group-item.j-tag a::text').extract()
        item['marketing_tags'] = marketing_tags
        brand = response.css('span.brand::text').extract()
        item['brand'] = brand
        section = response.css('ul.bread-crumbs span::text').extract()
        item['section'] = section

        price_data = dict()

        final_cost = response.css('span.final-cost::text').extract()[0]
        final_cost = self.price_to_integer(final_cost)
        price_data['current'] = final_cost

        if response.css('del.c-text-base::text').extract():
            original_price = response.css('del.c-text-base::text').extract()[0]
            original_price = self.price_to_integer(original_price)
            sale_size = (original_price - final_cost) / original_price
            sale_tag = "Скидка {}%".format(int(sale_size))

        else:
            original_price = final_cost
            sale_tag = ''

        price_data['current'] = final_cost
        price_data['original'] = original_price
        price_data['sale_tag'] = sale_tag

        item['price_data'] = price_data
        stock = None
        item['stock'] = stock
        assets = 0
        decription = response.css(
            'div.description.j-collapsable-description.i-collapsable-v1 p::text'
        ).extract()
        article = response.css('span.j-article::text').extract()
        color = response.css('span.color::text').extract()
        left_col = response.css(
            'div.params.j-collapsable-card-add-info.i-collapsable-v1 div.pp b::text').extract()
        right_col = response.css(
            'div.params.j-collapsable-card-add-info.i-collapsable-v1 div.pp span::text').extract()
        metadata = self.from_table_to_dict(left_col, right_col)
        metadata['color'] = color
        metadata['article'] = article
        metadata['decription'] = decription
        item['metadata'] = metadata
        yield item
