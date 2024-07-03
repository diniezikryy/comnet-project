from flask import Flask, render_template, redirect, url_for, flash, request
from extensions import db, login_manager
from flask_login import login_user, login_required, logout_user, current_user
from forms import RegistrationForm, LoginForm
from models import User, Log
import controls

app = Flask(__name__)
app.config['SECRET_KEY'] = '695bf18ae30e380398715ff072e684c0d1437958c7e9147a'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db.init_app(app)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, nfc_tag=form.nfc_tag.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ADD CONTROLS FOR PIN
app.add_url_rule('/control_door', 'control_door', view_func=controls.control_door, methods=["POST"])

# DB & Running Flask Web App

def create_app():
    with app.app_context():
        db.create_all()


@app.context_processor
def inject_user():
    return dict(current_user=current_user)


if __name__ == '__main__':
    create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)
