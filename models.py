from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Rabattkod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    butik = db.Column(db.String(100))
    kod = db.Column(db.String(50))
    beskrivning = db.Column(db.String(255))
    url = db.Column(db.String(255))
    kategori = db.Column(db.String(50))
    utgår = db.Column(db.String(50))

def init_db():
    db.drop_all()
    db.create_all()
