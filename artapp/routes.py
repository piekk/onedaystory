import os
import uuid
from PIL import Image
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask import render_template, request, url_for, redirect, flash, jsonify, json, session
from artapp import app, db, bcrypt, margin
from artapp.forms import RegistrationForm, LoginForm, MerchantRegistrationForm, ChangeStatusForm, MerchantLoginForm, ProductForm, EditImageForm, EditDetailForm, EditPriceForm, EditStockForm, Profile, Ship_Address, EditImageForm
from artapp.models import User, Products, Cart, CartItems, Articles, ShipAddress, Address
from flask_login import login_user, current_user, logout_user, login_required
from google.cloud import storage

default_title = "Onedaystory ตลาดศิลปะและของแต่งบ้าน"
short_title = "Onedaystory "

@app.route('/')
def home():
    illustration = Products.query.filter(Products.category=='illustration').order_by(Products.view.asc()).limit(12).all()
    painting = Products.query.filter(Products.category=='painting').order_by(Products.view.desc()).limit(12).all()
    photography = Products.query.filter(Products.category=='photograph').order_by(Products.view.desc()).limit(12).all()
    decorations = Products.query.filter(Products.category=='decoration').order_by(Products.view.desc()).limit(12).all()
    books = Products.query.filter(Products.category=='book').order_by(Products.view.desc()).limit(12).all()
    latest = Products.query.filter(Products.quantity>0).order_by(Products.date_add.desc()).limit(12).all()
    time = datetime.now()
    return render_template("home.html", title=default_title, latest=latest, illustration=illustration, painting=painting, photography=photography, decorations=decorations, books=books, margin=margin, time=time, bucket = app.config['BUCKET'])


@app.route('/gallery/', defaults={'filter':None})
@app.route('/gallery/<filter>')
def gallery(filter):
    page = request.args.get('page', 1,type=int)
    productcategory = ['illustration', 'painting', 'photograph', 'decoration', 'book']
    if filter == None:
        time = datetime.now()
        product = Products.query.order_by(Products.view.desc()).paginate(per_page=10, page=page)
        return render_template("gallery.html", title=default_title, product = product, margin=margin, time=time, filter='gallery', bucket = app.config['BUCKET'])
    elif filter == 'latest':
        time = datetime.now()
        product = Products.query.filter(Products.quantity>0).order_by(Products.date_add.desc()).paginate(per_page=10, page=page)
        return render_template("gallery.html", title=default_title, product = product, margin=margin, time=time, filter=filter, bucket = app.config['BUCKET'])
    elif filter in productcategory:
        time = datetime.now()
        product = Products.query.filter(Products.category==filter).paginate(per_page=10, page=page)
        return render_template("gallery.html", title=short_title+filter, product = product, margin=margin, time=time, filter=filter, bucket = app.config['BUCKET'])
    else:
        time = datetime.now()
        fil = secure_filename(filter)
        searchwordlower = fil.lower()
        searchword = searchwordlower.replace(" ","")
        product = Products.query.filter(Products.style.contains(searchword)).paginate(per_page=10, page=page)
        return render_template("gallery.html", title=short_title+filter, product = product, margin=margin, time=time, filter=filter, bucket = app.config['BUCKET'])

def check_promotion(p_insert):
    time = datetime.now()
    return int(p_insert.promotion)> 0 and time < p_insert.promotion_expire


