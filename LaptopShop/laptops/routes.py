from flask import render_template, url_for, flash, redirect, request, abort, Blueprint
from LaptopShop import db
from LaptopShop.laptops.forms import PurchaseForm, SellForm, LaptopForm
from LaptopShop.models import Laptop
from flask_login import current_user, login_required

laptops = Blueprint('laptops', __name__)


@laptops.route('/laptop_shop', methods=['GET', 'POST'])
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


@laptops.route("/laptop/add", methods=['GET', 'POST'])
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


@laptops.route("/laptop/<int:laptop_id>/update", methods=['GET', 'POST'])
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


@laptops.route("/laptop/<int:laptop_id>/delete", methods=['POST'])
@login_required
def delete_laptop(laptop_id):
    laptop = Laptop.query.get_or_404(laptop_id)
    if laptop.owner != current_user:
        abort(403)
    db.session.delete(laptop)
    db.session.commit()
    flash('deleted successful!', 'success')
    return redirect(url_for('LoginShop'))
