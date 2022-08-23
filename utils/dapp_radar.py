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

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from selenium.webdriver.common.proxy import Proxy, ProxyType


def crawl_dapp_radar(pages):
    
    s = Service(GeckoDriverManager().install())

    dapp_dict = defaultdict(dict)

    chain_classname = "//div[contains(@class, 'sc-ljMRFG') and contains(@class, 'ikDqTv')]"
    dapp_classname = "//span[contains(@class, 'sc-hKumaY') and contains(@class, 'falIJP')]"
    category_classname = "//div[contains(@class, 'rankings-column__category') and contains(@class, 'sc-eSxRXt') and contains(@class, 'fxjZId')]"
    balance_classname = "//div[contains(@class, 'rankings-column__balance') and contains(@class, 'sc-eSxRXt') and contains(@class, 'fxjZId')]"
    users_classname = "//div[contains(@class, 'rankings-column__users') and contains(@class, 'sc-eSxRXt') and contains(@class, 'fxjZId')]"
    volume_classname = "//div[contains(@class, 'rankings-column__volume') and contains(@class, 'sc-eSxRXt') and contains(@class, 'fxjZId')]"
    ad_classname =  "//div[contains(@class, 'sc-eSxRXt') and contains(@class, 'fxjZId')]"
    image_classname = "//div[contains(@class, 'sc-jNHqnW') and contains (@class, 'eZJvve')]"

    driver = webdriver.Firefox(service=s, desired_capabilities=None)
    for page in pages:
        
        driver.get(f"https://dappradar.com/rankings/protocol/ethereum/{page}")

        w = WebDriverWait(driver,10);

        for i in range((page-1)*25+1,(page-1)*25+26):
            try: 
                table = w.until(EC.presence_of_element_located((By.XPATH, dapp_classname)));
                ad = table.find_elements(By.XPATH, ad_classname)
                names = table.find_elements(By.XPATH, dapp_classname)

                chains = table.find_elements(By.XPATH, chain_classname)
                category = table.find_elements(By.XPATH, category_classname)
                balance = table.find_elements(By.XPATH, balance_classname)
                users = table.find_elements(By.XPATH, users_classname)
                volume = table.find_elements(By.XPATH, volume_classname)
                image = table.find_elements(By.XPATH, image_classname)
                dapp_id_list = [a.text for a in ad]
                idx = dapp_id_list.index(str(i))
                dapp = names[idx].text
                dapp_dict[dapp]["dapp_id"] = idx
                dapp_dict[dapp]["name"] = names[idx].text
                dapp_dict[dapp]["chain"] = chains[idx].text
                dapp_dict[dapp]["category"] = category[idx].text
                dapp_dict[dapp]["balance"] = balance[idx].text
                dapp_dict[dapp]["users"] = users[idx].text
                dapp_dict[dapp]["volume"] = volume[idx].text
                dapp_dict[dapp]["imageUrl"] = image[idx].find_element(By.TAG_NAME, 'img').get_attribute('src')
                button = names[idx].find_element(By.XPATH, './../../../../..')
                link = button.get_attribute('href')
                driver.get(f"{link}")

                # social links
                brand_classname = "//div[contains(@class, 'article-page__brand-info')]"

                brand = w.until(EC.presence_of_element_located((By.XPATH, brand_classname)));
                social_parents = brand.find_elements(By.TAG_NAME, "li")
                social_links = [social_parent.find_element(By.TAG_NAME, 'a').get_attribute('href') for social_parent in social_parents]
                dapp_dict[dapp]['social'] = social_links

                # description -> get href
                desc_classname = "article-page__description"
                desc = w.until(EC.presence_of_element_located((By.CLASS_NAME, desc_classname))).text;
                dapp_dict[dapp]['description'] = desc

                # open smart contract list
                sc_open_classname = "//div[contains(@class, 'sc-bhiFeW') and contains(@class, 'iqkoMY')]"
                sc_open = w.until(EC.presence_of_element_located((By.XPATH, sc_open_classname)));
                driver.execute_script("arguments[0].click();", sc_open)

                # get modal
                modal_classname = "modal-content"
                modal = w.until(EC.presence_of_element_located((By.CLASS_NAME, modal_classname)));
                # smart contract address
                sc_address_classname = "//a[contains(@class, 'sc-dusCKN') and contains(@class, 'sc-iaUyqC') and contains(@class, 'fbiXqM') and contains(@class, 'bXOZVX')]"

                addresses = w.until(EC.presence_of_all_elements_located((By.XPATH, sc_address_classname)))
                addresses_unpacked = [address.text for address in addresses]
                sc_chain_classname = "//div[contains(@class, 'sc-ljMRFG') and contains(@class, 'ikDqTv')]"
                chains =  w.until(EC.presence_of_all_elements_located((By.XPATH, sc_chain_classname)))
                chains_unpacked = [chain.text for chain in chains]
                dapp_dict[dapp]['smart_contract'] = list(zip(addresses_unpacked, chains_unpacked))

                driver.find_element(By.CLASS_NAME, 'modal-close').click()

                open_dapp_classname = "//a[contains(@class, 'sc-ksDcAU') and contains(@class, 'jYEOmc')]"
                open_dapp = w.until(EC.presence_of_element_located((By.XPATH, open_dapp_classname)));
                driver.execute_script("arguments[0].click();", open_dapp)
                w.until(EC.number_of_windows_to_be(2))

                original_window = driver.current_window_handle
                for window_handle in driver.window_handles:
                    if window_handle != original_window:
                        driver.switch_to.window(window_handle)
                        break

                WebDriverWait(driver, 10).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')

                dapp_dict[dapp]['url'] = driver.current_url
                driver.close()

                driver.switch_to.window(original_window)

                driver.execute_script("window.history.go(-1)")
                
                logging.info(f"done: {page}, {i}")
            except Exception as e:
                logging.error(f"error:{page}:{i}: {e}")
            
        with open(f"./data/dapp_radar/{page}.json", 'w') as f:
            json.dump(dapp_dict, f)

        driver.close()

import multiprocessing as mp


   
if __name__ == '__main__': 
    logging.basicConfig(filename='./logs/dapp_radar/error.log')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s')

    total_page = [i for i in range(1,126)]
    crawl_dapp_radar(total_page)