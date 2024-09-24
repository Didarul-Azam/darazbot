# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
import re

def serialize_price(price):
    cleaned_price = re.sub(r'[^\d.]', '', price)
    return cleaned_price

class DarazItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field() 
    url = scrapy.Field() 
    price = scrapy.Field(serializer = serialize_price )
    rating = scrapy.Field()
    rating_count = scrapy.Field()
    searched_term = scrapy.Field() 
    brand = scrapy.Field()   
    total_sold = scrapy.Field()
    category = scrapy.Field()
    
