import re
import datetime
import base64
import os
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Mail, Attachment, FileContent, FileName, FileType, Disposition)
from dotenv import load_dotenv


chrome_service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())

chrome_options = Options()
options = [
    "--headless",
    "--disable-gpu",
    "--window-size=1920,1200",
    "--ignore-certificate-errors",
    "--disable-extensions",
    "--no-sandbox",
    "--disable-dev-shm-usage"
]
for option in options:
    chrome_options.add_argument(option)

driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

url = "https://www.thelayoff.com/nike"

wait = WebDriverWait(driver, 10)

driver.get(url)

doc = BeautifulSoup(driver.page_source, 'html.parser')

posts = doc.find_all(class_='topic-wrap')

data_all = []
for post in posts:
    data={}
    data['title'] = post.find(class_='post-title').text.strip()
    try:    
        data['body'] = re.sub(r'\n', '', post.find(class_='post-body').text.strip())
    except:
        pass
    data['date'] = post.find(class_='post-timeago')['data-datetime']
    data['link'] = 'https://www.thelayoff.com' + post.find(class_='thread-link')['href']
    data_all.append(data)

df = pd.DataFrame(data_all)

df['scrape_date'] = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")

try:
    existing_df = pd.read_csv("recent_posts.csv")
except:
    existing_df = pd.DataFrame([])

combined = pd.concat([df, existing_df], ignore_index=True)

combined.drop_duplicates(subset=['link','date'], inplace=True)

combined.to_csv('updated_posts.csv')

#mail csv file
#load_dotenv()
#API_KEY = os.getenv('SG_KEY')
#ADDRESS = os.getenv('ADDRESS')

message = Mail(
    from_email=os.environ.get(EMAIL),
    to_emails=os.environ.get(EMAIL),
    subject='layoff update',
    html_content='someone is saying something new')

with open('updated_posts.csv', 'rb') as f:
    data = f.read()
    f.close()
encoded_file = base64.b64encode(data).decode()

attachedFile = Attachment(
    FileContent(encoded_file),
    FileName('updated_posts.csv'),
    FileType('text/csv'),
    Disposition('attachment')
)
message.attachment = attachedFile

try:
    sg = SendGridAPIClient(os.environ.get(API_KEY))
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(e)
