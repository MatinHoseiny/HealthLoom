"""
HealthLoom Medications API Routes
Medication management with conflict detection
"""

import logging
from typing import List
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import User, Medication
from schemas import MedicationCreate, MedicationUpdate, MedicationResponse, APIResponse
from agent.graph import run_healthloom_agent

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
async def add_medication(
    medication_data: MedicationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Add new medication with conflict detection
    
    Automatically checks for:
    - Duplicate medications (same active ingredient)
    - Drug-drug interactions
    - Food-drug interactions
    """
    logger.info(f"💊 Adding medication for user {medication_data.user_id}")
    
    try:
        # Validate user
        result = await db.execute(select(User).where(User.id == medication_data.user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {medication_data.user_id} not found"
            )
        
        # Get current active medications
        current_meds_result = await db.execute(
            select(Medication)
            .where(Medication.user_id == medication_data.user_id)
            .where(Medication.is_active == True)
        )
        current_meds = [
            {
                "brand_name": m.brand_name,
                "active_molecule": m.active_molecule,
                "dosage": m.dosage,
                "is_active": m.is_active
            }
            for m in current_meds_result.scalars().all()
        ]
        
        # Run AI agent for conflict detection
        logger.info(f"🤖 Running conflict detection for: {medication_data.brand_name}")
        
        agent_result = await run_healthloom_agent(
            user_id=str(medication_data.user_id),
            input_type="medication_query",
            user_message=medication_data.brand_name,
            user_profile={
                "age": user.age,
                "gender": user.gender
            },
            current_medications=current_meds
        )
        
        if not agent_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Medication analysis failed: {', '.join(agent_result.get('errors', ['Unknown error']))}"
            )
        
        # Extract conflict data
        conflicts = agent_result.get("medication_conflicts", [])
        conflict_data = conflicts[0] if conflicts else {}
        
        # Create medication record
        new_medication = Medication(
            user_id=medication_data.user_id,
            brand_name=conflict_data.get("corrected_brand_name") or medication_data.brand_name,
            active_molecule=conflict_data.get("active_molecule") or medication_data.active_molecule,
            dosage=medication_data.dosage,
            frequency=medication_data.frequency,
            start_date=medication_data.start_date or date.today(),
            end_date=medication_data.end_date,
            notes=medication_data.notes,
            is_active=True,
            conflict_data=conflict_data,
            interactions=conflict_data.get("drug_interactions", []) + conflict_data.get("food_interactions", [])
        )
        
        db.add(new_medication)
        await db.commit()
        await db.refresh(new_medication)
        
        logger.info(f"✅ Medication added: {new_medication.id}")
        
        # Log warnings if conflicts found
        if conflict_data.get("is_duplicate"):
            logger.warning(f"⚠️  Duplicate medication detected: {conflict_data.get('duplicate_of')}")
        
        critical_interactions = [
            i for i in conflict_data.get("drug_interactions", [])
            if i.get("severity") in ["high", "critical"]
        ]
        if critical_interactions:
            logger.warning(f"⚠️  {len(critical_interactions)} critical drug interactions found")
        
        return new_medication
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding medication: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add medication: {str(e)}"
        )


@router.get("/{user_id}", response_model=List[MedicationResponse])
async def get_user_medications(
    user_id: UUID,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all medications for a user
    """
    logger.info(f"Fetching medications for user {user_id}")
    
    try:
        query = select(Medication).where(Medication.user_id == user_id)
        
        if active_only:
            query = query.where(Medication.is_active == True)
        
        result = await db.execute(query.order_by(Medication.created_at.desc()))
        medications = result.scalars().all()
        
        return medications
        
    except Exception as e:
        logger.error(f"Error fetching medications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch medications: {str(e)}"
        )


@router.put("/{medication_id}", response_model=MedicationResponse)
async def update_medication(
    medication_id: UUID,
    medication_data: MedicationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update medication details
    """
    logger.info(f"Updating medication: {medication_id}")
    
    try:
        result = await db.execute(select(Medication).where(Medication.id == medication_id))
        medication = result.scalar_one_or_none()
        
        if not medication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medication {medication_id} not found"
            )
        
        # Update fields
        update_data = medication_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(medication, field, value)
        
        await db.commit()
        await db.refresh(medication)
        
        logger.info(f"✅ Medication updated: {medication_id}")
        return medication
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating medication: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update medication: {str(e)}"
        )


@router.delete("/{medication_id}", response_model=APIResponse)
async def delete_medication(
    medication_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete medication (or mark as inactive)
    """
    logger.info(f"Deleting medication: {medication_id}")
    
    try:
        result = await db.execute(select(Medication).where(Medication.id == medication_id))
        medication = result.scalar_one_or_none()
        
        if not medication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medication {medication_id} not found"
            )
        
        # Mark as inactive instead of deleting (better for history)
        medication.is_active = False
        medication.end_date = date.today()
        
        await db.commit()
        
        logger.info(f"✅ Medication marked inactive: {medication_id}")
        return APIResponse(
            success=True,
            message=f"Medication {medication_id} marked as inactive"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting medication: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete medication: {str(e)}"
        )
