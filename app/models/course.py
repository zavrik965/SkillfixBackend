from app.extensions import db
from dataclasses import dataclass

@dataclass
class Course(db.Model):
    id: int
    name: str
    author: str
    authorinfo: str
    expertphoto: str
    previewphoto: str
    previewvideo: str
    lessons: str
    category: int
    description: str
    duration: str

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    author = db.Column(db.Text)
    authorinfo = db.Column(db.Text)
    expertphoto = db.Column(db.Text)
    previewphoto = db.Column(db.Text)
    previewvideo = db.Column(db.Text)
    lessons = db.Column(db.Text)
    category = db.Column(db.Integer)
    description = db.Column(db.Text)
    duration = db.Column(db.Text)

    def __repr__(self):
        return f'<Course "{self.name}">'
