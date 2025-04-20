from enum import Enum
from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator

class SubscriptionType(Enum):
    """
    Enum for subscription types
    """
    FREE = "free"
    PREMIUM = "premium"

class User(models.Model):
    id = fields.IntField(pk=True)
    usr_telegram = fields.CharField(max_length=100, unique=True)
    subscription_type = fields.CharEnumField(enum_type=SubscriptionType, max_length=20, default=SubscriptionType.FREE)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "user"


class Skill(models.Model):
    id = fields.IntField(pk=True)

class ProjectStatus(Enum):
    """
    Enum for project status
    """
    ACTIVE = "active"
    TERMINATED = "terminated"

class Project(models.Model):
    """
    Represents a project
    """
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, index=True)
    description = fields.TextField()
    status = fields.CharField(max_length=20, default="active")
    admin = fields.ForeignKeyField(model_name='models.User', related_name='administered_projects')
    telegram_chat_id = fields.CharField(max_length=50)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "project"


"""
class ProjectUser(models.Model):
    
     Represents a m2m relationship between users and projects
    
    id = fields.IntField(pk=True)
    project = fields.ForeignKeyField('models.Project', related_name='members')
    user = fields.ForeignKeyField('models.User', related_name='project_memberships')
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "project_users"
        unique_together = ("project_id", "user_id")
"""

class TaskStaus(Enum):
    """
    Enum for task status
    """
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class Task(models.Model):
    """
    Represents a project's task
    """
    id = fields.IntField(pk=True)
    task_id = fields.CharField(max_length=50, index=True)  # id for users to determine
    name = fields.CharField(max_length=100)
    description = fields.TextField()
    #status = fields.CharField(max_length=20, default="ASSIGNED")
    status = fields.CharEnumField(enum_type=TaskStaus, max_length=20, default=TaskStaus.ASSIGNED)
    project = fields.ForeignKeyField('models.Project', related_name='tasks')
    assigned_user = fields.ForeignKeyField('models.User', related_name='assigned_tasks', null=True)
    deadline = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "task"



# Pydantic models for validation and serialization
User_Pydantic = pydantic_model_creator(User, name="User")
UserCreate_Pydantic = pydantic_model_creator(User, name="UserCreate", exclude_readonly=True)

#UserSkill_Pydantic = pydantic_model_creator(UserSkill, name="UserSkill")
#UserSkillCreate_Pydantic = pydantic_model_creator(UserSkill, name="UserSkillCreate", exclude_readonly=True)

Project_Pydantic = pydantic_model_creator(Project, name="Project")
ProjectCreate_Pydantic = pydantic_model_creator(Project, name="ProjectCreate", exclude_readonly=True)

Task_Pydantic = pydantic_model_creator(Task, name="Task")
TaskCreate_Pydantic = pydantic_model_creator(Task, name="TaskCreate", exclude_readonly=True)