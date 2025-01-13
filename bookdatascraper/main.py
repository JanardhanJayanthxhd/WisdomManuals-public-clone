from bs4 import BeautifulSoup
import requests
from time import sleep
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


CHROME_WEB_DRIVER_PATH = '' # Your chromedriver.exe'p path

class Book:
    book_dict = {}

    def get_book_dict(self):
        return self.book_dict


class BookIsbn(Book):
    CHR0ME_WEBDRIVER_PATH = CHROME_WEB_DRIVER_PATH
    service = Service(executable_path=CHR0ME_WEBDRIVER_PATH)
    driver = webdriver.Chrome(service=service)

    def book_scraper(self) -> list:
        """Scraping book titles using BS4"""
        response = requests.get("https://upjourney.com/best-self-help-books")
        books_website = response.text

        soup = BeautifulSoup(books_website, parser='html.parser', features='lxml')
        books_a_tags = soup.select(selector=".wp-block-heading a")
        # # Separating names from "1. "
        books = [str(a.text.split(". ", 1)[1:][0]) for a in books_a_tags]
        # # separating book title and authors name
        books = [book.split(" – ", 1)[0] for book in books]
        return books

    def isbn(self, book_name) -> str:
        """returns the ISBN-10 number for requested book name"""
        self.driver.get('https://isbnsearch.org/')

        sleep(2)

        search_bar = self.driver.find_element(By.ID, 'searchQuery')
        search_bar.clear()
        search_bar.send_keys(book_name)
        search_bar.send_keys(Keys.ENTER)

        # For captcha.
        sleep(10)

        # getting first search result because it seems to be right
        first_list_item = self.driver.find_element(By.XPATH, '//ul/li[1]')
        # print(first_list_item.text)
        # getting the isbn 10 which is present in the third <p> inside the search result
        try:
            isbn_10 = first_list_item.find_element(By.XPATH, ".//p[contains(text(), 'ISBN-10')]")
            isbn_10_number = isbn_10.text.split(': ')[1]
        except NoSuchElementException:
            print(first_list_item)
            isbn_10_number = '-'

        sleep(2)
        return isbn_10_number

    def write_book_data(self):
        book_dict = Book.get_book_dict(self)
        books = self.book_scraper()
        # updating book dictionary {book title : 'isbn'} is case if any error occurs when automation process.
        for item in books:
            book_dict[item] = ''

        print(book_dict)
        with open('../static/csv/bookdata.csv', 'a') as bookfile:
            bookfile.write('Book title, ISBN-10')
            for key, val in book_dict.items():
                # checking if the value of each book is empty.
                if val == '':
                    isbn_number = self.isbn(key)
                    book_dict[key] = isbn_number
                    # To save the book name in a single column by checking if it contains comma
                    if ',' in key:
                        bookfile.write(f'"{key}", {isbn_number}\n')
                    else:
                        bookfile.write(f'{key}, {isbn_number}\n')
        print(book_dict)

        # self.driver.close()


book = BookIsbn()
book.write_book_data()
