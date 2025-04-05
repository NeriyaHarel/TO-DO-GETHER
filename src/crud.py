from src.models.app_uesr import FamilyMember
from src.models.setting import Setting
from src.models.task import Task


def add_member(db_session, name: str, email: str) -> FamilyMember:
    """Add a new family member to the database."""
    if not name:
        raise ValueError("Name is required")
    member = FamilyMember(name=name, email=email)
    db_session.add(member)
    return member


def add_task(db_session, title, room, points, member_id):
    """Add a new task to the database."""
    if not title or not room:
        raise ValueError("Title and room are required")
    task = Task(title=title, room=room, points=points, family_member_id=member_id)
    db_session.add(task)
    return task


def get_task(db_session, task_id) -> Task:
    """Get a task by its ID."""
    task = db_session.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise ValueError("Task not found")
    return task


def get_family_member(db_session, family_member_id) -> FamilyMember:
    """Get a family member by their ID."""
    member = db_session.query(FamilyMember).filter(
        FamilyMember.id == family_member_id).first()
    if not member:
        raise ValueError("Family member not found")
    return member


def set_setting(db_session, key: str, value: str):
    """Set a setting in the database."""
    setting = db_session.query(Setting).filter(Setting.key == key).first()
    if not setting:
        setting = Setting(key=key, value=value)
        db_session.add(setting)
    else:
        setting.value = value
    db_session.commit()


def get_setting(db_session, key: str, default=None) -> str:
    """Get a setting from the database."""
    setting = db_session.query(Setting).filter(Setting.key == key).first()
    if not setting:
        return default
    return setting.value
