import time
from typing import Optional

from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, NoSuchElementException


try:
    from ..seqlbtoolkit.text import substring_mapping
except ImportError:
    from seqlbtoolkit.text import substring_mapping


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


def load_article_html(doi) -> str:
    """
    Load online articles and convert them to HTML strings

    Parameters
    ----------
    doi: article DOI

    Returns
    -------
    HTML string
    """

    article_url = 'https://doi.org/' + doi
    driver = load_webdriver()

    driver.get(article_url)

    if doi.startswith('10.1039'):
        try:
            driver.find_element(By.LINK_TEXT, 'Article HTML').click()
            scroll_down_page(driver)
        except NoSuchElementException:
            pass

    html_content = driver.page_source
    return html_content


def load_webdriver(headless: Optional[bool] = True) -> WebDriver:
    """
    A more robust way to load chrome webdriver (compatible with headless mode)

    Returns
    -------
    WebDriver
    """
    try:
        options = Options()
        if headless:
            options.headless = True
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                 "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    except WebDriverException:

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    return driver
