import os
from base64 import urlsafe_b64encode, urlsafe_b64decode
from datetime import datetime
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from flask_login import UserMixin
from extensions import db

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    nfc_tags = db.relationship('NfcTag', backref='user', lazy=True)

    def set_password(self, password):
        salt = os.urandom(16)
        kdf = Scrypt(salt=salt, length=32, n=2 ** 14, r=8, p=1, backend=default_backend())
        key = kdf.derive(password.encode('utf-8'))
        self.password_hash = f'{urlsafe_b64encode(salt).decode("utf-8")}:{urlsafe_b64encode(key).decode("utf-8")}'

    def check_password(self, password):
        try:
            salt, key = self.password_hash.split(':')
            salt = urlsafe_b64decode(salt.encode('utf-8'))
            key = urlsafe_b64decode(key.encode('utf-8'))
            kdf = Scrypt(salt=salt, length=32, n=2 ** 14, r=8, p=1, backend=default_backend())
            kdf.verify(password.encode('utf-8'), key)
            return True
        except Exception as e:
            print(f"Password Verification Error: {e}")
            return False


class NfcTag(db.Model):
    __tablename__ = 'nfc_tag'
    nfc_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))




class DoorLog(db.Model):
    __tablename__ = 'door_log'
    id = db.Column(db.Integer, primary_key=True)
    nfc_id = db.Column(db.Integer, db.ForeignKey('nfc_tag.nfc_id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(150), nullable=False)


class DoorbellLog(db.Model):
    __tablename__ = 'doorbell_log'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    image = db.Column(db.String(256), nullable=False)
