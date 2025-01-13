from flask import Flask, render_template, redirect, url_for, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, logout_user, login_required, LoginManager, current_user
from flask_migrate import Migrate
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from sqlalchemy.orm import relationship
from functools import wraps
import json
import razorpay
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# SMTP setup
my_email = ""  # Your senders email id
pwd = "" # That email's password

# application
app = Flask(__name__)
app.app_context().push()
app.config["SECRET_KEY"] = "" # Secret key for this application

# DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)
# migrator
migrate = Migrate(app, db)

# password hasher
bcrypt = Bcrypt(app)

# Flask login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def user_loader(user):
    return Users.query.filter_by(id=user).first()


# admin only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(404)
        return f(*args, **kwargs)
    return decorated_function


class Users(UserMixin, db.Model):
    __tablename__ = "UserTable"

    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.Integer(), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Integer(), nullable=False)

    # defining one-to-one relationship by using 'uselist=False' with cart,'
    cart = relationship("Cart", uselist=False, back_populates='user')

    # Defining one-to-one relationship between Address and Users
    addr = relationship("Address", uselist=False, back_populates='user')

    def __repr__(self):
        return f'user - {self.username}'


class Address(db.Model):
    __tablename__ = "AddressTable"

    addr_id = db.Column(db.Integer(), primary_key=True)
    # ForeignKey from UserTable(id)
    user_id = db.Column(db.Integer(), db.ForeignKey(Users.id))

    first_name = db.Column(db.String(100), nullable=False)
    addr_st = db.Column(db.String(150), nullable=False)
    addr_city = db.Column(db.String(50), nullable=False)
    addr_state = db.Column(db.String(50), nullable=False)
    addr_pincode = db.Column(db.Integer(), nullable=False)

    # 1-to-1 r/s with Users
    user = relationship("Users", back_populates='addr')

    def __repr__(self):
        return f'address - {self.addr_id}'


class Cart(db.Model):
    __tablename__ = "CartTable"

    cart_id = db.Column(db.Integer(), primary_key=True)
    # foreign key from UserTable
    user_id = db.Column(db.Integer(), db.ForeignKey(Users.id))
    status = db.Column(db.String(20), nullable=False)

    # defining one-to-one relationship with each user
    user = relationship("Users", back_populates='cart')

    # Defining one-to-many to cart item
    cart_item = relationship("CartItems", back_populates="cart")

    def get_current_cart_id(self):
        """returns the cart_id of the current user"""
        return Cart.query.filter_by(user_id=current_user.id).first().cart_id

    def __repr__(self):
        return f"cart - {self.cart_id}"


class Books(db.Model):
    __tablename__ = "BooksTable"

    book_id = db.Column(db.Integer(), primary_key=True)
    book_title = db.Column(db.String(200), nullable=False, unique=True)
    book_subtitle = db.Column(db.String(200), nullable=False)
    book_author = db.Column(db.String(200), nullable=False)
    book_category = db.Column(db.String(200), nullable=False)
    book_pages = db.Column(db.Integer(), nullable=False)
    book_price = db.Column(db.Integer(), nullable=False)
    book_isbn = db.Column(db.Integer(), nullable=False)
    book_cover = db.Column(db.String(200), nullable=False)
    qty_available = db.Column(db.Integer())

    # Defining many-to-one relationship to cart items
    cart_item = relationship("CartItems", back_populates="book")

    # To store list in string table columns by converting it into JSON
    def __init__(self, book_title, book_subtitle, book_author, book_category, book_pages, book_price, book_isbn,
                 book_cover, qty_available):
        self.book_title = book_title
        self.book_subtitle = book_subtitle
        self.book_author = json.dumps(book_author)
        self.book_category = json.dumps(book_category)
        self.book_pages = book_pages
        self.book_price = book_price
        self.book_isbn = book_isbn
        self.book_cover = book_cover
        self.qty_available = qty_available

    def get_authors(self):
        # converting JSON to list for retrieving
        return list(json.loads(self.book_author))

    def get_category(self):
        return json.loads(self.book_category)

    def __repr__(self):
        return f"book - {self.book_title}"


class CartItems(db.Model):
    __tablename__ = "CartItemsTable"

    item_id = db.Column(db.Integer(), primary_key=True)
    # foreignkey from Cart
    cart_id = db.Column(db.Integer(), db.ForeignKey(Cart.cart_id))
    # foreign key form book
    book_id = db.Column(db.Integer(), db.ForeignKey(Books.book_id))
    qty_ordered = db.Column(db.Integer(), nullable=False)
    offer_applied = db.Column(db.Boolean(), default=False, nullable=False)

    # many-to-one relationship between Cart.id and cart_items
    cart = relationship("Cart", back_populates="cart_item")

    # Many-to-one r/s with Books table
    book = relationship("Books", back_populates='cart_item')

    def __repr__(self):
        return f"item_id - {self.item_id}"


