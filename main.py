from flask import Flask, abort, render_template, flash, redirect, url_for, request
from sqlalchemy import String, Integer, Float
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_required, login_user, logout_user, current_user, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime
from forms import CreateAccount, MakeDeposit, LoginForm, WithdrawalsForm

app = Flask(__name__)
app.config['SECRET_KEY'] = '12mnbj23njk4bbh32'
Bootstrap5(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# def only_user


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    deposit = relationship('Deposit', back_populates='user')
    date: Mapped[str] = mapped_column(String(100), nullable=False)
    total_transection: Mapped[int] = mapped_column(Integer, nullable=False)


class Transection(db.Model):
    __tablename__ = 'transections'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    depositor_id: Mapped[int | None] = mapped_column(Integer, db.ForeignKey('deposits.id'))
    depositor = relationship('Deposit')


class Deposit(db.Model):
    __tablename__ = 'deposits'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    user = relationship('User', back_populates='deposit')
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'))
    date: Mapped[str] = mapped_column(String(100), nullable=False)


with app.app_context():
    db.create_all()


@app.context_processor
def inject_now():
    return {
        'current_year': datetime.now().year
    }


@app.route('/', methods=["GET", "POST"])
def home():
    return render_template('index.html', current_user=current_user)


@app.route('/registration', methods=['GET', 'POST'])
def register():
    form = CreateAccount()
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.name == form.name.data))
        user = result.scalar()

        if user:
            flash('You already have an account, Log in Instead!')
            return redirect(url_for('login'))

        if form.amount.data < 1000.0:
            flash('Amount should be 1000 or above.')
            return redirect(url_for('register'))

        hashed_and_salted = generate_password_hash(
            form.password.data,
            method='scrypt',
            salt_length=8
        )

        new_user = User(
            name=form.name.data,
            email=form.email.data,
            amount=form.amount.data,
            password=hashed_and_salted,
            total_transection=1,
            date=date.today().strftime('%B %d,%Y')
        )
        db.session.add(new_user)
        db.session.commit()

        new_deposit = Deposit(
            name=form.name.data,
            amount=form.amount.data,
            user=new_user,
            date=date.today().strftime('%B %d,%Y')
        )
        db.session.add(new_deposit)
        db.session.commit()

        new_transection = Transection(
            depositor=new_deposit
        )
        db.session.add(new_transection)
        db.session.commit()

        login_user(new_user)

        return redirect(url_for('account', user_id=new_user.id))
    return render_template('register.html', form=form, current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.name == form.name.data))
        user = result.scalar()

        if not user:
            flash("There isn't any user with that name, register instead!")
            return redirect(url_for('register'))

        elif not check_password_hash(user.password, form.password.data):
            flash("Password is wrong try again!")
            return redirect(url_for('login'))

        else:
            login_user(user)
            return redirect(url_for('account', user_id=user.id))
    return render_template('login.html', form=form, current_user=current_user)


@app.route('/user-account/<int:user_id>', methods=["GET", "POST"])
@login_required
def account(user_id):
    # user = db.get_or_404(User,user_id)
    if current_user.id != user_id:
        return abort(403)
    return render_template('user-account.html', current_user=current_user)


@app.route('/withdraw_or_deposit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def withdraw_or_deposit(user_id):
    form = WithdrawalsForm()
    result = db.session.execute(db.select(User).where(User.id == user_id))
    user = result.scalar()
    status = request.args.get('status', type=int)
    # print(type(status))
    if form.validate_on_submit():
        if status == 1:
            user.amount = user.amount + form.amount.data
            db.session.commit()

            new_deposit = Deposit(
                name=user.name,
                amount=form.amount.data,
                user=user,
                date=date.today().strftime('%B %d, %Y')
            )
            db.session.add(new_deposit)
            db.session.commit()

            new_transection = Transection(
                depositor=new_deposit
            )
            db.session.add(new_transection)
            db.session.commit()

            user.total_transection += 1
            db.session.commit()

            return redirect(url_for('account', user_id=user_id))

        elif status == 0:
            withdrawal_amount = form.amount.data
            if withdrawal_amount > user.amount:
                flash("You do not have that much money in your account! ")
                return redirect(url_for('withdraw_or_deposit', user_id=user_id))

            if not check_password_hash(user.password, form.password.data):
                flash('Password is wrong try again!')
                return redirect(url_for('withdraw_or_deposit', user_id=user_id))


            user.amount = user.amount - withdrawal_amount
            db.session.commit()

            new_transection = Transection()
            db.session.add(new_transection)
            db.session.commit()

            user.total_transection += 1
            db.session.commit()

            return redirect(url_for('account', user_id=user_id))

    return render_template('widthdraw.html', form=form)


@app.route('/deposit', methods=["GET", "POST"])
def deposit():
    form = MakeDeposit()
    if form.validate_on_submit():

        result = db.session.execute(db.select(User).where(User.name == form.receiver.data))
        user = result.scalar()
        if not user:
            flash('User with that name is not found.')
            return redirect(url_for('deposit'))

        new_deposit = Deposit(
            name=form.name.data,
            amount=form.amount.data,
            user=user,
            date=date.today().strftime('%B %d,%Y')
        )
        db.session.add(new_deposit)
        db.session.commit()

        new_transection = Transection(
            depositor=new_deposit
        )
        db.session.add(new_transection)
        db.session.commit()

        user.amount = user.amount + form.amount.data
        user.total_transection = user.total_transection + 1
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('deposit.html', form=form, current_user=current_user)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, port=5005)
