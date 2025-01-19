from flask import Flask, render_template, redirect, url_for, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_BINDS'] = {
    'stock': 'sqlite:///stock.db'
}
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)

class StockItem(db.Model):
    __bind_key__ = 'stock'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(150), nullable=False)
    producer = db.Column(db.String(150), nullable=False)
    use_case = db.Column(db.String(150), nullable=False)
    isle = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(50), nullable=False)
    shelf = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(150), nullable=False)
    ncs_colorcode = db.Column(db.String(50), nullable=False)
    shine = db.Column(db.String(50), nullable=False)
    expiry_date = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Integer, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/update_item', methods=['POST'])
@login_required
def update_item():
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        field = request.form.get('field')
        value = request.form.get('value')

        item = StockItem.query.get_or_404(item_id)
        setattr(item, field, value)
        db.session.commit()
        return 'success', 200
    return 'error', 400

@app.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = StockItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('delete_users'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.role not in ["Admin", "Chief"]:
        abort(403)
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')

        if password != confirm_password:
            return render_template('register.html', name=name, email=email, role=role)

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template('register.html', name=name, email=email, role=role)

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(name=name, email=email, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/delete_users', methods=['GET', 'POST'])
@login_required
def delete_users():
    if current_user.role not in ["Admin", "Chief"]:
        abort(403)
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        role = request.form.get('role')
        users = User.query.filter(User.name.like(f"%{name}%"), User.email.like(f"%{email}%"), User.role.like(f"%{role}%")).all()
    else:
        users = User.query.all()
    return render_template('delete_user.html', users=users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            if user.role in ['Admin', 'Chief']:
                return redirect(url_for('dashboard'))
            elif user.role in ['User', 'HR']:
                return redirect(url_for('dashboard_user'))
        else:
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if current_user.role not in ['Admin', 'Chief']:
        return redirect(url_for('dashboard_user'))

    if request.method == 'POST':
        description = request.form.get('description')
        producer = request.form.get('producer')
        use_case = request.form.get('use_case')
        isle = request.form.get('isle')
        section = request.form.get('section')
        shelf = request.form.get('shelf')
        content = request.form.get('content')
        ncs_colorcode = request.form.get('ncs_colorcode')
        shine = request.form.get('shine')
        expiry_date = request.form.get('expiry_date')
        amount = request.form.get('amount')

        new_item = StockItem(
            description=description, producer=producer, use_case=use_case, 
            isle=isle, section=section, shelf=shelf, content=content, 
            ncs_colorcode=ncs_colorcode, shine=shine, expiry_date=expiry_date, 
            amount=amount
        )
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    stock_items = StockItem.query.all()
    return render_template('dashboard.html', name=current_user.name, role=current_user.role, stock_items=stock_items)

@app.route('/dashboard-user')
@login_required
def dashboard_user():
    if current_user.role not in ['User', 'HR']:
        return redirect(url_for('dashboard'))
    
    stock_items = StockItem.query.all()
    return render_template('dashboard-user.html', name=current_user.name, role=current_user.role, stock_items=stock_items)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    if not os.path.exists('users.db'):
        db.create_all()
    if not os.path.exists('stock.db'):
        with app.app_context():
            db.create_all(bind='stock')
    app.run(debug=True)