# # to create database
# db.create_all()

# # get all books from sub to fill it in BookTable
# from sub import Book
# b = Book()
# all_books = b.update_books()
# for book in all_books:
#     new_book = Books(
#         book_title=book['title'],
#         book_subtitle=book['subtitle'],
#         book_author=book['authors'],
#         book_category=book['categories'],
#         book_pages=book['pages'],
#         book_price=book['price'],
#         book_isbn=book['isbn'],
#         book_cover=book['img_url'],
#         qty_available=100,
#     )
#     db.session.add(new_book)
#     db.session.commit()


# Routes
@app.route('/')
def home():
    """home page of the application"""
    all_books = Books.query.all()
    if current_user.is_authenticated:
        name = current_user.username
    else:
        name = ''

    # Pagination - adding pages in home page (18 books/page)
    page = request.args.get('page', 1, type=int)
    books_per_page = 18
    start = (page - 1) * books_per_page
    end = start + books_per_page
    total_pages = (len(all_books) + books_per_page - 1) // books_per_page
    books_on_page = all_books[start:end]
    return render_template('index.html', books_on_page=books_on_page, total_pages=total_pages,
                           page=page, current_user=current_user)


@app.route('/bookview/<int:book_id>')
def bookview(book_id):
    """Book View page of the site"""
    book = Books.query.filter_by(book_id=book_id).first()
    authors = book.get_authors()
    categories = book.get_category()
    return render_template('book-view.html', book=book, authors=authors,
                           categories=categories, authors_len=len(authors), category_len=len(categories))


@app.route('/add_to_cart/<int:book_id>', methods=["POST", "GET"])
@login_required
def add_to_cart(book_id):
    """adds a book to cart from book-view.html"""
    # Checking if book already exists in cart.
    already_exists = CartItems.query.filter_by(book_id=book_id).first()
    if already_exists:
        already_exists.qty_ordered += 1
        db.session.commit()
        update_amount(book_id, 'add', 1)
    elif already_exists is None:
        print(current_user.is_authenticated)
        add_new_book = CartItems(
            cart_id=Cart.query.filter_by(user_id=current_user.id).first().cart_id,
            book_id=book_id,
            qty_ordered=1
        )
        db.session.add(add_new_book)
        db.session.commit()
        print('book added')
        update_amount(book_id, 'add', add_new_book.qty_ordered)
    return redirect(url_for('cart'))


@app.route('/cart')
@login_required
def cart():
    """Cart page : has book(s) that are in cart, login required"""
    book_qty = book_and_quantity()
    print(book_qty)
    return render_template('cart.html', current_user=current_user,
                           amount=round(current_user.amount, 3), books=book_qty)


@app.route('/update/<int:book_id>', methods=["POST"])
@login_required
def update(book_id):
    """Updates the quantity of a book(book_id) in CartItemsTable"""
    if request.method == "POST":
        book_to_update = CartItems.query.filter_by(book_id=book_id).first()
        # Checking if quantity to update is same as before
        existing_qty = book_to_update.qty_ordered
        new_qty = request.form.get('book_qty')
        if existing_qty != new_qty:
            book_to_update.qty_ordered = new_qty
            db.session.commit()
            # subtracting amount that was present before
            update_amount(book_id=book_id, operation='sub', qty=existing_qty)
            # adding amount with new quantity
            update_amount(book_id=book_id, operation='add', qty=new_qty)
        return redirect(url_for('cart'))


@app.route('/remove/<int:book_id>')
@login_required
def remove(book_id):
    """removes a book from cart using book_id in CartItemsTable"""
    print(book_id)
    book_to_remove = CartItems.query.filter_by(book_id=book_id).first()
    db.session.delete(book_to_remove)
    db.session.commit()
    update_amount(book_id=book_to_remove.book_id, operation='sub', qty=book_to_remove.qty_ordered)
    return redirect(url_for('cart'))


@app.route('/login', methods=["POST", "GET"])
def login():
    """login page"""
    if request.method == "POST":
        user = Users.query.filter_by(username=request.form.get('username')).first()
        if user:
            if bcrypt.check_password_hash(user.password, request.form.get('password')):
                # changing status: close > open. in Cart table
                open_cart = Cart.query.filter_by(user_id=user.id).first()
                open_cart.status = 'open'
                db.session.commit()
                login_user(user)
                return redirect(url_for('home'))

    return render_template('login.html', current_user=current_user)


