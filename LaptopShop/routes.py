import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from LaptopShop import app, db, bcrypt, mail
from LaptopShop.forms import RegistrationForm, LoginForm, UpdateProfileForm, LaptopForm, PurchaseForm, SellForm, \
    ResetPasswordForm, RequestResetForm
from LaptopShop.models import User, Laptop
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message


@app.route('/laptop_shop', methods=['GET', 'POST'])
@login_required
def LaptopShop():
    purchase_form = PurchaseForm()
    sell_form = SellForm()

    if request.method == "POST":
        # purchasing a laptop
        chosen_laptop = request.form.get('chosen_laptop')
        get_chosen_laptop = Laptop.query.filter_by(name=chosen_laptop).first()
        if get_chosen_laptop:
            if current_user.can_purchase(get_chosen_laptop):
                get_chosen_laptop.buy(current_user)
                flash(f"Congratulations! You purchased {get_chosen_laptop.name} for"
                      f" {get_chosen_laptop.price}$", category='success')
            else:
                flash(f"Unfortunately, you don't have enough money to purchase "
                      f"{get_chosen_laptop.name}!", category='danger')
        # returning a laptop back to its seller
        returned_laptop = request.form.get('returned_laptop')
        get_returned_laptop = Laptop.query.filter_by(name=returned_laptop).first()
        if get_returned_laptop:
            if current_user.can_sell(get_returned_laptop):
                get_returned_laptop.return_(current_user)
                flash(f"Congratulations! You returned {get_returned_laptop.name} "
                      f"back to its seller!", category='success')
            else:
                flash(f"Something went wrong with selling {get_returned_laptop.name}", category='danger')

        return redirect(url_for('laptop_shop'))

    elif request.method == "GET":
        not_owned_laptops = Laptop.query.filter_by(owner=None)
        owned_laptops = Laptop.query.filter_by(owner=current_user.id)
        return render_template('laptop_shop.html', owned_laptops=owned_laptops, not_owned_laptops=not_owned_laptops,
                               purchase_form=purchase_form, sell_form=sell_form, title='Laptop Shop')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('LoginShop'))
    flash('You are already logged in')

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, email=form.email.data,
                        password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        login_user(new_user)
        return redirect(url_for('LoginShop'))

    if form.errors != {}:
        flash(f'There was an error while creating a user: '
              f'{[error for error in form.errors.values()]}', category='danger')
    return render_template('register.html', form=form, title='Register Page')


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('LoginShop'))
    flash('You are already logged in')
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        password = bcrypt.check_password_hash(user.password, form.password.data)
        if user and password:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('LoginShop'))
        else:
            flash('Login unsuccessful.', 'danger')
    return render_template('login.html', form=form, title='Login Page')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for('LoginShop'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    img = Image.open(form_picture)
    if img.height > 800 or img.width > 650:
        img.thumbnail((800, 650))
        img.save(picture_path)

    return picture_fn


@app.route("/profile/<user_id>/update", methods=['GET', 'POST'])
@login_required
def profile(user_id):
    profile = User.query.get_or_404(user_id)
    form = UpdateProfileForm()

    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Updated successfully!', 'success')
        return redirect(url_for('LoginShop'))

    elif request.method == 'GET':
        form.username.data = profile.username
        form.email.data = profile.email

    page = request.args.get('page', 1, type=int)
    owned_laptops = Laptop.query.filter_by(owner=profile.id). \
        order_by(Laptop.date_added.desc()). \
        paginate(page=page, per_page=5)

    image_file = url_for('static', filename='profile_pics/'
                                            + profile.image_file)

    return render_template('profile.html', form=form, profile=profile,
                           owned_laptops=owned_laptops, image_file=image_file,
                           title='Profile')


@app.route("/laptop/add", methods=['GET', 'POST'])
@login_required
def add_laptop():
    form = LaptopForm()
    if form.validate_on_submit():
        new_laptop = Laptop(name=form.name.data, price=form.price.data,
                            owner=current_user)
        db.session.add(new_laptop)
        db.session.commit()
        flash('Added successfully!', 'success')
        return redirect(url_for('LoginShop'))
    return render_template('add_laptop.html', form=form)


@app.route("/laptop/<int:laptop_id>/update", methods=['GET', 'POST'])
@login_required
def update_laptop(laptop_id):
    laptop = Laptop.query.get_or_404(laptop_id)
    if laptop.owner != current_user:
        abort(403)

    form = LaptopForm()
    if form.validate_on_submit():
        laptop.name = form.name.data
        laptop.price = form.price.data
        laptop.description = form.description.data
        db.session.commit()
        flash('Laptop has been updated!', 'success')
        return redirect(url_for('LoginShop'))

    elif request.method=="GET":
        form.name.data=laptop.name
        form.price.data = laptop.price
        form.description.data = laptop.description

    return render_template('update_laptop.html', form=form)


@app.route("/laptop/<int:laptop_id>/delete", methods=['POST'])
@login_required
def delete_laptop(laptop_id):
    laptop = Laptop.query.get_or_404(laptop_id)
    if laptop.owner != current_user:
        abort(403)
    db.session.delete(laptop)
    db.session.commit()
    flash('deleted successful!', 'success')
    return redirect(url_for('LoginShop'))


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
              {url_for('reset_token', token=token, _external=True)}
              If you did not make this request then simply ignore this 
              email and no changes will be made.
                '''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('LaptopShop'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('LaptopShop'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', form=form)


@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 400


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


