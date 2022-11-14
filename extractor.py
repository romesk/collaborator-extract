from datetime import datetime
import os
import pickle
import re

import pandas as pd
from RPA.Browser.Selenium import Selenium
from SeleniumLibrary.errors import ElementNotFound
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from utils import LoginException

COLLABORATOR_URL = "https://collaborator.pro/ua/"
CWD = os.getcwd()


class Extractor:
    """
    Main Extraction logic
    """

    def __init__(self, user_data: dict):

        self.url = user_data['url']

        print("\n> Виконується вхід..\nЯкщо це перший вхід потрібно зачекати трошки більше часу.")

        self.browser = Selenium()
        self.browser.open_available_browser(headless=True)
        self.browser.maximize_browser_window()

        if 'cookies' in user_data:
            self._login_with_cookies(user_data['cookies'])
        else:
            self._login_with_creds(user_data['login'], user_data['password'])

        result_columns = ["WEBSITE", "THEMES", "TRAFFIC", "DR", "ARTICLE_PRICE", "PRESS_RELEASE_PRICE"]
        self.result_df = pd.DataFrame(columns=result_columns)

    def start(self):
        try:
            self._extract_results()
        except Exception as ex:
            raise ex

        now = datetime.now().strftime("%d-%m-%Y_%H-%M")
        filename = f"[Collaborator-Extract] results_{now}.xlsx"
        self.result_df.to_excel(filename, index=False)

        print(f">>> Успішно збережено файл з результатами {filename}.")

    def _login_with_creds(self, login: str, password: str) -> None:
        """
        Login to account using credentials and save cookies sessions

        :param login: Collaborator login
        :type login: str
        :param password: Collaborator password
        :type password: str
        """

        self.browser.go_to(COLLABORATOR_URL + "login/")

        accept_btn = 'xpath://button[contains(@class, "accept-all")]'
        if self.browser.is_element_visible(accept_btn):
            self.browser.click_button(accept_btn)

        self.browser.input_text('xpath://input[@id="loginform-identity"]', login)
        self.browser.input_text('xpath://input[@id="loginform-password"]', password)

        self.browser.click_button('xpath://button[@type="submit"]')

        try:
            self.browser.wait_until_element_is_visible('xpath://li[@id="header-balance-item"]')
        except Exception as ex:
            print(f"\nUnable to login. > Error: {ex}")
            raise LoginException()

        self._create_cookies_dump(login)

    def _create_cookies_dump(self, login: str) -> None:
        """
        Save cookies for logins without credentials.
        :param login: account email for naming
        :type login: str
        """

        sessions_folder_path = os.path.join(CWD, 'sessions')
        if not os.path.exists(sessions_folder_path):
            os.mkdir(os.path.join(CWD, 'sessions'))

        session_path = os.path.join(sessions_folder_path, f"{login.split('@')[0]}.pkl")
        with open(session_path, "wb") as file:
            pickle.dump(self.browser.driver.get_cookies(), file)

        print(f"\n> Cecія для {login} успішно збережена для майбутніх входів!")

    def _login_with_cookies(self, cookies_dump: str):
        """
        Using saved cookies to sign in to account.
        :param cookies_dump: name of cookies
        :type cookies_dump: str
        """

        self.browser.go_to(COLLABORATOR_URL)

        with open(cookies_dump, 'rb') as f:
            cookies = pickle.load(f)

        if isinstance(cookies, dict):
            for name, value in cookies.items():
                self.browser.add_cookie(name, value, domain='collaborator.pro')
        else:
            for cookie in cookies:
                self.browser.driver.add_cookie(cookie)

        print("\n> Успішно увійдено використовуючи збережену сесію!")

        self.browser.go_to(COLLABORATOR_URL)

    def _extract_results(self):
        """
        Process of extracting all the results
        """

        regex = re.compile(r'&per-page=\d+')
        if regex.search(self.url):
            url = re.sub(r'&per-page=\d+', '&per-page=100', self.url)
        else:
            url = self.url + '&per-page=100'

        url = re.sub(r'&page=\d+', 'page=1', url)  # set 1 as current page

        self.browser.go_to(url)

        self.browser.wait_until_element_is_visible('xpath://div[@class="creator-catalog block-blur-holder"]')

        amount = self.browser.find_element('xpath://div[@class="filter-panel"]/ul/li/b').text
        amount = re.sub(r'[^0-9]', '', amount)
        max_pages = '?'

        if amount.isdecimal():
            max_pages = int(amount) // 100
            if max_pages % 100:
                max_pages += 1
        else:
            print("Не вдалось з'ясувати кількість результатів.")

        print(f"Знайдено {amount} позицій для зчитування. Починається витягування даних...")
        is_last_page = False
        page_num = 1

        while not is_last_page:
            print(f">> Витягування данних зі сторінки {page_num}/{max_pages}..")
            try:
                is_last_page = self.browser.find_element('xpath://li[@class="page-item_next disabled"]')
            except ElementNotFound:
                is_last_page = False

            self.__process_separate_page()

            if not is_last_page:
                next_page = self.browser.find_element('xpath://li[@class="page-item_next"]/a').get_attribute('href')
                self.browser.go_to(next_page)

            page_num += 1

    @staticmethod
    def __parse_separate_marketplace(marketplace: WebElement) -> dict:
        """
        Extract all the data from single marketplace
        :param marketplace: marketplace to process
        :type marketplace: WebElement
        :return: dict column_name: value
        :rtype: dict
        """

        try:
            website_url = marketplace.find_element(
                By.XPATH, './/div[@class="link-holder link-holder_icon-right"]'
                          '//a[@class="faw fas fa-external-link tooltips"]'
            ).get_attribute('href')
        except NoSuchElementException:
            return {}  # if URL is hidden, skip

        themes_list = marketplace.find_elements(By.XPATH, './/td[@class="c-t-theme"]//span[@class="tag"]')
        themes = "\n".join([theme.text for theme in themes_list])

        traffic = marketplace.find_element(By.XPATH, './/ul/li[@class="value-with-graph"]').text

        tds = marketplace.find_elements(By.TAG_NAME, 'td')
        domain_rating = tds[5].text

        article_div = './/div[contains(@class, "format-item format-item--article format-item_sm")]'
        article_price = marketplace.find_element(
            By.XPATH, article_div + '//div[@class="creator-price__publication-value"]').text

        try:
            article_writing = marketplace.find_element(
                By.XPATH, article_div + '//div[@class="creator-price__spelling"]').text
        except NoSuchElementException:
            article_writing = ""

        press_release_div = './/div[contains(@class, "format-item format-item--press-release format-item_sm")]'

        try:
            press_release_price = marketplace.find_element(
                By.XPATH, press_release_div + '//div[@class="creator-price__publication-value"]').text
        except NoSuchElementException:
            press_release_price = ""

        try:
            press_release_writing = marketplace.find_element(
                By.XPATH, press_release_div + '//div[@class="creator-price__spelling"]').text
        except NoSuchElementException:
            press_release_writing = ""

        return {
            "WEBSITE": website_url,
            "THEMES": themes,
            "TRAFFIC": traffic,
            "DR": domain_rating,
            "ARTICLE_PRICE": article_price + f" ({article_writing})" if article_writing else article_price,
            "PRESS_RELEASE_PRICE": press_release_price + f" ({press_release_writing})" if press_release_writing
            else press_release_price
        }

    def __process_separate_page(self):
        """
        Parse single page
        """

        marketplaces = self.browser.find_elements('xpath://tbody/tr')

        for marketplace in marketplaces:
            parsed_data = self.__parse_separate_marketplace(marketplace)

            if parsed_data:
                self.result_df = pd.concat((self.result_df, pd.DataFrame(parsed_data, index=[0])), ignore_index=True)
