<<<<<<< HEAD
from sqlalchemy.orm import declarative_base

Base = declarative_base()
=======
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy models."""
    pass
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
