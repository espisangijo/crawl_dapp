import os
import sys
sys.path.append(os.path.dirname(os.path.abspath('')))

import requests
import logging
import json
import time
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup as bs
from tqdm import tqdm
import selenium
from lxml import html
from collections import defaultdict

from utils.constants import *

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


vr_data = open('./data/vrdb/vr.json', 'r')
vr_games = json.load(vr_data)
vr_data.close()


s=Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=s)
driver.maximize_window()
vr_complete_data = defaultdict(dict)
failed = []

for k, v in vr_games.items():
    try:
        driver.get(v['link'])
        w = WebDriverWait(driver,5);
        close_modal = "//i[contains(@class, 'sky-modal__title-close-icon')]"
        w.until(EC.presence_of_element_located((By.XPATH, close_modal))).click()
        time.sleep(1)
        description_classname = "store-item-detail-page-description__content"
        desc = w.until(EC.presence_of_element_located((By.CLASS_NAME, description_classname)))
        vr_complete_data[v['title']]['title'] = v['title']
        vr_complete_data[v['title']]['desc'] = desc.text

        app_details_classname = "app-details__rows"

        app_detail_key_classname = "app-details-row__left"
        app_detail_value_classname = "app-details-row__right"

        app_details = w.until(EC.presence_of_element_located((By.CLASS_NAME, app_details_classname)))

        app_detail_key = [i.text for i in app_details.find_elements(By.CLASS_NAME, app_detail_key_classname)]
        app_detail_value = [i.text for i in app_details.find_elements(By.CLASS_NAME, app_detail_value_classname)]

        vr_complete_data[v['title']]['additional_data'] = dict(zip(app_detail_key, app_detail_value))
    except Exception as e:
        failed.append(f"{k} {e}")
driver.close()

with open('./data/vrdb/vr_complete.json', 'w') as f:
    json.dump(vr_complete_data, f)
    

with open('./data/vrdb/failed.txt', 'w') as f:
    failed =map(lambda x:x+'\n', failed)
    f.writelines(failed)
    
