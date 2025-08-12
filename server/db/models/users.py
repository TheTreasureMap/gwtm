from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from werkzeug.security import generate_password_hash, check_password_hash
from ..database import Base


class Users(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    username = Column(String(25), index=True, unique=True)
    firstname = Column(String(25))
    lastname = Column(String(25))
    password_hash = Column(String(128))
    datecreated = Column(DateTime)
    email = Column(String(100), index=True, unique=True)
    api_token = Column(String(128))
    verification_key = Column(String(128))
    verification_expires = Column(DateTime)
    verified = Column(Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserGroups(Base):
    __tablename__ = "usergroups"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    userid = Column(Integer)
    groupid = Column(Integer)
    role = Column(String(25))


class Groups(Base):
    __tablename__ = "groups"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    name = Column(String(25))
    datecreated = Column(DateTime)


class UserActions(Base):
    __tablename__ = "useractions"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    userid = Column(Integer)
    ipaddress = Column(String(50))
    url = Column(String())
    time = Column(DateTime)
    jsonvals = Column(JSON)
    method = Column(String(24))
