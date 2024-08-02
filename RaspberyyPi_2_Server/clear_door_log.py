from flask import Flask
from extensions import db
from models import DoorLog

# Create a Flask application context
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Update this with your actual database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app context
db.init_app(app)

with app.app_context():
    # Delete all entries in the DoorLog table
    try:
        table_name = "DoorbellLog"
        num_deleted = db.session.query(DoorLog).delete()
        db.session.commit()
        print(f"Deleted {num_deleted} entries from the {table_name} table.")
    except Exception as e:
        db.session.rollback()
        print(f"An error occurred: {e}")
