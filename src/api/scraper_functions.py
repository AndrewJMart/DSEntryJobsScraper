from src import database as db
import time
import os
import re
import json
import requests
import html
import random
from bs4 import BeautifulSoup
import sys
import sqlalchemy

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Add the 'src' directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def Job_URLs(Driver, URL, Page_Num):
    # TODO - Implement Page Numbering Multiple Pages
    print("Getting Original Job Page")
    Driver.get(URL)
    for i in range(2):
        Driver.execute_script("window.scrollBy(0, 200);")
        time.sleep(random.uniform(0.5, 1.0))

    # ".base-card.relative.w-full.hover\\:no-underline.focus\\:no-underline.base-card--link.base-search-card.base-search-card--link.job-search-card.job-search-card--active",
    # ".base-card.relative.w-full.hover\\:no-underline.focus\\:no-underline.base-card--link.base-search-card.base-search-card--link.job-search-card"

    selectors = [
        "a.base-card__full-link.absolute.top-0.right-0.bottom-0.left-0.p-0.z-\\[2\\]"
    ]

    Job_Links = []
    Job_Identifier_List = []

    for selector in selectors:
        div_elements = Driver.find_elements(By.CSS_SELECTOR, selector)
        for element in div_elements:
            Job_Link = element.get_attribute('href')

            if Job_Link:
                # print(f"Job Link {Job_Link}")

                Job_Identifier = Job_ID(Job_Link)
                # print(f"Job Indentifer {Job_Identifier}")

                with db.engine.begin() as connection:
                    exists = connection.execute(
                        sqlalchemy.select(db.Jobs).where(
                            db.Jobs.c.Job_ID == Job_Identifier)
                    ).fetchone() is not None

                if Job_Identifier in Job_Identifier_List or exists:
                    pass

                Job_Links.append(Job_Link)
                Job_Identifier_List.append(Job_Identifier)

            else:
                print("Missing Link")

    return Job_Links


def Job_Scraper(Driver, Job_Links):
    Job_List = []
    Description_List = []
    Job_Identifier_List = []

    for Job_Link in Job_Links:
        for i in range(10):
            Driver.execute_script("window.scrollBy(0, 200);")
            time.sleep(random.uniform(2, 2.5))
            
        print("Navigating To Job Posting")
        Driver.get(Job_Link)

        Job_Posting_HTMl = Driver.page_source

        print("Scraping Job Data")
        Experience, Employment_Type, Industry = Job_Metadata(Job_Posting_HTMl)
        Title = Job_Title(Job_Posting_HTMl)
        Description = Job_Description(Job_Posting_HTMl)
        Job_Identifier = Job_ID(Job_Link)
        Company = Job_Company(Job_Posting_HTMl)
        Image = Job_Image(Job_Posting_HTMl)
        Day_Posted = Job_Date(Job_Posting_HTMl)
        J_Location = Job_Location(Job_Posting_HTMl)

        Job_Identifier_List.append(Job_Identifier)

        Job_Info = {
            'Job_ID': Job_Identifier,
            'Experience_Level': Experience,
            'Employment_Type': Employment_Type,
            'Industry': Industry,
            'Title': Title,
            'Description': Description,
            'Company': Company,
            'Image': Image,
            'Day_Posted': Day_Posted,
            'Job_Location': J_Location,
            'Job_Link': Job_Link
        }

        Job_List.append(Job_Info)
        Description_List.append(Description)

        if all(element is not None for element in Job_Info.values()):
            print(f"""
                Job Information Debugging:
                ---------------------------
                Job ID:             {Job_Identifier}
                Title:              {Title}
                Company:            {Company}
                Experience Level:   {Experience}
                Employment Type:    {Employment_Type}
                Industry:           {Industry}
                Day Posted:         {Day_Posted}
                Description:        {Description[:10]}
                Image URL:          {Image[:10]}
                Job Link:           {Job_Link}
                Job Location:       {J_Location}
                ---------------------------
                """)

    return Job_List, Description_List


def Job_Metadata(Job_HTML):
    soup = BeautifulSoup(Job_HTML, 'html.parser')

    criteria_tags = soup.select(
        "span.description__job-criteria-text.description__job-criteria-text--criteria"
    )

    if criteria_tags:
        Job_Experience = criteria_tags[0].get_text(strip=True)
        Employment_Type = criteria_tags[1].get_text(strip=True)
        Industry = criteria_tags[3].get_text(strip=True)

        return Job_Experience, Employment_Type, Industry
    else:
        print("No matching experience level tags found.")
        return None, None, None


def Job_Title(Job_HTML):
    Soup = BeautifulSoup(Job_HTML, 'html.parser')

    h3_element = Soup.select_one("h3.sub-nav-cta__header")

    if h3_element:
        job_title = h3_element.get_text(strip=True)
        return job_title
    else:
        print("No matching <h3> tag found.")
        return None


def Job_Description(Job_HTML):
    Soup = BeautifulSoup(Job_HTML, 'html.parser')

    Div_Tag = Soup.find(
        'div', class_='show-more-less-html__markup show-more-less-html__markup--clamp-after-5 relative overflow-hidden')

    if Div_Tag:
        for Tag in Div_Tag.find_all(['strong', 'li', 'div', 'br', 'ul', 'p', 'span']):
            Tag.unwrap()

        Cleaned_Description = Div_Tag.get_text(separator=' ', strip=True)

        return Cleaned_Description
    else:
        print("Description Not Found")
        return None


def Job_Company(Job_HTML):
    Soup = BeautifulSoup(Job_HTML, 'html.parser')

    Company_Link = Soup.select_one(
        "a.topcard__org-name-link.topcard__flavor--black-link")

    if Company_Link:
        company_name = Company_Link.get_text(strip=True)
        return company_name
    else:
        print("No matching company name found.")
        return None


def Job_Image(Job_HTML):
    soup = BeautifulSoup(Job_HTML, 'html.parser')

    image_tag = soup.select_one("img.artdeco-entity-image")

    if image_tag:
        try:
            image_url = image_tag['src']
        except:
            print("Failed to retrieve image.")
            return None

        response = requests.get(image_url)

        if response.status_code == 200:
            image_data = response.content

            return image_data
        else:
            print("Failed to retrieve image.")
            return None
    else:
        print("No matching image tag found.")
        return None


def Job_Date(Job_HTML):
    soup = BeautifulSoup(Job_HTML, 'html.parser')

    posted_time_tag = soup.select_one(
        "span.posted-time-ago__text.topcard__flavor--metadata")

    if posted_time_tag:
        posted_time = posted_time_tag.get_text(strip=True).strip()
        return posted_time
    else:
        print("No matching posted time tag found.")
        return None


def Job_Location(Job_HTML):
    soup = BeautifulSoup(Job_HTML, 'html.parser')

    location_element = soup.find(
        'span', class_='topcard__flavor topcard__flavor--bullet')

    if location_element:
        location = location_element.get_text(strip=True)
        return location
    else:
        print("No matching tag found for location.")
        return None


def Job_ID(URL):
    match = re.search(r'-(\d+)\?position=', URL)
    job_id = match.group(1)
    return job_id