@app.route('/product/<product>', methods=['GET', 'POST'])
def product(product):
    time = datetime.now()
    product=Products.query.filter_by(productcode=product).first()
    if request.method == 'POST' and current_user.is_authenticated:
        cart = Cart.query.filter_by(cartcode=current_user.username).first()
        if cart and cart.payment == 'N':
            if len(cart.items)== 0:
                if check_promotion(product):
                    product_price = round((int(product.price)*(1-int(product.promotion)/100))*margin)+int(product.shipping_fee)
                    db.session.commit()
                else:
                    product_price = round(int(product.price)*margin)+int(product.shipping_fee)
                    db.session.commit()
                db.session.add(CartItems(product = product.productcode, img=product.imgfile1, quantity=1, price=product_price, seller=product.owner_product.username, cart=cart))
                db.session.commit()
                return redirect(url_for('cart'))
            else:
                listofitem = []
                for item in cart.items:
                    listofitem.append(item.product)
                if product.productcode in listofitem:
                    return redirect(url_for('cart'))
                else:
                    if check_promotion(product):
                        product_price = round((int(product.price)*(1-int(product.promotion)/100))*margin)+int(product.shipping_fee)
                    else:
                        product_price = round(int(product.price)*margin)+int(product.shipping_fee)
                    db.session.add(CartItems(product = product.productcode, img=product.imgfile1, quantity=1, price=product_price, seller=product.owner_product.username, cart=cart))
                    db.session.commit()
                    return redirect(url_for('cart'))
        elif cart and cart.payment=='W' and time > cart.payment_expire:
            for item in cart.items:
                product=Products.query.filter_by(productcode=item.product).first()
                product.quantity += item.quantity
                db.session.delete(item)
                db.session.commit()
            if cart.shippingaddress:
                db.session.delete(cart.shippingaddress)
                db.session.delete(cart)
                db.session.commit()
            else:
                db.session.delete(cart)
                db.session.commit()
            time = datetime.now()
            timecreate = time.strftime("%Y-%m-%d  %H:%M")
            expire = datetime.now() + timedelta(days=30)
            timeexpire = expire.strftime("%Y-%m-%d  %H:%M")
            reference = uuid.uuid4().hex[:4].upper()+time.strftime("%m%d")+uuid.uuid4().hex[:2]
            db.session.add(Cart(cartcode=current_user.username, reference_id=reference, date_create=timecreate, date_expire=timeexpire,cartowner=current_user))
            db.session.commit()
            cart = Cart.query.filter_by(cartcode=current_user.username).first()
            if check_promotion(product):
                product_price = round((int(product.price)*(1-int(product.promotion)/100))*margin)+int(product.shipping_fee)
                db.session.commit()
            else:
                product_price = round(int(product.price)*margin)+int(product.shipping_fee)
                db.session.commit()
            db.session.add(CartItems(product = product.productcode, img=product.imgfile1, quantity=1, price=product_price, seller=product.owner_product.username, cart=cart))
            db.session.commit()
            return redirect(url_for('cart'))
        elif cart and cart.payment == 'W':
            if cart.shippingaddress:
                return redirect(url_for('payment'))
            else:
                return redirect(url_for('address'))
        else:
            timecreate = datetime.now().strftime("%Y-%m-%d  %H:%M")
            expire = datetime.now() + timedelta(days=30)
            timeexpire = expire.strftime("%Y-%m-%d  %H:%M")
            reference = uuid.uuid4().hex[:4].upper()+datetime.now().strftime("%m%d")+uuid.uuid4().hex[:2]
            db.session.add(Cart(cartcode=current_user.username, reference_id=reference, date_create=timecreate, date_expire=timeexpire,cartowner=current_user))
            db.session.commit()
            cart = Cart.query.filter_by(cartcode=current_user.username).first()
            if check_promotion(product):
                product_price = round((int(product.price)*(1-int(product.promotion)/100))*margin)+int(product.shipping_fee)
                db.session.commit()
            else:
                product_price = round(int(product.price)*margin)+int(product.shipping_fee)
                db.session.commit()
            db.session.add(CartItems(product = product.productcode, img=product.imgfile1, quantity=1, price=product_price, seller=product.owner_product.username, cart=cart))
            db.session.commit()
            return redirect(url_for('cart'))
    elif request.method == 'POST':
        return redirect(url_for('login', productcode=product.productcode))
    elif not product:
        return redirect(url_for('home'))
    else:
        time = datetime.now()
        product.view += 1
        db.session.commit()
        return render_template("product.html", product = product, time=time, margin=margin, bucket=app.config['BUCKET'])


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method=='POST':
        if 'todelete' in request.form:
            todelete = request.form.get('todelete')
            delete = CartItems.query.get(todelete)
            db.session.delete(delete)
            db.session.commit()
            return redirect(url_for('cart'))
        elif 'checkout' in request.form:
            cart = Cart.query.filter_by(cartcode=current_user.username).first()
            expire = datetime.now() + timedelta(days=1)
            timeexpire = expire.strftime("%Y-%m-%d  %H:%M")
            cart.payment = 'W'
            cart.payment_expire = timeexpire
            cart.date_expire = timeexpire
            db.session.commit()
            for item in cart.items:
                product=Products.query.filter_by(productcode=item.product).first()
                if item.quantity > product.quantity:
                    message = "Some products are no longer available"
                    return redirect("cart", message = message)
                else:
                    if check_promotion(product):
                        item.price = round((int(product.price)*(1-int(product.promotion)/100))*margin)+int(product.shipping_fee)
                        product.quantity = product.quantity-item.quantity
                        db.session.commit()
                    else:
                        item.price = round(int(product.price)*margin)+int(product.shipping_fee)
                        product.quantity = product.quantity-item.quantity
                        db.session.commit()
            return redirect(url_for('address'))
    elif current_user.is_authenticated:
        time = datetime.now()
        try:
            cart = current_user.cart
        except:
            message = "Your Cart is empty"
            return render_template("cart.html", message = message)
        if cart and cart.payment == 'W' and time > cart.payment_expire:
            if cart.items:
                for item in cart.items:
                    product=Products.query.filter_by(productcode=item.product).first()
                    product.quantity += item.quantity
                    db.session.delete(item)
                    db.session.commit()
                if cart.shippingaddress:
                    db.session.delete(cart.shippingaddress)
                    db.session.delete(cart)
                    db.session.commit()
                else:
                    db.session.delete(cart)
                    db.session.commit()
            else:
                if cart.shippingaddress:
                    db.session.delete(cart.shippingaddress)
                    db.session.delete(cart)
                    db.session.commit()
                else:
                    db.session.delete(cart)
                    db.session.commit()
            return redirect('cart')
        elif cart and cart.payment == 'W':
            if cart.shippingaddress:
                return redirect(url_for('payment'))
            else:
                return redirect(url_for('address'))
        elif cart and cart.items and cart.payment == 'N' and cart.date_expire > time:
            product_inventory = {}
            price = {}
            for item in cart.items:
                product=Products.query.filter_by(productcode=item.product).first()
                if product.quantity > 0 and product.quantity >= item.quantity:
                    product_inventory[product.productcode] = product.quantity
                    if check_promotion(product):
                        price[product.productcode] = round((int(product.price)*(1-int(product.promotion)/100))*margin)+int(product.shipping_fee)
                    else:
                        price[product.productcode] = round(int(product.price)*margin)+int(product.shipping_fee)
                elif product.quantity > 0 and product.quantity < item.quantity:
                    item.quantity = product.quantity
                    db.session.commit()
                    product_inventory[product.productcode] = product.quantity
                    if check_promotion(product):
                        price[product.productcode] = round((int(product.price)*(1-int(product.promotion)/100))*margin)+int(product.shipping_fee)
                    else:
                        price[product.productcode] = round(int(product.price)*margin)+int(product.shipping_fee)
                else:
                    db.session.delete(item)
                    db.session.commit()
            if product_inventory == {}:
                message = "Product is no longer available"
                return render_template("cart.html", message = message)
            else:
                return render_template("cart.html", cart = cart, product_inventory = product_inventory, bucket=app.config['BUCKET'], price=price)
        elif cart and cart.items and cart.payment == 'N' and cart.date_expire < time:
            for item in cart.items:
                db.session.delete(item)
                db.session.commit()
            if cart.shippingaddress:
                db.session.delete(cart.shippingaddress)
                db.session.delete(cart)
                db.session.commit()
            else:
                db.session.delete(cart)
                db.session.commit()
            message = "Your Cart is empty"
            return render_template("cart.html", message = message)
        else:
            message = "Your Cart is empty"
            return render_template("cart.html", message = message)
    else:
        return redirect(url_for('login'))


