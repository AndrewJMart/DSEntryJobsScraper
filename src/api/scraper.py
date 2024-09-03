from scraper_functions import *
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from src import database as db
import sqlalchemy
import time
import sys
import os
import re
import json
import requests
import html
import random
from bs4 import BeautifulSoup
from Llama import Llama3


def post_new_jobs():
    # Initial Selenium Setup
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--ignore-certificate-errors")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    print("Sucessfully Bult Chrome Instance")

    url = 'https://www.linkedin.com/jobs/search?keywords=Data%20Scientist&location=United%20States&geoId=103644278&f_E=2%2C1%2C3&f_TPR=r604800&position=1&pageNum=0'

    print("Scraping URLS")

    urls = []

    # if initial job page stalls wait 4/8 seconds and request URL again
    while len(urls) == 0:
        time.sleep(random.uniform(4, 8))
        urls = list(set(Job_URLs(driver, url, 0)))

    Job_List, Description_List = Job_Scraper(driver, urls)

    driver.quit()

    # Instantiate local instance of Llama-3-8B for simple text extraction from job descriptions
    Llama = Llama3("./meta-llama/Meta-Llama-3-8B-Instruct")
    degree, experience = Llama.description_info(Description_List)

    # Reiterate through jobs to assign minimum degree & work experience requirements
    for Job, Degree_Level, Experience_Level in zip(Job_List, degree, experience):
        Job['Job_Degree'] = Degree_Level
        Job['Job_Experience'] = Experience_Level

    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.insert(db.Jobs), Job_List
        )

    return f"Finished Scraping {len(Job_List)} Jobs"


if __name__ == "__main__":
    post_new_jobs()