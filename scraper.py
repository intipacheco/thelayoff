import re
import datetime
import base64
import os
import time
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
from webdriver_manager.chrome import ChromeDriverManager
#from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import chromedriver_autoinstaller #new
from selenium.webdriver.support.ui import WebDriverWait
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Mail, Attachment, FileContent, FileName, FileType, Disposition)
from dotenv import load_dotenv

chromedriver_autoinstaller.install()
#chrome_service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())

chrome_options = webdriver.ChromeOptions()    
#chrome_options = Options()
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

#driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

driver = webdriver.Chrome(options = chrome_options)

def scroll_down():
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height



def send_email():
    message = Mail(
        from_email=os.environ.get('EMAIL'),
        to_emails=os.environ.get('EMAIL'),
        subject='layoff update',
        html_content='someone is saying something new') 

    with open('recent_posts.csv', 'rb') as f:
        data1 = f.read()
        f.close()
    encoded_file = base64.b64encode(data1).decode()  

    attachedFile = Attachment(
        FileContent(encoded_file),
        FileName('recent_posts.csv'),
        FileType('text/csv'),
        Disposition('attachment')
    )
    message.attachment = attachedFile   

    try:
        sg = SendGridAPIClient(os.environ.get('API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)


url = "https://www.thelayoff.com/nike"

wait = WebDriverWait(driver, 10)

driver.get(url)

scroll_down()

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
    print(data)
    print('-----')

df = pd.DataFrame(data_all)

df['scrape_date'] = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")

print(df.head(10))

try:
    existing_df = pd.read_csv("recent_posts.csv")
except:
    existing_df = pd.DataFrame()

#combined = pd.concat([df, existing_df], ignore_index=True)

combined = pd.concat([df, existing_df], ignore_index=True).drop_duplicates(keep='first', subset=['link'])

send_it = len(combined) > len(existing_df)

combined.to_csv('recent_posts.csv', index=False)

if send_it:
    send_email()
    print('incoming email')
else:
    print('nothing new')




#combined.drop_duplicates(subset=['link','date'], inplace=True)

#combined.to_csv('updated_posts.csv')

#mail csv file
#load_dotenv()
#API_KEY = os.getenv('SG_KEY')
#ADDRESS = os.getenv('ADDRESS')


