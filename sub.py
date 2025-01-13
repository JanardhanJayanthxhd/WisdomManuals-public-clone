import requests
from random import choice

google_books_api_key = '' # Google books API Key


class Book:

    def update_books(self) -> list:
        """returns a list containing multiple(100) list[book name, its isbn, ... and more]"""
        data_list = []
        with open('static/csv/bookdata.csv', 'r') as data:
            for line in data:
                book_data = {}

                line_list = line.split(',')
                # slicing to remove \n from end
                book_isbn = line_list[1].replace('\n', '')
                # if book title contains comma
                if len(line_list) > 2:
                    # title_list = line_list[:-1]
                    # # Combining all title text from title_list into one and removing double quotes from either ends.
                    # book_title = ''.join(title_list)[1:-1]
                    book_isbn = line_list[-1].replace('\n', '')

                # Checking if data exists in google book api
                g_book_data = self.get_data(book_isbn)
                if g_book_data:
                    cover_url = self.get_cover(book_isbn)
                    book_data['title'] = g_book_data[0]
                    book_data['subtitle'] = g_book_data[1]
                    book_data['authors'] = g_book_data[2]
                    book_data['categories'] = g_book_data[3]
                    book_data['pages'] = g_book_data[4]
                    book_data['price'] = g_book_data[5]
                    book_data['isbn'] = book_isbn
                    book_data['img_url'] = cover_url
                    data_list.append(book_data)

        return data_list[1:]

    def get_cover(self, isbn) -> str:
        """returns the cover of a specific book"""
        base_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
        response = requests.get(base_url)
        if response.status_code == 200:
            return response.url
        return ''

    def get_data(self, isbn) -> list:
        """returns the data required for BookTable"""
        base_url = "https://www.googleapis.com/books/v1/volumes"
        params = {
            'q': f'isbn:{isbn}',
            'key': google_books_api_key,
            'printType': 'books'
        }
        response = requests.get(url=base_url, params=params)
        google_book_data = []
        if response.status_code == 200:
            data = response.json()
            if data["totalItems"] > 0:
                subtitle = ''
                categories = []
                title = data["items"][0]['volumeInfo']['title']
                google_book_data.append(title)
                # checking if there is a subtitle
                try:
                    subtitle = data["items"][0]['volumeInfo']['subtitle']
                except KeyError:
                    subtitle = '-'
                finally:
                    google_book_data.append(subtitle)
                authors = data["items"][0]['volumeInfo']['authors']
                # print(authors)
                google_book_data.append(authors)

                #
                try:
                    categories = data["items"][0]['volumeInfo']['categories']
                except KeyError:
                    categories = []
                else:
                    categories = categories[0].split(' ')
                    # removing unwanted elements from categories
                    items_to_check = ['&']
                    for item in items_to_check:
                        if item in categories:
                            categories.remove(item)
                    # Turning items into lowercase
                    categories = [i.lower() for i in categories]
                    # print(categories)
                finally:
                    google_book_data.append(categories)

                # pages
                try:
                    pages = data["items"][0]['volumeInfo']['pageCount']
                except KeyError:
                    # if there is no length of the book I cannot determine price. So eliminating that book.
                    return []
                else:
                    # checking if pages = 0.
                    if pages != 0:
                        google_book_data.append(pages)
                    else:
                        return []

                # not all api response contain price so...
                sale_info = data["items"][0]['saleInfo']
                try:
                    price = sale_info['retailPrice']['amount']
                except KeyError:
                    if pages > 400:
                        price = choice([441, 444, 440, 439, 450])
                    elif pages > 200:
                        price = choice([250, 249, 255, 253])
                    else:
                        price = choice([170, 169, 150, 160])
                google_book_data.append(price)

                return google_book_data

        return []


# single item in all books:
# {'title': 'How To Win Friends and Influence People', 'subtitle': '-', 'authors': ['Dale Carnegie'],
# 'categories': ['self-help'], 'img_url': 'https://covers.openlibrary.org/b/isbn/145162171X-L.jpg'}

# Available categories from all books
# ['concentration', 'camp', 'inmates', 'business', 'economics', 'self-help', 'body,', 'mind', 'spirit', 'psychology',
# 'humor', 'military', 'art', 'and', 'science', 'philosophy', 'biography', 'autobiography', 'creation', '(literary,',
# 'artistic,', 'etc.)']