@app.route('/register', methods=["GET", "POST"])
def register():
    """register page"""
    if request.method == "POST":
        new_user = Users(
            username=request.form.get('username'),
            email=request.form.get('email'),
            phone_number=request.form.get('phone'),
            password=bcrypt.generate_password_hash(password=request.form.get('password'), rounds=8),
            amount=0
        )
        db.session.add(new_user)
        db.session.commit()
        cart_row = Cart(
            user_id=new_user.id,
            status='close'
        )
        db.session.add(cart_row)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html', current_user=current_user)


@app.route('/filters/<string:category>', methods=["POST", "GET"])
def filters(category):
    """applies fiter on products in home page"""
    book = Books.query.filter(Books.book_category.like('%' + category + '%')).order_by(Books.book_id).all()
    return render_template('category.html', category=category, books=book)


@app.route('/search', methods=["POST", "GET"])
def search():
    if request.method == "POST":
        searched = request.form.get('searched')
        # Searching the database for searched book form navbar,
        # like() is used to find book titles that resembles searched text
        book = Books.query.filter(Books.book_title.like('%' + searched + '%'))
        book = book.order_by(Books.book_id).all()
        return render_template('search.html', searched=searched, searched_book=book)


@app.route('/logout')
@login_required
def logout():
    """ Logs user out and sets their status in CartTable to 'close' """
    user_cart = Cart.query.filter_by(user_id=current_user.id).first()
    user_cart.status = 'close'
    db.session.commit()
    logout_user()
    return redirect(url_for('home'))


# Payment
@app.route('/checkout', methods=["GET", "POST"])
@login_required
def checkout():
    """checkout page which collects users billing address"""
    book_qty = book_and_quantity()
    user_addr = Address.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST' and user_addr:
        # if user address is already present, edit address
        user_addr.first_name = request.form.get('firstname')
        user_addr.addr_st = request.form.get('streetaddress')
        user_addr.addr_city = request.form.get('city')
        user_addr.addr_state = request.form.get('state')
        user_addr.addr_pincode = request.form.get('pincode')
        db.session.commit()
        return redirect(url_for('bill'))
        
    elif request.method == 'POST':
        # add the form data to address info table, linked with UserTable
        new_address_info = Address(
            user_id=current_user.id,
            first_name=request.form.get('firstname'),
            addr_st=request.form.get('streetaddress'),
            addr_city=request.form.get('city'),
            addr_state=request.form.get('state'),
            addr_pincode=request.form.get('pincode')
        )
        db.session.add(new_address_info)
        db.session.commit()
        return redirect(url_for('bill'))
    offer = ''
    current_user_cart_items = CartItems.query.filter_by(cart_id=Cart().get_current_cart_id()).all()
    if not current_user_cart_items[0].offer_applied or current_user_cart_items[0] == 0:
        offer = apply_offers()
        for item in current_user_cart_items:
            item.offer_applied = True
            db.session.commit()
    return render_template('checkout.html', current_user=current_user,
                           books=book_qty, addr=user_addr, offer=offer)


@app.route('/bill')
@login_required
def bill():
    """payment portal for WM, uses RAZORPAY"""
    current_cart_id = Cart().get_current_cart_id()

    auth = ('', '') # the razor pay's auth info : (test_key, api_key)
    # razor pay code
    client = razorpay.Client(auth=auth)
    data = {"amount": (current_user.amount * 100), "currency": "INR", "receipt": f'{current_cart_id}'}
    payment = client.order.create(data=data)

    current_user_address = Address.query.filter_by(user_id=current_user.id).first()
    # applying offers
    return render_template('bill.html', payment=payment, addr=current_user_address,
                           current_user=current_user, books=book_and_quantity())


@app.route('/success')
@login_required
def payment_successful():
    """checks if payment made is successful or not"""
    current_user_cart_items = CartItems.query.filter_by(cart_id=Cart().get_current_cart_id()).all()
    send_mail()
    for item in current_user_cart_items:
        # deleting items present in cart
        db.session.delete(item)
        db.session.commit()
    # resetting users' amount
    current_user.amount = 0
    db.session.commit()
    return redirect(url_for('cart'))


@app.route('/failed')
@login_required
def payment_failed():
    """if payment is form inauthentic source"""
    print('payment failed')
    return redirect(url_for('checkout'))


