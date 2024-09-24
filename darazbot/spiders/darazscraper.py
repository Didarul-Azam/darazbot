import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapy.http import TextResponse
from darazbot.items import DarazItem
import time

class DarazscraperSpider(scrapy.Spider):
    name = "darazscraper"
    allowed_domains = ["www.daraz.com.bd"]
    start_urls = ["https://www.daraz.com.bd/"]
    search_terms = ['smart watch']
    def start_requests(self):
        for search_term in self.search_terms:
            yield SeleniumRequest(url='https://www.daraz.com.bd/', 
                              callback=self.search_parse,
                              wait_time=5,
                              wait_until = EC.presence_of_element_located((By.CSS_SELECTOR,'div[id="J_Categories"]')),
                              meta={'search_term': search_term}
                              )

    def search_parse(self, response):
        search_term = response.meta['search_term']
        driver = response.meta['driver']
        search_box = driver.find_element_by_css_selector('input[type="search"][id="q"]')
        search_box.send_keys(search_term)
        search_box.send_keys(Keys.RETURN)
        self.logger.info("Waiting for the search results to load...")
        wait = WebDriverWait(driver, 10)
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa-locator="general-products"]'))
        )
        # response.meta['driver'] = driver
        self.logger.info(f"Search results for {search_term} loaded, processing...")
        body = driver.page_source
        response_obj = TextResponse(url=driver.current_url, body=body, encoding='utf-8')
        # driver.quit()
        yield from self.parse_page(response_obj, search_term)
        # print(response.css('p.hp-mod-card-title::text').get())
        # self.crawler.engine.close_spider(self)
    def parse_page(self,response,search_term):
        self.logger.info(f"Processing search results for {search_term}")
        products = response.css('div.Bm3ON')
        print("********")
        print(f'total  products in page:{len(products)}')
        
        for product in products[:2]:
            url = "https:" + product.css('div.buTCk a::attr(href)').get()
            sold_amount = product.xpath('.//span[@class="_1cEkb"]/span[1]/text()').get()
            yield SeleniumRequest(url=url,
                    callback=self.ensure_fully_loaded_and_parse,
                    wait_time=10,        
                    meta={'search_term': search_term, "total_sold": sold_amount,}
                )


    def ensure_fully_loaded_and_parse(self, response):
        driver = response.meta['driver']
        search_term = response.meta['search_term']
        total_sold = response.meta['total_sold']
        # Scroll down the page to load all content
        driver.execute_script("window.scrollBy(0, 1500);")

        # Wait for the div.score element inside div.summary within div.mod-rating to be visible
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'div.mod-rating div.summary div.score')
            )
        )
        # self.scroll_down(driver)
        
        # Pass the updated page source to the callback
        body = driver.page_source
        response_obj = TextResponse(url=driver.current_url, body=body, encoding='utf-8')
        name = response_obj.css('div.pdp-product-title h1.pdp-mod-product-badge-title::text').get()
        url = response_obj.url
        print('****************')
        print("*******************")
        print(name, url)
        print('****************')
        print("*******************")
        
        # driver.close()
        # Call item_parse with the updated response
        yield from self.item_parse(response_obj,search_term,total_sold)
    
    # def scroll_down(self, driver):
    #     # Scroll down to the bottom of the page or a sufficient amount
    #     driver.execute_script("window.scrollBy(0, 1500);")
        
    #     # time.sleep(1)
    #     # driver.execute_script("document.body.click();")
    #     # Wait for the div.score element inside div.summary within div.mod-rating to be visible
    #     WebDriverWait(driver, 10).until(
    #         EC.visibility_of_element_located(
    #             (By.CSS_SELECTOR, 'div.mod-rating div.summary div.score')
    #         )
    #     )
        # time.sleep(2)
        #print(response.css('div.Bm3ON div.buTCk a::attr(href)').get())
    def item_parse(self,response,search_term,total_sold):
        
        product_item = DarazItem()
        product_item['total_sold'] = total_sold
        product_item['searched_term'] = search_term
        product_item['category'] = response.xpath('//ul[@class="breadcrumb"]/li[position() = last()-1]/span/a/@title').get()
        product_item['name'] = response.css('div.pdp-product-title h1.pdp-mod-product-badge-title::text').get()
        product_item['url'] = response.url
        product_item['price'] = response.xpath('//div[@class="pdp-product-price"]/span/text()').get()
        product_item['rating'] = response.css('div.mod-rating div.score span.score-average::text').get()
        product_item['rating_count'] = response.css('div.mod-rating div.count::text').get()
        yield product_item