@app.route('/cart/process', methods=['POST'])
def process():
    cart = Cart.query.filter_by(cartcode=current_user.username).first()
    data = request.json
    json_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.username+'item.json')
    with open(json_path, 'w') as f:
            json.dump(data, f)
    for item in cart.items:
        item.quantity = data[item.product]
        db.session.commit()
    return jsonify(data)

@app.route('/address', methods=['GET', 'POST'])
def address():
    form = Ship_Address()
    if form.validate_on_submit():
        try:
            db.session.add(ShipAddress(firstname=form.firstname.data, lastname=form.lastname.data, contact=form.contact.data,
                                       homeaddress=form.homeaddress.data, housename=form.housename.data,
                                       street=form.street.data, sub_street=form.substreet.data,
                                       subdistrict=form.subdistrict.data, district=form.district.data,
                                       province=form.province.data, country='Thailand', postcode=form.postcode.data,
                                       cartshipaddress = current_user.cart))
            db.session.add(Address(homeaddress=form.homeaddress.data, housename=form.housename.data,
                                   street=form.street.data, sub_street=form.substreet.data,
                                   subdistrict=form.subdistrict.data, district=form.district.data,
                                   province=form.province.data, country='Thailand', postcode=form.postcode.data,
                                   owner_address = current_user))
            db.session.commit()
            return redirect(url_for('payment'))
        except:
            message = "ข้อมูลผิดพลาด"
            return render_template("address.html", form=form, message=message)
    elif current_user.is_anonymous:
        return redirect(url_for('login'))
    else:
        cart = current_user.cart
        time = datetime.now()
        if cart:
            if cart.shippingaddress and cart.date_expire > time:
                return redirect(url_for('payment'))
            elif cart.payment=='N':
                return redirect(url_for('cart'))
            elif current_user.address and cart.date_expire > time:
                form.firstname.data = current_user.firstname
                form.lastname.data = current_user.lastname
                form.contact.data = current_user.contact
                form.homeaddress.data = current_user.address.homeaddress
                form.street.data = current_user.address.street
                form.substreet.data = current_user.address.sub_street
                form.subdistrict.data = current_user.address.subdistrict
                form.district.data = current_user.address.district
                form.province.data = current_user.address.province
                form.postcode.data = current_user.address.postcode
                return render_template("address.html", form=form)
            elif cart.date_expire > time:
                form.firstname.data = current_user.firstname
                form.lastname.data = current_user.lastname
                form.contact.data = current_user.contact
                return render_template("address.html", form=form)
            else:
                return redirect(url_for('cart'))
        elif not cart:
            return redirect(url_for('cart'))
        else:
            return redirect(url_for('address'))

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if current_user.is_anonymous:
        redirect (url_for('login'))
    else:
        cart = current_user.cart
        product_title = {}
        cart_total = 0
        for item in cart.items:
            cart_total += int(item.price) * item.quantity
            t = Products.query.filter_by(productcode = item.product).first()
            product_title[item.product] = t.title
        return render_template("payment.html", cart = cart, cart_total = cart_total, product_title=product_title, bucket = app.config['BUCKET'])


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        phone = str(form.contact.data)
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        time = datetime.now()
        try:
            db.session.add(User(username=form.username.data, email=form.email.data, password=hashed_pw, role='Buyer', contact = phone, date_register= time.strftime("%Y-%m-%d  %H:%M")))
            db.session.commit()
            user = User.query.filter_by(email=form.email.data).first()
            login_user(user)
            session.permanent = True
            return redirect(url_for('home'))
        except:
            flash('Email is already registered')
            return redirect(url_for('login'))
    return render_template("register.html", title='Register', form=form)


