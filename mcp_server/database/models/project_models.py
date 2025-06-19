from sqlalchemy import Column, Integer, String, Text, DateTime, func, Index
from sqlalchemy.orm import relationship
from ..database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alias = Column(String(255), nullable=False, unique=True, index=True)
    root_path = Column(Text, nullable=False, unique=True, index=True) # Absolute path to the project's root
    description = Column(Text, nullable=True)

    created_at_db = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at_db = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to CodeFile (one-to-many)
    # 'lazy="dynamic"' allows for further querying on the relationship
    code_files = relationship("CodeFile", back_populates="project", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, alias='{self.alias}', root_path='{self.root_path}')>"
