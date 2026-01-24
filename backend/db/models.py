from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.session import Base
import datetime
from models.mcp_connection import MCPConnection

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sessions = relationship("ChatSession", back_populates="project")

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    db_id = Column(String, nullable=False)
    title = Column(String, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    query = Column(Text, nullable=True)
    chart_config = Column(JSON, nullable=True)
    results = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ChatSession", back_populates="messages")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    username = Column(String, nullable=False)
    db_id = Column(String, nullable=False)
    natural_query = Column(Text, nullable=True)
    generated_query = Column(Text, nullable=True)
    executed = Column(Boolean, default=False)
    success = Column(Boolean, default=False)
    error = Column(Text, nullable=True)
    rows_returned = Column(Integer, nullable=True)

class SavedQuery(Base):
    __tablename__ = "saved_queries"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    db_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    natural_language_query = Column(Text, nullable=True)
    raw_query = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
