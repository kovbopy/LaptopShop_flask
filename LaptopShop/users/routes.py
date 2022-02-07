from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from LaptopShop import db, bcrypt
from LaptopShop.models import User
from LaptopShop.users.forms import RegistrationForm, LoginForm, UpdateProfileForm, RequestResetForm, ResetPasswordForm
from LaptopShop.users.utils import save_picture, send_reset_email
from LaptopShop.models import Laptop

users = Blueprint('users', __name__)


@users.route("/register", methods=['GET', 'POST'])
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


@users.route("/login", methods=['GET', 'POST'])
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


@users.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for('LoginShop'))


@users.route("/profile/<user_id>/update", methods=['GET', 'POST'])
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


@users.route("/reset_password", methods=['GET', 'POST'])
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


@users.route("/reset_password/<token>", methods=['GET', 'POST'])
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