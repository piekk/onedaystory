from artapp import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(22), unique=True,  nullable=False)
    email = db.Column(db.String(40), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    firstname = db.Column(db.String(30), nullable=True)
    lastname = db.Column(db.String(40), nullable=True)
    contact = db.Column(db.String(12), unique=True, nullable=True)
    alter_contact = db.Column(db.String(10), unique=True, nullable=True)
    role = db.Column(db.String(6), unique=False, nullable=False)
    description = db.Column(db.Text, nullable=True)
    style = db.Column(db.String(40), unique=False, nullable=True)
    verified = db.Column(db.String(3), unique=False, default='no', nullable=False)
    rank = db.Column(db.Numeric(10,2), unique=False, default=1.00, nullable=False)
    date_register = db.Column(db.DateTime, unique=False, nullable=False)
    total_bought = db.Column(db.Integer, unique=False, nullable=True, default=0)
    otp = db.Column(db.String(12), unique=True, nullable=True)
    otp_expire = db.Column(db.DateTime, unique=False, nullable=True)
    product = db.relationship("Products", backref="owner_product")
    payment_due = db.relationship("PaymentDue", backref="owner_paymentdue")
    payment_recieve = db.relationship("PaymentRecieved", backref="owner_paymentrevieve")
    address = db.relationship("Address", backref="owner_address", uselist=False)
    cart = db.relationship("Cart", backref='cartowner', uselist=False)
    review = db.relationship("Reviews", backref='owner_review', uselist=False)

    def __repr__(self):
        return "(username: %s)" % (self.username)

class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_add = db.Column(db.DateTime, unique=False, nullable=False)
    productcode = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(35), unique=False, nullable=False)
    price = db.Column(db.String(7), unique=False, nullable=False)
    shipping_fee= db.Column(db.String(5), unique=False, nullable=False)
    promotion = db.Column(db.String(6), unique=False, nullable=True, default=0)
    promotion_expire = db.Column(db.DateTime, unique=False, nullable=True)
    imgfile1 = db.Column(db.String(50), unique=True, nullable=False)
    imgfile2 = db.Column(db.String(50), unique=True, nullable=True)
    imgfile3 = db.Column(db.String(50), unique=True, nullable=True)
    imgfile4 = db.Column(db.String(50), unique=True, nullable=True)
    quantity = db.Column(db.Integer, unique=False, nullable=False, default=0)
    category = db.Column(db.String(20), unique=False, nullable=False, default='Category')
    style = db.Column(db.String(50), unique=False, nullable=True, default='Style')
    size = db.Column(db.String(40), unique=False, nullable=True)
    object_size = db.Column(db.String(40), unique=False, nullable=True)
    frame = db.Column(db.String(40), unique=False, nullable=True)
    condition = db.Column(db.String(15), unique=False, nullable=True)
    book_condition = db.Column(db.String(15), unique=False, nullable=True)
    authors = db.Column(db.String(40), unique=False, nullable=True)
    description = db.Column(db.Text, nullable=True)
    view = db.Column(db.Integer, unique=False, nullable=False, default=0)
    number_bought = db.Column(db.Integer, unique=False, nullable=False, default=0)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return "(title: %s)" % (self.title)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cartcode = db.Column(db.String(30), unique=True, nullable=False)
    reference_id = db.Column(db.String(10), unique = True, nullable=False)
    payment = db.Column(db.String(2), unique= False, default = 'N')
    date_create = db.Column(db.DateTime, nullable=False)
    date_expire = db.Column(db.DateTime, nullable=False)
    payment_expire = db.Column(db.DateTime, nullable=True)
    owner = db.Column(db.Integer, db.ForeignKey('user.id'))
    items = db.relationship("CartItems", backref='cart')
    shippingaddress = db.relationship("ShipAddress", backref='cartshipaddress', uselist=False)

    def __repr__(self):
        return "(CartCode: %s)" % (self.cartcode)

class CartItems(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(50), unique=False, nullable=False)
    img = db.Column(db.String(50), unique=False, nullable=False)
    quantity = db.Column(db.Integer, unique=False, nullable=False, default=1)
    price = db.Column(db.String(7), unique=False, nullable=False)
    seller = db.Column(db.String(12), unique=False,  nullable=False)
    status = db.Column(db.String(20), unique=False, nullable=False, default = 'pending')
    tracking = db.Column(db.String(15), unique=False,  nullable=True)
    cartID = db.Column(db.Integer, db.ForeignKey('cart.id'))

    def __repr__(self):
        return "(Product: %s)" % (self.product)


