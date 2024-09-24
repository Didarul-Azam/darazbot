# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from scrapy.exporters import CsvItemExporter  
import re

class DarazbotPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        field_names = adapter.field_names()
        for field in field_names:
            value = adapter.get(field)
            if value:
                stripped_value = value.strip()
                cleaned_value = re.sub(r'\s+', ' ', stripped_value)
                adapter[field] = cleaned_value
        if not adapter['total_sold']:
            raise DropItem(f"{item} Not sold")

        return item

class CsvExportPipeline:
    def open_spider(self,spider) -> None:
        self.cat_to_exporter = {}
    def close_spider(self,spider):
        for exporter,csv_file in self.cat_to_exporter.values():
            exporter.finish_exporting()
            csv_file.close()
    def _exporter_for_item(self,item):
        adapter = ItemAdapter(item)
        searched_term = adapter['searched_term']
        if searched_term not in self.cat_to_exporter:
            csv_file = open(f"'{searched_term}'_search_results_.csv",'wb')
            exporter = CsvItemExporter(csv_file)
            exporter.fields_to_export = ['name','category','price','rating','rating_count','total_sold','brand','url']
            exporter.start_exporting()
            self.cat_to_exporter[searched_term]= (exporter,csv_file)
        return self.cat_to_exporter[searched_term][0]  
    def process_item(self,item,spider):
        exporter = self._exporter_for_item(item)
        exporter.export_item(item)
        return item           