@app.route('/login/', defaults={'productcode':None}, methods=['GET', 'POST'])
@app.route('/login/<productcode>', methods=['GET', 'POST'])
def login(productcode):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data) and user.role=='Buyer':
            login_user(user)
            session.permanent = True
            if productcode == None:
                return redirect(url_for('home'))
            else:
                try:
                    return redirect(url_for('product',product=productcode))
                except:
                    return redirect(url_for('home'))
        elif user and bcrypt.check_password_hash(user.password, form.password.data) and user.role=='Seller':
            login_user(user)
            session.permanent = True
            if productcode == None:
                return redirect(url_for('merchant', name=user.username))
            else:
                try:
                    return redirect(url_for('product',product=productcode))
                except:
                    return redirect(url_for('merchant', name=user.username))
        elif user and bcrypt.check_password_hash(user.password, form.password.data) and user.role=='admin':
            login_user(user)
            return redirect(url_for('admin', name=user.username))
        elif not user:
            flash("EMAIL NOT FOUND")
            return redirect(url_for('login'))
        else:
            flash("INCORRECT PASSWORD")
            return redirect(url_for('login'))
    return render_template("login.html", title='login', form=form, product=productcode)


@app.route('/merchantregister', methods=['GET', 'POST'])
def merchantregister():
    form = MerchantRegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        phone = str(form.contact.data)
        time = datetime.now()
        try:
            db.session.add(User(firstname=form.firstname.data, lastname=form.lastname.data, username=form.username.data, email=form.email.data, password=hashed_pw, verified='no', contact=phone, role='Seller', date_register=time.strftime("%Y-%m-%d  %H:%M")))
            db.session.commit()
            user = User.query.filter_by(email=form.email.data).first()
            login_user(user)
            session.permanent = True
            return redirect(url_for('merchant', name=current_user.username))
        except:
            flash("Email  is already registered")
            return redirect(url_for('merchantlogin'))
    elif current_user.is_authenticated:
        return redirect (url_for('home'))
    else:
        return render_template("merchantregister.html", title='', form=form)

