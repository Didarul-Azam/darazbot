import scrapy
from scrapy_playwright.page import PageMethod
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
from darazbot.items import DarazItem
from scrapy.http import HtmlResponse
import logging
import asyncio
import time 

class DarazscraperSpiderPw(scrapy.Spider):
    name = "darazscraperpw"
    allowed_domains = ["daraz.com.bd"]
    custom_settings = {
        'LOG_FILE': 'scrapy_log.log',
        'LOG_LEVEL': 'INFO',
    } 
    def __init__(self,search_term=None, *args, **kwargs):
        super(DarazscraperSpiderPw, self).__init__(*args, **kwargs)
        self.search_term = search_term  # Set the search term dynamically   
    
    def start_requests(self):
        if self.search_term:
            search_url = f'https://www.daraz.com.bd/catalog/?q={self.search_term}'
            yield scrapy.Request(
                url=search_url,
                callback=self.search_parse,
                errback=self.errback,
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,
                    playwright_page_methods=[
                        PageMethod("wait_for_selector", 'div[data-qa-locator="general-products"]')
                    ],
                    search_term=self.search_term,
                    pageNO =1
                )
            )
        else:
            self.logger.error("No search term provided. Use -a search_term='<term>' to provide it.")

            
    async def search_parse(self, response):
        page = response.meta['playwright_page']
        pageNO = response.meta['pageNO']
        search_term = response.meta['search_term']
        products = response.css('div.Bm3ON')
        #loop through the products
        for product in products:
            product_url = "https:" + product.css('div.buTCk a::attr(href)').get()
            sold_amount = product.xpath('.//span[@class="_1cEkb"]/span[1]/text()').get()
            yield scrapy.Request(url = product_url,
                                 callback=self.item_parse,
                                 errback = self.errback,
                                 meta=dict(
                                 playwright= True,
                                 playwright_include_page= True,
                                 playwright_page_methods =[
                                    PageMethod('wait_for_timeout', 3000)   
                    ],
                                 search_term= search_term,
                                 total_sold =sold_amount
                                 )
                )
        # code for next page for upto 5 pages
        next_page_selector = 'li[title= "Next Page"]'       
        await page.evaluate("window.scrollBy(0, 1500);")
        await page.wait_for_selector(next_page_selector,timeout=60000)
        is_disabled = await page.get_attribute(next_page_selector, 'aria-disabled')      
        logging.info(f"is_disabled: {is_disabled}")
        if (is_disabled == "false" or is_disabled is None) and pageNO<5:
            logging.info(f'moving to page no. {pageNO+1}')           
            await page.click(next_page_selector)
            await asyncio.sleep(1)
            await page.wait_for_selector('div[data-qa-locator="general-products"]', timeout=120000)
            time.sleep(1)
            next_url = page.url
            logging.info(f'page no. {pageNO+1} url : {next_url}')
            yield scrapy.Request(
                url=next_url,
                callback=self.search_parse,
                errback=self.errback,
                dont_filter = True,
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,
                    playwright_page_methods=[
                        PageMethod("wait_for_selector", 'div[data-qa-locator="general-products"]')
                    ],
                    search_term=search_term,
                    pageNO =pageNO+1
                )
            )
            
        else:
            logging.info(f"No more pages or page limit reached at page {pageNO}")
        await page.close()  

        
    async def item_parse(self,response):
        search_term = response.meta['search_term']
        total_sold = response.meta['total_sold']
        logging.info(f'into item_parse with {response.url}')
        second_search = response.meta.get('second_search', False)
        page = response.meta['playwright_page']
        url = page.url
        await page.mouse.move(50, 50)
        await asyncio.sleep(1)
        try:
            await page.wait_for_selector('ul.breadcrumb',timeout=60000)
            await page.evaluate('window.scrollBy(0, 1500);')
            await asyncio.sleep(2)
            await page.wait_for_selector('div.mod-rating div.summary div.score',timeout=60000)
        except:
            if not second_search:
                try:
                    if "?pdpBucketId" in response.url:
                        logging.warning(f'bad url sent by server for url: {response.url}')
                        original_url = response.url.split("?")[0]
                        logging.info(f"Now trying again with {original_url}")
                        logging.info(f'response request url : {response.request.url}')
                        yield scrapy.Request(url = original_url,
                                    callback=self.item_parse,
                                    errback = self.errback,
                                    dont_filter = True,
                                    meta=dict(
                                    playwright= True,
                                    playwright_include_page= True,
                                    playwright_page_methods =[
                                        PageMethod('wait_for_timeout', 3000)   
                        ],
                                    search_term= search_term,
                                    total_sold =total_sold,
                                    second_search = True
                                    ))
                        await page.close()
                        return
                    else:    
                        await page.reload()
                        await asyncio.sleep(1)
                        await page.wait_for_selector('ul.breadcrumb',timeout=60000)
                        await page.evaluate('window.scrollBy(0, 1500);')
                        await asyncio.sleep(2)
                        await page.wait_for_selector('div.mod-rating div.summary div.score',timeout=60000)                
                except:
                    logging.error(f"could not load {response.url}")
                    await page.close()
                    return
            else:
                logging.error(f'same bad url sent by server by {response.url}')
                await page.close()
                return

        content = await page.content()
        url = page.url
        await page.close()
        page_response = HtmlResponse(url=url, body=content, encoding='utf-8')
        product_item = DarazItem()
        product_item['total_sold'] = total_sold
        product_item['searched_term'] = search_term
        product_item['brand'] = page_response.xpath('//span[@class="pdp-product-brand__name"]/following-sibling::a[1]/text()').get()
        product_item['category'] = page_response.xpath('//ul[@class="breadcrumb"]/li[position() = last()-1]/span/a/@title').get()
        product_item['name'] = page_response.css('div.pdp-product-title h1.pdp-mod-product-badge-title::text').get()
        product_item['url'] = page_response.url
        product_item['price'] = page_response.xpath('//div[@class="pdp-product-price"]/span/text()').get()
        product_item['rating'] = page_response.css('div.mod-rating div.score span.score-average::text').get()
        product_item['rating_count'] = page_response.css('div.mod-rating div.count::text').get()
        yield product_item
    async def errback(self,failure):
        # log all failures
        self.logger.error(repr(failure))

        page = failure.request.meta.get('playwright_page')
        if page:
            await page.close()

        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            self.logger.error("HttpError on %s", response.url)

        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error("DNSLookupError on %s", request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error("TimeoutError on %s", request.url)
