"""
HealthLoom Pydantic Schemas
Request/Response validation models
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID
from enum import Enum


# ==============================================
# ENUMS
# ==============================================

class MessageRole(str, Enum):
    """Chat message roles"""
    USER = "user"
    ASSISTANT = "assistant"


class Gender(str, Enum):
    """User gender options"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


# ==============================================
# USER SCHEMAS
# ==============================================

class UserBase(BaseModel):
    """Base user schema"""
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    age: Optional[int] = Field(None, ge=1, le=150)
    gender: Optional[Gender] = None
    limitations_json: List[str] = Field(default_factory=list)
    conditions_json: List[str] = Field(default_factory=list)
    language_preference: str = Field(default="en")


class UserCreate(UserBase):
    """Schema for creating a new user"""
    pass


class UserUpdate(UserBase):
    """Schema for updating user"""
    pass


class UserResponse(UserBase):
    """Schema for user response"""
    id: UUID
    created_at: datetime
    profile_data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


# ==============================================
# TEST RESULT SCHEMAS
# ==============================================

class TestResultBase(BaseModel):
    """Base test result schema"""
    test_name: str
    test_type_normalized: Optional[str] = None
    category: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    is_abnormal: bool = False
    test_date: Optional[date] = None


class TestResultCreate(TestResultBase):
    """Schema for creating test result"""
    user_id: UUID
    source_file_path: Optional[str] = None
    source_file_type: Optional[str] = None
    ai_analysis: Dict[str, Any] = Field(default_factory=dict)
    extracted_data: Dict[str, Any] = Field(default_factory=dict)


class TestResultResponse(TestResultBase):
    """Schema for test result response"""
    id: UUID
    user_id: UUID
    created_at: datetime
    upload_date: datetime
    source_file_path: Optional[str] = None
    ai_analysis: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class TestResultsGrouped(BaseModel):
    """Grouped test results by category"""
    category: str
    tests: List[TestResultResponse]
    count: int


# ==============================================
# MEDICATION SCHEMAS
# ==============================================

class MedicationBase(BaseModel):
    """Base medication schema"""
    brand_name: str
    active_molecule: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None


class MedicationCreate(MedicationBase):
    """Schema for creating medication"""
    user_id: UUID


class MedicationUpdate(BaseModel):
    """Schema for updating medication"""
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class MedicationResponse(MedicationBase):
    """Schema for medication response"""
    id: UUID
    user_id: UUID
    created_at: datetime
    is_active: bool
    conflict_data: Dict[str, Any] = Field(default_factory=dict)
    interactions: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class MedicationConflictAlert(BaseModel):
    """Medication conflict alert"""
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    affected_medications: List[str]
    recommendation: str


# ==============================================
# CHAT/CONVERSATION SCHEMAS
# ==============================================

class ChatMessage(BaseModel):
    """Single chat message"""
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    """Request for chat endpoint"""
    user_id: UUID
    message: str
    include_context: bool = Field(
        default=True,
        description="Whether to include health context in the response"
    )


class ChatResponse(BaseModel):
    """Response from chat endpoint"""
    message: str
    context_used: Dict[str, Any] = Field(
        default_factory=dict,
        description="Health data referenced in the response"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions"
    )


class ConversationHistory(BaseModel):
    """Conversation history"""
    messages: List[ChatMessage]
    total_count: int


# ==============================================
# FILE UPLOAD SCHEMAS
# ==============================================

class UploadResponse(BaseModel):
    """Response from document upload"""
    success: bool
    message: str
    file_path: Optional[str] = None
    extracted_tests: List[TestResultResponse] = Field(default_factory=list)
    ai_analysis: Dict[str, Any] = Field(default_factory=dict)
    processing_time_seconds: float


class AnalysisResult(BaseModel):
    """AI analysis result from document processing"""
    test_name: str
    value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    test_date: Optional[date] = None
    category: str
    is_abnormal: bool
    interpretation: str
    confidence_score: float = Field(ge=0.0, le=1.0)


# ==============================================
# DASHBOARD SCHEMAS
# ==============================================

class CategorySummary(BaseModel):
    """Summary for a test category"""
    category_name: str
    icon_name: str
    color_code: str
    total_tests: int
    latest_test_date: Optional[date] = None
    abnormal_count: int
    status: str  # 'good', 'warning', 'critical'


class HealthInsight(BaseModel):
    """AI-generated health insight"""
    title: str
    description: str
    priority: str  # 'low', 'medium', 'high'
    action_items: List[str] = Field(default_factory=list)
    related_tests: List[str] = Field(default_factory=list)


class DashboardData(BaseModel):
    """Complete dashboard data"""
    user: UserResponse
    category_summaries: List[CategorySummary]
    recent_tests: List[TestResultResponse]
    active_medications: List[MedicationResponse]
    health_insights: List[HealthInsight]
    medication_alerts: List[MedicationConflictAlert]


# ==============================================
# HEALTH API RESPONSE SCHEMAS
# ==============================================

class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = Field(default_factory=list)


class PaginatedResponse(BaseModel):
    """Paginated response"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==============================================
# TREND/GRAPH SCHEMAS
# ==============================================

class DataPoint(BaseModel):
    """Single data point for graphs"""
    date: date
    value: float
    unit: str
    is_abnormal: bool


class TrendData(BaseModel):
    """Trend data for visualization"""
    test_name: str
    test_type_normalized: str
    data_points: List[DataPoint]
    reference_range_min: Optional[float] = None
    reference_range_max: Optional[float] = None
    trend_direction: str  # 'up', 'down', 'stable'
    trend_interpretation: str