@app.route('/changeuserstatus', methods=['GET', 'POST'])
def changeuserstatus():
    form = ChangeStatusForm()
    if form.validate_on_submit():
        try:
            current_user.firstname = form.firstname.data
            current_user.lastname = form.lastname.data
            current_user.role = 'Seller'
            db.session.commit()
            return redirect (url_for('merchant', name=current_user.username))
        except:
            return redirect(url_for('changeuserstatus'))
    elif current_user.role == 'Buyer':
        return render_template("changeuserstatus.html", form=form)
    else:
        return redirect (url_for('home'))

@app.route('/merchantlogin', methods=['GET', 'POST'])
def merchantlogin():
    form = MerchantLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data) and user.role=='Seller':
            login_user(user)
            session.permanent = True
            return redirect(url_for('merchant', name=user.username))
        elif not user:
            flash("EMAIL NOT FOUND")
            return redirect(url_for('merchantlogin'))
        else:
            flash("INCORRECT PASSWORD")
            return redirect(url_for('merchantlogin'))
    return render_template("merchantlogin.html", form=form)

@app.route('/view/<name>')
def view(name):
    user= User.query.filter_by(username=name).first()
    if user.role == 'Seller':
        return render_template("view.html", user=user, bucket=app.config['BUCKET'])
    else:
        return redirect(url_for('home'))

