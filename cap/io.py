import os
import json
import glob
import time

from seqlbtoolkit.text import substring_mapping

from .constants import *

try:
    import pyautogui
    import shutil
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.common.exceptions import NoSuchElementException
except KeyError:
    pass


def scroll_down(driver_var, value):
    driver_var.execute_script("window.scrollBy(0," + str(value) + ")")


# Scroll down the page
def scroll_down_page(driver, n_max_try=100):

    old_page = driver.page_source
    for _ in range(n_max_try):
        for i in range(2):
            scroll_down(driver, 500)
            time.sleep(0.1)
        new_page = driver.page_source
        if new_page != old_page:
            old_page = new_page
        else:
            break
    return True


def every_downloads_chrome(driver):
    if not driver.current_url.startswith("chrome://downloads"):
        driver.get("chrome://downloads/")
    return driver.execute_script("""
        var items = document.querySelector('downloads-manager')
            .shadowRoot.getElementById('downloadsList').items;
        if (items.every(e => e.state === "COMPLETE"))
            return items.map(e => e.fileUrl || e.file_url);
        """)


def download_article_windows(doi, download_path, driver_path=None):

    article_url = 'https://doi.org/' + doi
    driver = webdriver.Chrome(executable_path=driver_path)

    driver.get(article_url)
    scroll_down_page(driver)

    if doi.startswith('10.1039'):
        try:
            driver.find_element(By.LINK_TEXT, 'Article HTML').click()
            scroll_down_page(driver)
        except NoSuchElementException:
            pass

    pyautogui.hotkey('ctrl', 's')

    time.sleep(1)

    file_name = substring_mapping(doi, CHAR_TO_HTML_LBS) + '.html'
    save_path = os.path.join(download_path, file_name)
    save_path = os.path.abspath(os.path.normpath(save_path))

    if os.path.isfile(save_path):
        os.remove(save_path)
    if os.path.isdir(save_path.replace('.html', '_files')):
        shutil.rmtree(save_path.replace('.html', '_files'))
    pyautogui.write(save_path)
    pyautogui.hotkey('enter')
    time.sleep(0.1)

    pyautogui.hotkey('ctrl', 't')
    time.sleep(0.1)
    driver.switch_to.window(driver.window_handles[1])
    _ = WebDriverWait(driver, 120, 1).until(every_downloads_chrome)
    time.sleep(0.1)

    driver.quit()


def get_file_paths(input_dir: str):
    if os.path.isfile(input_dir):
        with open(input_dir, 'r', encoding='utf-8') as f:
            file_list = json.load(f)
    elif os.path.isdir(input_dir):
        folder = input_dir
        file_list = list()
        for suffix in ('xml', 'html'):
            file_list += glob.glob(os.path.join(folder, f"*.{suffix}"))
    else:
        raise FileNotFoundError("Input file does not exist!")
    return file_list
