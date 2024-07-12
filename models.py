import os
from base64 import urlsafe_b64encode, urlsafe_b64decode

from cryptography.exceptions import InvalidKey
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    nfc_tag = db.Column(db.String(150), unique=True, nullable=True)

    def set_password(self, password):
        salt = os.urandom(16)
        kdf = Scrypt(
            salt=salt,
            length=32,
            n=2 ** 14,
            r=8,
            p=1,
            backend=default_backend()
        )
        key = kdf.derive(password.encode('utf-8'))
        self.password_hash = f'{urlsafe_b64encode(salt).decode("utf-8")}:{urlsafe_b64encode(key).decode("utf-8")}'

    def check_password(self, password):
        try:
            salt, key = self.password_hash.split(':')
            salt = urlsafe_b64decode(salt.encode('utf-8'))
            key = urlsafe_b64decode(key.encode('utf-8'))
            kdf = Scrypt(
                salt=salt,
                length=32,
                n=2 ** 14,
                r=8,
                p=1,
                backend=default_backend()
            )
            kdf.verify(password.encode('utf-8'), key)
            return True
        except Exception as e:
            print(f"Password verification error: {e}")
            return False


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    action = db.Column(db.String(150), nullable=False)
    method = db.Column(db.String(50), nullable=False)
