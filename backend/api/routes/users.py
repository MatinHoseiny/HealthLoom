"""
HealthLoom Users API Routes
User profile management endpoints
"""

import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import User, UserPreferences
from schemas import UserCreate, UserUpdate, UserResponse, APIResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user profile
    """
    logger.info("Creating new user")
    
    try:
        # Create user
        new_user = User(
            age=user_data.age,
            gender=user_data.gender,
            limitations_json=user_data.limitations_json,
            conditions_json=user_data.conditions_json,
            language_preference=user_data.language_preference
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"✅ User created: {new_user.id}")
        return new_user
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get user profile by ID
    """
    logger.info(f"Fetching user: {user_id}")
    
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update user profile
    """
    logger.info(f"Updating user: {user_id}")
    
    try:
        # Fetch user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        # Update fields
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"✅ User updated: {user_id}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/{user_id}", response_model=APIResponse)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user profile (and all associated data due to CASCADE)
    """
    logger.info(f"Deleting user: {user_id}")
    
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        await db.delete(user)
        await db.commit()
        
        logger.info(f"✅ User deleted: {user_id}")
        return APIResponse(
            success=True,
            message=f"User {user_id} deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.get("/{user_id}/preferences")
async def get_user_preferences(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get user preferences and questionnaire responses
    Returns empty defaults if not yet set
    """
    logger.info(f"Fetching preferences for user: {user_id}")
    
    try:
        # Check if user exists
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        # Get or create preferences
        pref_result = await db.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        preferences = pref_result.scalar_one_or_none()
        
        if not preferences:
            # Return empty defaults
            return {
                "user_id": str(user_id),
                "health_goals": [],
                "dietary_restrictions": [],
                "exercise_frequency": None,
                "activity_level": None,
                "health_concerns": [],
                "allergies": [],
                "sleep_hours": None,
                "stress_level": None,
                "smoking_status": None,
                "alcohol_consumption": None,
                "questionnaire_completed": False
            }
        
        # Return existing preferences
        return {
            "user_id": str(user_id),
            "health_goals": preferences.health_goals or [],
            "dietary_restrictions": preferences.dietary_restrictions or [],
            "exercise_frequency": preferences.exercise_frequency,
            "activity_level": preferences.activity_level,
            "health_concerns": preferences.health_concerns or [],
            "allergies": preferences.allergies or [],
            "sleep_hours": preferences.sleep_hours,
            "stress_level": preferences.stress_level,
            "smoking_status": preferences.smoking_status,
            "alcohol_consumption": preferences.alcohol_consumption,
            "questionnaire_completed": preferences.questionnaire_completed or False,
            "updated_at": preferences.updated_at.isoformat() if preferences.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch preferences: {str(e)}"
        )


@router.put("/{user_id}/preferences")
async def update_user_preferences(
    user_id: UUID,
    preferences_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Update user preferences and questionnaire responses
    Creates preferences record if it doesn't exist
    """
    logger.info(f"Updating preferences for user: {user_id}")
    
    try:
        # Check if user exists
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        # Get or create preferences
        pref_result = await db.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        preferences = pref_result.scalar_one_or_none()
        
        if not preferences:
            # Create new preferences
            preferences = UserPreferences(user_id=user_id)
            db.add(preferences)
        
        # Update fields from request
        if "health_goals" in preferences_data:
            preferences.health_goals = preferences_data["health_goals"]
        if "dietary_restrictions" in preferences_data:
            preferences.dietary_restrictions = preferences_data["dietary_restrictions"]
        if "exercise_frequency" in preferences_data:
            preferences.exercise_frequency = preferences_data["exercise_frequency"]
        if "activity_level" in preferences_data:
            preferences.activity_level = preferences_data["activity_level"]
        if "health_concerns" in preferences_data:
            preferences.health_concerns = preferences_data["health_concerns"]
        if "allergies" in preferences_data:
            preferences.allergies = preferences_data["allergies"]
        if "sleep_hours" in preferences_data:
            preferences.sleep_hours = preferences_data["sleep_hours"]
        if "stress_level" in preferences_data:
            preferences.stress_level = preferences_data["stress_level"]
        if "smoking_status" in preferences_data:
            preferences.smoking_status = preferences_data["smoking_status"]
        if "alcohol_consumption" in preferences_data:
            preferences.alcohol_consumption = preferences_data["alcohol_consumption"]
        if "questionnaire_completed" in preferences_data:
            preferences.questionnaire_completed = preferences_data["questionnaire_completed"]
            if preferences_data["questionnaire_completed"]:
                from datetime import datetime
                preferences.questionnaire_completed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(preferences)
        
        # Invalidate AI cache when preferences change
        from models import HealthInsightCache
        from sqlalchemy import delete as sql_delete
        await db.execute(
            sql_delete(HealthInsightCache).where(HealthInsightCache.user_id == user_id)
        )
        await db.commit()
        
        logger.info(f"✅ Preferences updated for user: {user_id}")
        
        return {
            "success": True,
            "message": "Preferences updated successfully",
            "data": {
                "user_id": str(user_id),
                "health_goals": preferences.health_goals or [],
                "dietary_restrictions": preferences.dietary_restrictions or [],
                "exercise_frequency": preferences.exercise_frequency,
                "activity_level": preferences.activity_level,
                "health_concerns": preferences.health_concerns or [],
                "allergies": preferences.allergies or [],
                "sleep_hours": preferences.sleep_hours,
                "stress_level": preferences.stress_level,
                "smoking_status": preferences.smoking_status,
                "alcohol_consumption": preferences.alcohol_consumption,
                "questionnaire_completed": preferences.questionnaire_completed or False
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}"
        )

