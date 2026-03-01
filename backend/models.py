"""
HealthLoom ORM Models
SQLAlchemy models for database tables
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, Date, DateTime, Text,
    ForeignKey, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from database import Base


class User(Base):
    """User profile and health information"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Basic Info
    name = Column(String(100))
    email = Column(String(255), unique=True)
    
    # Demographics
    age = Column(Integer, CheckConstraint('age > 0 AND age < 150'))
    gender = Column(String(20))
    
    # Health Profile
    limitations_json = Column(JSONB, default=list, server_default='[]')
    conditions_json = Column(JSONB, default=list, server_default='[]')
    profile_data = Column(JSONB, default=dict, server_default='{}')
    
    # Preferences
    language_preference = Column(String(10), default="en")
    
    # Metadata (for future vector store integration)
    embedding_updated_at = Column(DateTime(timezone=True))
    
    # Relationships
    test_results = relationship("TestResult", back_populates="user", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="user", cascade="all, delete-orphan")
    session_states = relationship("SessionState", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class TestResult(Base):
    """Medical test results with AI analysis"""
    __tablename__ = "test_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Test Identification
    test_name = Column(String(255), nullable=False)
    test_type_normalized = Column(String(255))
    category = Column(String(100))
    
    # Test Values
    value = Column(String(500))  # Increased from 100 to handle longer values
    unit = Column(String(50))
    reference_range = Column(String(500))  # Increased from 100 to handle longer ranges
    is_abnormal = Column(Boolean, default=False)
    
    # Dates
    test_date = Column(Date)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Source Information
    source_file_path = Column(Text)
    source_file_type = Column(String(50))
    file_hash = Column(String(64), index=True)  # SHA-256 hash for duplicate detection
    
    # AI Analysis
    ai_analysis = Column(JSONB, default=dict, server_default='{}')
    extracted_data = Column(JSONB, default=dict, server_default='{}')
    
    # Additional Data
    extra_data = Column(JSONB, default=dict, server_default='{}')
    
    # Relationships
    user = relationship("User", back_populates="test_results")
    
    # Indexes
    __table_args__ = (
        Index('idx_test_results_user_date', 'user_id', 'test_date'),
        Index('idx_test_results_category', 'category'),
        Index('idx_test_results_normalized', 'test_type_normalized'),
    )


class Medication(Base):
    """User medications with conflict detection"""
    __tablename__ = "medications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Medication Details
    brand_name = Column(String(255), nullable=False)
    active_molecule = Column(String(255))
    dosage = Column(String(100))
    frequency = Column(String(100))
    
    # Timeline
    start_date = Column(Date)
    end_date = Column(Date)
    is_active = Column(Boolean, default=True)
    
    # Conflict Detection
    conflict_data = Column(JSONB, default=dict, server_default='{}')
    interactions = Column(JSONB, default=list, server_default='[]')
    
    # Notes
    notes = Column(Text)
    
    # Additional Data
    extra_data = Column(JSONB, default=dict, server_default='{}')
    
    # Relationships
    user = relationship("User", back_populates="medications")
    
    # Indexes
    __table_args__ = (
        Index('idx_medications_user', 'user_id', 'is_active'),
        Index('idx_medications_molecule', 'active_molecule'),
    )


class SessionState(Base):
    """Conversation session state for continuity"""
    __tablename__ = "session_states"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Session Data
    session_json = Column(JSONB, nullable=False, default=dict, server_default='{}')
    
    # Session Metadata
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="session_states")
    conversations = relationship("Conversation", back_populates="session")


class Conversation(Base):
    """Chat messages for memory and context"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("session_states.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Message Content
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    
    # Context Used (what health data was referenced)
    context_used = Column(JSONB, default=dict, server_default='{}')
    
    # Additional Data
    token_count = Column(Integer)
    extra_data = Column(JSONB, default=dict, server_default='{}')
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    session = relationship("SessionState", back_populates="conversations")
    
    # Indexes
    __table_args__ = (
        Index('idx_conversations_user', 'user_id', 'created_at'),
        Index('idx_conversations_session', 'session_id', 'created_at'),
    )


class TestCategory(Base):
    """Predefined categories for test organization"""
    __tablename__ = "test_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    icon_name = Column(String(50))
    color_code = Column(String(7))
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class HealthInsightCache(Base):
    """Cache for AI-generated health insights to reduce API calls"""
    __tablename__ = "health_insight_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # The cached AI response
    insights_json = Column(JSONB, nullable=False)
    
    # Metadata for cache validity
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="insight_cache")


class UserPreferences(Base):
    """User health preferences and questionnaire responses"""
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Questionnaire responses
    health_goals = Column(JSONB, default=list, server_default='[]')  # e.g., ["lose_weight", "build_muscle"]
    dietary_restrictions = Column(JSONB, default=list, server_default='[]')  # e.g., ["vegetarian", "gluten_free"]
    exercise_frequency = Column(String(50))  # e.g., "daily", "weekly", "rarely", "never"
    activity_level = Column(String(50))  # e.g., "sedentary", "moderate", "active", "very_active"
    health_concerns = Column(JSONB, default=list, server_default='[]')  # e.g., ["heart_health", "diabetes"]
    allergies = Column(JSONB, default=list, server_default='[]')  # e.g., ["peanuts", "penicillin"]
    sleep_hours = Column(Integer)  # average hours per night
    stress_level = Column(String(20))  # e.g., "low", "moderate", "high"
    
    # Additional health information
    smoking_status = Column(String(20))  # e.g., "never", "former", "current"
    alcohol_consumption = Column(String(50))  # e.g., "never", "occasional", "regular"
    
    # Onboarding tracking
    questionnaire_completed = Column(Boolean, default=False)
    questionnaire_completed_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")


# Update User relationship
User.insight_cache = relationship("HealthInsightCache", back_populates="user", uselist=False, cascade="all, delete-orphan")
User.preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
