from enum import Enum
from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator


# Enums ------------------------------------------------------------------------
class SubscriptionType(str, Enum):
    FREE = "free"
    PREMIUM = "premium"


class SkillType(str, Enum):
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    DATABASE = "database"
    PROTOTYPING = "prototyping"
    AGILE = "agile"
    REQUIREMENTS = "requirements"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEVOPS = "devops"


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    TERMINATED = "terminated"


class TaskStatus(str, Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class ProjectRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"


# Models -----------------------------------------------------------------------
class User(models.Model):
    id = fields.BigIntField(pk=True)
    username = fields.CharField(max_length=100, null=True)
    first_name = fields.CharField(max_length=100)
    subscription_type = fields.CharEnumField(SubscriptionType, default=SubscriptionType.FREE)
    created_at = fields.DatetimeField(auto_now_add=True)

    projects = fields.ManyToManyField("models.Project", through="project_user", related_name="members")
    skills = fields.ManyToManyField("models.Skill", through="user_skill")

    class Meta:
        table = "user"


class Skill(models.Model):
    id = fields.IntField(pk=True)
    type = fields.CharEnumField(SkillType)
    name = fields.CharField(max_length=100, unique=True)

    class Meta:
        table = "skill"


class Project(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    description = fields.TextField()
    status = fields.CharEnumField(ProjectStatus, default=ProjectStatus.ACTIVE)
    telegram_chat_id = fields.CharField(max_length=50)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "project"


class ProjectUser(models.Model):
    project = fields.ForeignKeyField("models.Project", related_name="project_users")
    user = fields.ForeignKeyField("models.User", related_name="user_projects")
    role = fields.CharEnumField(ProjectRole, default=ProjectRole.MEMBER)  # Integrated system roles

    class Meta:
        table = "project_user"
        #unique_together = (("project", "role"),)  # A single admin per project


class Task(models.Model):
    id = fields.IntField(pk=True)
    custom_id = fields.CharField(max_length=50, null=True)
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    status = fields.CharEnumField(TaskStatus, default=TaskStatus.ASSIGNED)
    deadline = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    project = fields.ForeignKeyField("models.Project", related_name="tasks")
    assigned_user = fields.ForeignKeyField("models.User", null=True, related_name="tasks")

    class Meta:
        table = "task"


class UserSkill(models.Model):
    user = fields.ForeignKeyField("models.User", related_name="user_skills")
    skill = fields.ForeignKeyField("models.Skill", related_name="skill_users")
    value = fields.CharField(max_length=50)

    class Meta:
        table = "user_skill"



# Pydantic models for validation and serialization
User_Pydantic = pydantic_model_creator(User, name="User")
UserCreate_Pydantic = pydantic_model_creator(User, name="UserCreate", exclude_readonly=True)

Skill_Pydantic = pydantic_model_creator(Skill, name="Skill")
SkillCreate_Pydantic = pydantic_model_creator(Skill, name="SkillCreate", exclude_readonly=True)

UserSkill_Pydantic = pydantic_model_creator(UserSkill, name="UserSkill")
UserSkillCreate_Pydantic = pydantic_model_creator(UserSkill, name="UserSkillCreate", exclude_readonly=True)

Project_Pydantic = pydantic_model_creator(Project, name="Project")
ProjectCreate_Pydantic = pydantic_model_creator(Project, name="ProjectCreate", exclude_readonly=True)

ProjectUser_Pydantic = pydantic_model_creator(ProjectUser, name="ProjectUser")
ProjectUserCreate_Pydantic = pydantic_model_creator(ProjectUser, name="ProjectUserCreate", exclude_readonly=True)

Task_Pydantic = pydantic_model_creator(Task, name="Task")
TaskCreate_Pydantic = pydantic_model_creator(Task, name="TaskCreate", exclude_readonly=True)