#Group merchant page merchant,edit,addproduct,accout detail
@app.route('/merchant/<name>', methods=['GET'])
@login_required
def merchant(name):
    if current_user.role == 'Seller' and current_user.username == name:
        time = datetime.now()
        product = Products.query.filter_by(owner_id=current_user.id)
        order = CartItems.query.join(Cart,(Cart.payment!='N')).filter(CartItems.seller == current_user.username).all()
        return render_template("merchant.html", product=product, order=order, time=time, bucket=app.config['BUCKET'])
    elif current_user.role == 'Seller':
        return redirect(url_for('merchant', name =current_user.username))
    else:
        return redirect(url_for('home'))


@app.route('/merchant/<name>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(name):
    form = Profile()
    user = User.query.filter_by(username=name).first()
    if current_user.role == 'Seller' and name == current_user.username:
        if form.validate_on_submit():
            current_user.username = form.username.data
            current_user.email  = form.email.data
            db.session.commit()
            return redirect(url_for('merchant', name=current_user.username))
        elif request.method == 'GET':
            form.username.data = current_user.username
            form.email.data = current_user.email
            return render_template("edit.html", form=form, user=user)
    elif current_user.role == 'admin':
        if form.validate_on_submit():
            user.username = form.username.data
            user.email  = form.email.data
            db.session.commit()
            return redirect(url_for('merchant', name=current_user.username, user=user))
        elif request.method == 'GET':
            form.username.data = user.username
            form.email.data = user.email
            return render_template("edit.html", form=form, user=user)
    else:
        return redirect(url_for('home'))


@app.route('/addcontact', methods=['GET', 'POST'])
@login_required
def add_contact():
        return redirect(url_for('home'))


def save_picture(form_picture,name,filetype):
    picture_fn = secure_filename(name + '.jpg')
    picture_path = os.path.join(app.config['UPLOAD_FOLDER'], picture_fn)
    output_size = (1000,1000)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(app.config['BUCKET'])
    blob = bucket.blob('product/'+filetype+'/'+picture_fn)
    blob.upload_from_filename(picture_path)

    return picture_path

def delete_blob(blob_name):
    bucket_name = app.config['BUCKET']
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()

    return blob_name


@app.route('/merchant/product', methods=['GET', 'POST'])
@login_required
def addproduct():
    if current_user.role == 'Seller' and current_user.verified == 'y':
        form = ProductForm()
        if form.validate_on_submit():
            name = str(current_user.id) + 'ID'+uuid.uuid4().hex[:6]
            category = form.category.data
            filename = 'product/'+category+'/'+ secure_filename(name+'.jpg')
            productcode = form.title.data + str(current_user.id)
            keyword = form.style.data.lower()
            time = datetime.now()
            noofdays = form.promotion_expire.data
            promotion_expiry_date = datetime.now() + timedelta(days=noofdays)
            expire_on = promotion_expiry_date.strftime("%Y-%m-%d")
            try:
                save_picture(form.photo1.data, name, category)
                db.session.add(Products(productcode=productcode, date_add=time.strftime("%Y-%m-%d, %H:%M"),
                                        title=form.title.data, price=form.price.data, shipping_fee=form.shipping_fee.data,
                                        imgfile1=filename, quantity=form.quantity.data, category=category, promotion=form.promotion.data,
                                        promotion_expire=expire_on, style=keyword, description=form.description.data, size=form.size.data,
                                        object_size=form.object_size.data, frame=form.frame.data, authors=form.authors.data,
                                        condition=form.condition.data, book_condition=form.book_condition.data, owner_product=current_user))
                db.session.commit()
                return redirect(url_for('edit_product', name=productcode))
            except:
                delete_blob(filename)
                flash("unsuccess")
                return redirect(url_for('addproduct'))
        else:
            return render_template("addproduct.html", form=form, margin=margin)
    elif current_user.role == 'Seller' and current_user.verified == 'no':
        return redirect(url_for('merchant', name = current_user.username))
    else:
        return redirect(url_for('home'))

@app.route('/merchant/product/edit/<name>', methods=['GET', 'POST'])
@login_required
def edit_product(name):
    time = datetime.now()
    product=Products.query.filter_by(productcode=name).first()
    if current_user.id == product.owner_id:
        in_cart = CartItems.query.filter(CartItems.product == product.productcode).first()
        if in_cart:
            message = "มีสินค้าอยู่ในตะกร้าสินค้าของผู้ซื้อ ไม่สามารถเปลี่ยนข้อมูลสินค้านี้ได้"
            return render_template("editproduct.html", time=time,  product=product, margin=margin, message=message, bucket = app.config['BUCKET'])
        else:
            return render_template("editproduct.html", time=time, product=product, margin=margin, bucket = app.config['BUCKET'])
    else:
        return redirect (url_for('merchant', name=current_user.username))

@app.route('/merchant/product/image/<name>', methods=['GET', 'POST'])
@login_required
def update_image(name):
    form = EditImageForm()
    product=Products.query.filter_by(productcode=name).first()
    in_cart = CartItems.query.filter(CartItems.product == product.productcode).first()
    if form.validate_on_submit():
        try:
            name = str(current_user.id) + 'ID'+uuid.uuid4().hex[:6]
            category = product.category
            filename = 'product/'+category+'/'+ secure_filename(name+'.jpg')
            save_picture(form.image.data, name, category)
            delete_blob(product.imgfile1)
            product.imgfile1 = filename
            db.session.commit()
            return redirect (url_for('edit_product', name=product.productcode))
        except:
            return "incomplete"
    elif request.method == 'GET' and product.owner_id == current_user.id:
        in_cart = CartItems.query.filter(CartItems.product == name).first()
        if in_cart:
            return redirect(url_for('edit_product', name=product.productcode))
        else:
            return render_template("updateimage.html", form=form, product=product, bucket= app.config['BUCKET'])
    else:
        return redirect (url_for('merchant', name=current_user.username))


@app.route('/merchant/product/detail/<name>', methods=['GET', 'POST'])
@login_required
def update_detail(name):
    product = Products.query.filter_by(productcode=name).first()
    form = EditDetailForm()
    if form.validate_on_submit():
        keyword = form.tag.data.lower()
        product.frame = form.frame.data
        product.style = keyword
        product.size = form.size.data
        product.object_size = form.object_size.data
        product.description = form.description.data
        db.session.commit()
        return redirect (url_for('edit_product', name = product.productcode))
    elif request.method == 'GET' and product.owner_id == current_user.id:
        in_cart = CartItems.query.filter(CartItems.product == name).first()
        if in_cart:
            return redirect (url_for('edit_product', name = product.productcode))
        else:
            form.frame.data = product.frame
            form.tag.data = product.style
            form.object_size.data = product.object_size
            form.size.data = product.size
            form.description.data = product.description
            return render_template("updatedetail.html", form=form, product=product, bucket=app.config['BUCKET'])
    else:
        return redirect (url_for('merchant', name=current_user.username))

@app.route('/merchant/product/price/<name>', methods=['GET', 'POST'])
@login_required
def update_price(name):
    product = Products.query.filter_by(productcode=name).first()
    time = datetime.now()
    form = EditPriceForm()
    if form.validate_on_submit():
        noofdays = form.promotion_expire.data
        promotion_expiry_date = datetime.now() + timedelta(days=noofdays)
        expire_on = promotion_expiry_date.strftime("%Y-%m-%d")
        product.promotion_expire  = expire_on
        product.price = form.price.data
        product.promotion = form.promotion.data
        shipping_fee = form.shipping_fee.data
        db.session.commit()
        return redirect (url_for('edit_product', name = product.productcode))
    elif request.method == 'GET' and product.owner_id == current_user.id:
        in_cart = CartItems.query.filter(CartItems.product == name).first()
        if in_cart:
            return redirect (url_for('edit_product', name = product.productcode))
        else:
            form.price.data = product.price
            form.shipping_fee.data = product.shipping_fee
            form.promotion.data = product.promotion
            return render_template("updateprice.html", form=form, time=time, product=product, bucket=app.config['BUCKET'])
    else:
        return redirect (url_for('merchant', name=current_user.username))

@app.route('/merchant/product/stock/<name>', methods=['GET', 'POST'])
@login_required
def update_stock(name):
    product = Products.query.filter_by(productcode=name).first()
    form = EditStockForm(quantity = product.quantity)
    if form.validate_on_submit():
        product.quantity = form.quantity.data
        db.session.commit()
        return redirect (url_for('edit_product', name = product.productcode))
    elif request.method == 'GET' and product.owner_id == current_user.id:
        in_cart = CartItems.query.filter(CartItems.product == name).first()
        if in_cart:
            return redirect (url_for('edit_product', name = product.productcode))
        else:

            return render_template("updatestock.html", form=form, product=product, bucket=app.config['BUCKET'])
    else:
        return redirect (url_for('merchant', name=current_user.username))

@app.route('/merchant/product/edit/delete/<name>', methods=['GET', 'POST'])
@login_required
def edit_delete_product(name):
    product = Products.query.filter_by(productcode=name).first()
    if request.method == 'POST' and current_user.id == product.owner_id:
        try:
            delete_blob(product.imgfile1)
            db.session.delete(product)
            db.session.commit()
        except:
            db.session.delete(product)
            db.session.commit()
        return redirect (url_for('merchant', name=current_user.username))
    elif current_user.id == product.owner_id:
        in_cart = CartItems.query.filter(CartItems.product == product.productcode).first()
        if not in_cart:
            return render_template("deleteproduct.html", product=product, bucket= app.config['BUCKET'])
        else:
            return redirect(url_for("edit_product", name=product.productcode))
    else:
        return redirect(url_for("merchant", name = current_user.username))


@app.route('/merchant/order/<c_id>/<p_id>', methods=['GET', 'POST'])
@login_required
def order(c_id,p_id):
    product = CartItems.query.join(Cart,(Cart.reference_id==c_id)).filter(CartItems.id == p_id).first()
    if current_user.is_authenticated:
        if current_user.username == product.seller:
            return render_template("order.html", item=product)
        elif current_user.role == 'Seller':
            return redirect(url_for("merchant", name = current_user.username))
        else:
            return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))



