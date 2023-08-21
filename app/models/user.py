from app.extensions import db
from dataclasses import dataclass

@dataclass
class User(db.Model):
    id: int
    name: str
    payment_time: str
    email: str
    password: str
    hashtoken: str
    confirmed: int
    submited: int

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    payment_time = db.Column(db.Text)
    email = db.Column(db.Text)
    password = db.Column(db.Text)
    hashtoken = db.Column(db.Text)
    confirmed = db.Column(db.Integer)
    submited = db.Column(db.Integer)

    def __repr__(self):
        return f'<User "{self.name}">'
