from datetime import datetime
from flask import app
from LaptopShop import db, login_manager
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(30), nullable=False)
    budget=db.Column(db.Integer(),nullable=False,default=0)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    laptops = db.relationship('Laptop', backref='owner')

    def __repr__(self):
        return self.username

    @property
    def pretty_budget(self):# to make it look like $10,500/$10,500,500
        str_budg=str(self.budget)
        if 7>len(str_budg) >= 4:
            return f'${str_budg[:-3]},{str_budg[-3:]}'
        elif len(str_budg) >=7:
            return f"${str_budg[-9:-6]},{str_budg[-6:-3]},{str_budg[-3:]}"
        else:
            return f"${self.budget}"


    def can_purchase(self, laptop):
        return self.budget >= laptop.price

    def can_sell(self, laptop):
        return laptop in self.laptops


    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)


class Laptop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False,unique=True)
    price=db.Column(db.Integer(),nullable=False)
    description = db.Column(db.String(length=1024), nullable=False, unique=True)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    owner = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return self.name

    @property
    def pretty_price(self):
        str_price=str(self.price)
        if 7>len(str_price) >= 4:
            return f'${str_price[:-3]},{str_price[-3:]}'
        elif len(str_price) >=7:
            return f"${str_price[-9:-6]},{str_price[-6:-3]},{str_price[-3:]}"
        else:
            return f"${self.price}"

    past_owners={}
    def buy(self, new_owner):
        # i'll store past laptops' owners
        # to be able to return it to them
        global past_owners
        past_owners.update({self.id:self.owner})

        self.owner = new_owner.id
        new_owner.budget -= self.price
        db.session.commit()

    def return_(self,owner):
        self.owner = past_owners.get(self.id)
        owner.budget += self.price
        db.session.commit()