@app.route('/terms')
def terms():
    return render_template("terms.html", title="Terms of use & Privacy policy")


@app.route('/resetpassword')
def password_email_reset():
    return render_template("resetpassword.html")



# Articles page
@app.route('/articles')
def articles():
    return render_template("articles.html")

#Add Article by admin
@app.route('/articles/add/', methods=['GET', 'POST'])
@login_required
def addarticles():
    form = ArticlesForm()
    if form.validate_on_submit():
        try:
            return redirect(url_for('admin'))
        except:
            return redirect(url_for('admin'))
    elif current_user.role == 'admin':
        return render_template("addarticles.html", form=form)
    else:
        return render_template("articles.html")

@app.route('/admin')
@login_required
def admin():
    if current_user.role == 'admin':
        return render_template("admin.html")
    else:
        return redirect(url_for('home'))

@app.route('/admin/user_verify' , methods=['GET', 'POST'])
def user_verify():
    if request.method=='POST':
        if 'confirm_user' in request.form:
            confirm_user = request.form.get('confirm_user')
            user = User.query.get(confirm_user)
            user.verified = 'y'
            db.session.commit()
        return redirect(url_for('user_verify'))
    elif current_user.is_anonymous:
        return redirect(url_for('home'))
    elif current_user.role == 'admin':
        pending_user = User.query.filter(User.role=='Seller',User.verified=='no').order_by(User.date_register.desc()).all()
        return render_template("verifyuser.html", pending_user=pending_user)
    else:
        return redirect(url_for('home'))

@app.route('/admin/payment_verify')
def payment_verify():
    order = Cart.query.filter_by(payment = 'W').all()
    return render_template("verifypayment.html", order = order)


@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('home')), 404
