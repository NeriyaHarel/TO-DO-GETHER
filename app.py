from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
from src import crud
from src.models.app_uesr import FamilyMember
from src.models.base import Base
from src.models.setting import Setting
from src.models.task import Task
from src.expenses_balance.splitwise.calculator import CostILS, SplitWiseConfig, Debt, \
    SplitCalc
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "Sachin"
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(model_class=Base,
                app=app)  # Use the custom Base class for SQLAlchemy


def get_expense_calculator(db_session, current_splitwise=None) -> SplitCalc:
    with app.app_context():
        config = SplitWiseConfig.from_env()
        config.group_id = crud.get_setting(
            db_session, 'SPLITWISE_GROUP_ID',
            default=config.group_id
        )
        if current_splitwise and current_splitwise.splitwise_config == config:
            return current_splitwise
        return SplitCalc(config)


def init_settings():
    settings = {
        'SPLITWISE_CONSUMER_KEY': os.environ['SPLITWISE_CONSUMER_KEY'],
        'SPLITWISE_CONSUMER_SECRET': os.environ['SPLITWISE_CONSUMER_SECRET'],
        'SPLITWISE_API_KEY': os.environ['SPLITWISE_API_KEY'],
        'SPLITWISE_GROUP_ID': os.environ['SPLITWISE_GROUP_ID'],
    }
    for key, value in settings.items():
        crud.set_setting(db.session, key, value)
    db.session.commit()


@app.route('/get_users_from_splitwise', methods=['POST'])
def get_users_from_splitwise():
    expense_calculator = get_expense_calculator(db.session)
    for user in expense_calculator.group_users:
        try:
            crud.add_member(db.session, user.first_name, user.email)
        except ValueError:
            continue  # Skip if the user already exists
    db.session.commit()
    return redirect(url_for('settings'))


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        for key, value in request.form.items():
            print(f"Setting {key} to {value}")
            crud.set_setting(db.session, key.upper(), value)
            db.session.commit()
        global global_splitwise
        global_splitwise = get_expense_calculator(db.session, global_splitwise)
        return redirect(url_for('settings'))

    settings = db.session.execute(db.select(Setting)).scalars().all()
    family_members = db.session.execute(db.select(FamilyMember)).scalars().all()
    return render_template('settings.html', settings=settings,
                           family_members=family_members)


@app.route('/')
def index():
    members = db.session.execute(db.select(FamilyMember)).scalars().all()
    tasks = db.session.execute(
        db.select(Task).options(db.joinedload(Task.assignee)).order_by(
            Task.created_at.desc())
    ).scalars().all()
    categories = db.session.execute(db.select(Task.room).distinct()).scalars().all()
    current_balance = get_expense_calculator(db.session).get_balance()
    return render_template('index.html', members=members, tasks=tasks,
                           categories=categories, balance=current_balance)


@app.route('/balance', methods=['GET'])
def balance():
    current_balance = get_expense_calculator(db.session).get_balance()
    return render_template('balance.html', balance=current_balance)


@app.route('/add_member', methods=['POST'])
def add_member():
    name = request.form.get('name')
    email = request.form.get('email')

    try:
        crud.add_member(db.session, name, email)
        db.session.commit()
    except ValueError as e:
        return str(e), 400
    return redirect(url_for('settings'))

@app.route('/delete_member/<int:member_id>', methods=['POST'])
def delete_member(member_id):
    member = crud.get_family_member(db.session, member_id)
    if not member:
        return "Member not found", 404
    db.session.delete(member)
    db.session.commit()
    return redirect(url_for('settings'))

@app.route('/add_task', methods=['POST'])
def add_task():
    title = request.form.get('title')
    room = request.form.get('room')
    points = int(request.form.get('points', 1))
    member_id = request.form.get('member_id')
    if not title or not room:
        return "Title and room are required", 400
    crud.add_task(db.session, title, room, points, member_id)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/complete_task/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    task = crud.get_task(db.session, task_id)
    task.completed = True
    cost = float(request.form.get('cost', 0))
    if not task.family_member_id:
        return "Task has no assigned family member", 400
    family_member = crud.get_family_member(db.session, task.family_member_id)
    if not family_member:
        return "Family member not found", 404
    expense_calculator = get_expense_calculator(db.session)
    family_member.points += task.points
    if cost > 0:
        cost_ils = CostILS.from_shekel(cost)
        try:
            paying_user=expense_calculator.user_from_email(family_member.email)
        except ValueError:
            flash(f"User {family_member.email} not found in Splitwise group, "
                  f"the task '{task.title}' with cost of {cost_ils} will not be added "
                  f"to Splitwise."
                  f" Please add the user to Splitwise group first.")
        else:
            expense_calculator.add_equal_split_expense(
                cost=cost_ils,
                description=task.title,
                paying_user=paying_user,
            )
    task.cost = cost
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    task = crud.get_task(db.session, task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/assign_task/<int:task_id>', methods=['POST'])
def assign_task(task_id):
    member_id = request.form.get('member_id')
    if not member_id:
        return "Member ID is required", 400
    task = crud.get_task(db.session, task_id)
    task.family_member_id = member_id
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_settings()
        global_splitwise: SplitCalc = get_expense_calculator(db.session)
        print(global_splitwise.splitwise_config)

    app.run(debug=True)
