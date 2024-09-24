# Darazbot

Darazbot is a web scraping tool designed to extract product information from the Daraz.com e-commerce platform. It utilizes Scrapy and Playwright to handle both static and JavaScript-rendered content, enabling to gather valuable data for analysis or personal use.

## Features

- **Persistent Crawling:** Maintains state between runs to avoid data duplication.
- **Dynamic Search Options:** Allows users to customize search queries.
- **Dynamic Fake Headers:** Uses rotating fake headers for better anonymity during scraping.
- **Data Serialization:** Saves scraped data into CSV format for easy access and analysis.
- **Error Handling:** Implements robust error handling to ensure reliable data collection.

## Technologies Used

- **Python:** The primary programming language used for developing the bot.
- **Scrapy:** A powerful web scraping framework for extracting data from websites.
- **Playwright:** A web automation tool used for scraping JavaScript-rendered pages.
