# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class DarazbotSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class DarazbotDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

import requests
from random import randint


class ScrapeOpsHeadersMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        #to return a spider istance to get access to settings
        return cls(crawler.settings)
    
    def __init__(self,settings):
        self.scrapeops_api_key = settings.get('SCRAPEOPS_API',None)
        self.scrapeops_headers_endpoint = settings.get('SCRAPEOPS_HEADERS_ENDPOINT')
        self.scrapeops_headers_active = settings.get('SCRAPEOPS_HEADERS_ENABLED',False)
        self.header_nums = settings.get('SCRAPEOPS_HEADERS_NUM',10)
        self.headers_list = []
        self._scrapeops_fake_headers_enabled()
        self._get_headers_list()

    def _get_headers_list(self):
        if self.scrapeops_headers_active:
            payload = {'api_key':self.scrapeops_api_key}
            if self.header_nums is not None:
                payload['num_results'] = self.header_nums
            try:
                response = requests.get(self.scrapeops_headers_endpoint, params=payload)
                response.raise_for_status()
                json_response = response.json()
                self.headers_list = json_response.get('result', [])
            except (requests.RequestException, ValueError) as e:
                # Handle the exception (e.g., log the error)
                self.headers_list = [] 
    def _get_random_header(self):
        if not self.headers_list:
            return {}
        random_index = randint(0,len(self.headers_list)-1) 
        return self.headers_list[random_index]
    
    def _scrapeops_fake_headers_enabled(self):
        self.scrapeops_headers_active = bool(self.scrapeops_api_key) and self.scrapeops_headers_active 

    def process_request(self,request,spider):
        if not self.scrapeops_headers_active:
            return
        random_header = self._get_random_header()
        if random_header:
            try:
                request.headers['user-agent'] = random_header['user-agent']
                request.headers['accept'] = random_header['accept']
                request.headers["sec-ch-ua-platform"] = random_header["sec-ch-ua-platform"]
                request.headers["sec-ch-ua"] = random_header["sec-ch-ua"]
            except:
                request.headers = request.headers    
        self.record_headers(request)
    def record_headers(self,request):
        with open('request_headers.txt', 'a') as f:
            f.write(f"Request Headers: {dict(request.headers)}\n") 