class ShipAddress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(30), unique=False, nullable=False)
    lastname = db.Column(db.String(30), unique=False, nullable=False)
    contact = db.Column(db.String(20), unique=False, nullable=False)
    homeaddress = db.Column(db.String(40), unique=False, nullable=False)
    housename = db.Column(db.String(30), unique=False, nullable=True)
    street = db.Column(db.String(40), unique=False, nullable=True)
    sub_street = db.Column(db.String(50), unique=False, nullable=True)
    subdistrict = db.Column(db.String(30), unique=False, nullable=False)
    district = db.Column(db.String(30), unique=False, nullable=False)
    province = db.Column(db.String(30), unique=False, nullable=False)
    country = db.Column(db.String(34), unique=False, nullable=False)
    postcode = db.Column(db.Integer, unique=False, nullable=False)
    cart_address = db.Column(db.Integer, db.ForeignKey('cart.id'))

    def __repr__(self):
        return "(Name: {} {})" .format(self.firstname, self.lastname)

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    homeaddress = db.Column(db.String(40), unique=False, nullable=False)
    housename = db.Column(db.String(30), unique=False, nullable=True)
    street = db.Column(db.String(40), unique=False, nullable=True)
    sub_street = db.Column(db.String(40), unique=False, nullable=True)
    subdistrict = db.Column(db.String(20), unique=False, nullable=False)
    district = db.Column(db.String(20), unique=False, nullable=False)
    province = db.Column(db.String(24), unique=False, nullable=False)
    country = db.Column(db.String(24), unique=False, nullable=False)
    postcode = db.Column(db.Integer, unique=False, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return "(Name: {})" .format(self.owner_id)

class PaymentDue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_firstname =  db.Column(db.String(30), unique=False, nullable=True)
    buyer_lastname =  db.Column(db.String(30), unique=False, nullable=True)
    item = db.Column(db.String(50), unique=False, nullable=False)
    order_no = db.Column(db.String(10), unique = False, nullable=False)
    paid_on = db.Column(db.DateTime, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    amount = db.Column(db.String(7), unique=False, nullable=False)
    recipient = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return "(เลขที่: {})" .format(self.id)

class PaymentRecieved(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_firstname =  db.Column(db.String(30), unique=False, nullable=True)
    buyer_lastname =  db.Column(db.String(30), unique=False, nullable=True)
    item = db.Column(db.String(50), unique=False, nullable=False)
    order_no = db.Column(db.String(10), unique = False, nullable=False)
    paid_on = db.Column(db.DateTime, nullable=True)
    recieve_date = db.Column(db.DateTime, nullable=True)
    amount = db.Column(db.String(7), unique=False, nullable=False)
    recipient = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return "(เลขที่: {})" .format(self.id)

class Reviews(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    star_rating = db.Column(db.Integer, unique=False, nullable=False)
    messages = db.Column(db.String(100), nullable=True)
    review_by = db.Column(db.String(12), nullable=False)
    review_date = db.Column(db.DateTime, nullable=False)
    merchant = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return "(star_rating: {}, by: {})" .format(self.star_rating, self.review_by)


class Articles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), unique=True, nullable=False)
    sub_title = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    image1 = db.Column(db.String(50), unique=True, nullable=True)
    image2 = db.Column(db.String(50), unique=True, nullable=True)
    image3 = db.Column(db.String(50), unique=True, nullable=True)
    meta_keyword = db.Column(db.String(30), unique=False, nullable=True)
    title_element = db.Column(db.String(20), unique=True, nullable=False)
    meta_description = db.Column(db.Text, nullable=False)
    date_publish = db.Column(db.DateTime, nullable=False)

    author = db.Column(db.String(10), unique=False, nullable=False)

    def __repr__(self):
        return "(Article: {}, Author: {}, Publish: {})" .format(self.title, self.author, self.date_publish)


class Voucher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(7), unique=False, nullable=False)
    code = db.Column(db.String(60), unique=True, nullable=False)
    gernerate_by = db.Column(db.String(12), unique=True,  nullable=False)
    generate_date = db.Column(db.DateTime, nullable=False)
    expiry_date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return "(id: {}, Value: {}, by: {})" .format(self.id, self.value, self.generate_by)