# Admin privileges
@app.route('/admin', methods=["POST", "GET"])
@admin_only
def admin():
    """ADMINISTRATOR's dashboard"""
    books = Books.query.all()
    return render_template('admin.html', books=books)


@app.route('/add_book', methods=["GET", "POST"])
@admin_only
def add_book():
    """Adding new book to BooksTable"""
    if request.method == 'POST':
        new_book = Books(
            book_title=request.form.get('booktitle'),
            book_subtitle=request.form.get('booksubtitle'),
            book_author=request.form.get('bookauthor').split(','),
            book_category=request.form.get('bookcategory').split(','),
            book_pages=request.form.get('bookpages'),
            book_price=request.form.get('bookprice'),
            book_isbn=request.form.get('bookisbn'),
            book_cover=request.form.get('bookcoverurl'),
            qty_available=request.form.get('bookqty')
        )
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('add-book.html')


@app.route('/edit_book/<int:b_id>', methods=["POST", "GET"])
@admin_only
def edit_book(b_id):
    """Editing book in BooksTable"""
    book_to_edit = Books.query.filter_by(book_id=b_id).first()
    if request.method == "POST":
        book_to_edit.book_title = request.form.get('booktitle')
        book_to_edit.book_subtitle = request.form.get('booksubtitle')
        book_to_edit.book_cover = request.form.get('bookcoverurl')
        book_to_edit.qty_available = request.form.get('bookqty')
        db.session.commit()
        return redirect(url_for('admin'))

    return render_template('edit-book.html', book=book_to_edit)


@app.route('/delete_book/<int:b_id>')
@admin_only
def delete_book(b_id):
    """deleting book from BooksTable"""
    book_to_delete = Books.query.filter_by(book_id=b_id).first()
    db.session.delete(book_to_delete)
    db.session.commit()
    return redirect(url_for('admin'))


# Helpers
def send_mail():
    """sends mail to the current_user.email about his/her order"""
    to_email = Users.query.filter_by(id=current_user.id).first().email
    today = datetime.datetime.now().date()
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Test HTML Email'
    msg['From'] = my_email
    msg['To'] = current_user.email
    text = MIMEText(f"""
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, user-scalable=no, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="ie=edge">
    </head>
    <body>
        <h1>Order placed successfully in WisdomManuals.com</h1>
        <p>Name -  {current_user.username} </p>
        <p>{book_and_quantity().keys()}</p>
        <p>Total {current_user.amount} : PAID</p>
        <h2>Your order will be delivered within 7-9 days({today+datetime.timedelta(days=7)} - {today+datetime.timedelta(days=9)})</h2>
        <p>This is a test mail - there is no real WM.com</p>
    </body>
    </html>
    """, 'html')
    msg.attach(text)
    with smtplib.SMTP(host='smtp.gmail.com', port=587) as con:
        con.starttls()
        con.login(my_email, pwd)
        con.sendmail(from_addr=my_email,
                     to_addrs=current_user.email,
                     msg=msg.as_string())

def apply_offers() -> str:
    """applies offer when checking out"""
    offer = ''
    amount = current_user.amount
    if amount > 5000:
        current_user.amount -= 500
        db.session.commit()
        offer += 'books > ₹5,000, so ₹500 off'
    elif amount > 1000:
        current_user.amount -= 100
        db.session.commit()
        offer += 'books > ₹1,000, so ₹100 off'
    print(offer)
    return offer

def book_and_quantity() -> dict:
    """Returns current_user's dictionary of {ordered Book(object) : and its quantity}"""
    # Getting cart_id of the current_user from CartTable
    cart_id = Cart().get_current_cart_id()
    # Using that cart_id to query all items with that id from CartItemsTable
    cart_items = CartItems.query.filter_by(cart_id=cart_id).order_by('cart_id').all()
    # Using the cart_items(object) to get books form BooksTable using book_id in CartItemsTable
    # And creating a dictionary book_qty = {book(object) : its quantity}
    book_qty = {Books.query.filter_by(book_id=i.book_id).first(): i.qty_ordered for i in cart_items}
    return book_qty


def update_amount(book_id, operation, qty):
    """updates amount of the current user when a book is added, reduced or removed from cart"""
    book = Books.query.filter_by(book_id=book_id).first()
    price = book.book_price
    book_qty = book.qty_available
    print(price)
    if operation == 'add':
        print('amount updated')
        current_user.amount += price * int(qty)
        book_qty -= int(qty)
        db.session.commit()
        print(current_user.amount)
    elif operation == 'sub':
        print('amount decreased')
        current_user.amount -= price * int(qty)
        book_qty += int(qty)
        db.session.commit()
        print(current_user.amount)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
