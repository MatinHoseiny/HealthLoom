"""
HealthLoom Health Data API Routes
Test results and health analytics endpoints
"""

import logging
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import get_db
from models import TestResult, User
from schemas import TestResultResponse, TestResultsGrouped, TrendData, DataPoint

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/tests/{user_id}", response_model=List[TestResultResponse])
async def get_user_tests(
    user_id: UUID,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    abnormal_only: bool = False,
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    Get test results for a user with optional filters
    """
    logger.info(f"Fetching tests for user {user_id}")
    
    try:
        query = select(TestResult).where(TestResult.user_id == user_id)
        
        if category:
            query = query.where(TestResult.category == category)
        
        if start_date:
            query = query.where(TestResult.test_date >= start_date)
        
        if end_date:
            query = query.where(TestResult.test_date <= end_date)
        
        if abnormal_only:
            query = query.where(TestResult.is_abnormal == True)
        
        query = query.order_by(TestResult.test_date.desc()).limit(limit)
        
        result = await db.execute(query)
        tests = result.scalars().all()
        
        return tests
        
    except Exception as e:
        logger.error(f"Error fetching tests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tests: {str(e)}"
        )


@router.get("/tests/grouped/{user_id}", response_model=List[TestResultsGrouped])
async def get_tests_grouped_by_category(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get test results grouped by category
    """
    logger.info(f"Fetching grouped tests for user {user_id}")
    
    try:
        result = await db.execute(
            select(TestResult)
            .where(TestResult.user_id == user_id)
            .order_by(TestResult.category, TestResult.test_date.desc())
        )
        all_tests = result.scalars().all()
        
        # Group by category
        grouped = {}
        for test in all_tests:
            category = test.category or "Other"
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(test)
        
        # Format response
        grouped_results = [
            TestResultsGrouped(
                category=category,
                tests=[TestResultResponse.model_validate(t) for t in tests],
                count=len(tests)
            )
            for category, tests in grouped.items()
        ]
        
        return grouped_results
        
    except Exception as e:
        logger.error(f"Error fetching grouped tests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch grouped tests: {str(e)}"
        )


@router.get("/trends/{user_id}/{test_type}", response_model=TrendData)
async def get_test_trend(
    user_id: UUID,
    test_type: str,
    days: int = Query(default=365, le=1825),
    db: AsyncSession = Depends(get_db)
):
    """
    Get trend data for a specific test type over time
    """
    logger.info(f"Fetching trend for {test_type} (user {user_id})")
    
    try:
        start_date = datetime.now().date() - timedelta(days=days)
        
        result = await db.execute(
            select(TestResult)
            .where(TestResult.user_id == user_id)
            .where(TestResult.test_type_normalized == test_type)
            .where(TestResult.test_date >= start_date)
            .order_by(TestResult.test_date.asc())
        )
        tests = result.scalars().all()
        
        if not tests:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for test type: {test_type}"
            )
        
        # Convert to data points
        data_points = []
        for test in tests:
            try:
                value_float = float(test.value) if test.value else None
                if value_float is not None and test.test_date:
                    data_points.append(DataPoint(
                        date=test.test_date,
                        value=value_float,
                        unit=test.unit or "",
                        is_abnormal=test.is_abnormal
                    ))
            except (ValueError, TypeError):
                # Skip non-numeric values
                continue
        
        # Determine trend direction
        if len(data_points) >= 2:
            recent_avg = sum(dp.value for dp in data_points[-3:]) / min(3, len(data_points[-3:]))
            old_avg = sum(dp.value for dp in data_points[:3]) / min(3, len(data_points[:3]))
            
            if recent_avg > old_avg * 1.1:
                trend_direction = "up"
            elif recent_avg < old_avg * 0.9:
                trend_direction = "down"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "stable"
        
        return TrendData(
            test_name=tests[0].test_name,
            test_type_normalized=test_type,
            data_points=data_points,
            trend_direction=trend_direction,
            trend_interpretation=f"Trend is {trend_direction} over the last {days} days"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trend: {str(e)}"
        )


@router.get("/dashboard/{user_id}")
async def get_dashboard_data(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI-powered dashboard data with smart caching
    """
    logger.info(f"Loading AI-enhanced dashboard for user {user_id}")
    
    try:
        from models import Medication, HealthInsightCache, UserPreferences
        from agent.health_analyzer import (
            generate_overall_health_summary,
            analyze_abnormal_result
        )
        
        # 1. Check for existing cache
        cache_query = select(HealthInsightCache).where(HealthInsightCache.user_id == user_id)
        cache_result = await db.execute(cache_query)
        cache_entry = cache_result.scalar_one_or_none()
        
        # 2. Check for latest data updates to validate cache
        # Latest test upload
        latest_test_query = select(func.max(TestResult.upload_date)).where(TestResult.user_id == user_id)
        latest_test_result = await db.execute(latest_test_query)
        latest_test_date = latest_test_result.scalar()
        
        # Latest medication update
        latest_med_query = select(func.max(Medication.updated_at)).where(Medication.user_id == user_id)
        latest_med_result = await db.execute(latest_med_query)
        latest_med_date = latest_med_result.scalar()

        # Latest user profile update (name change, etc.)
        latest_user_query = select(User.updated_at).where(User.id == user_id)
        latest_user_result = await db.execute(latest_user_query)
        latest_user_date = latest_user_result.scalar()

        # Latest preferences update
        latest_pref_query = select(UserPreferences.updated_at).where(UserPreferences.user_id == user_id)
        latest_pref_result = await db.execute(latest_pref_query)
        latest_pref_date = latest_pref_result.scalar()
        
        # Determine last data change
        dates = [d for d in [latest_test_date, latest_med_date, latest_user_date, latest_pref_date] if d]
        last_data_change = max(dates) if dates else None
            
        # 3. Serve from cache if valid
        if cache_entry and last_data_change:
            # If cache is newer than last data change, use it
            # We add a small buffer (e.g. 1 second) to avoid race conditions where they are equal
            if cache_entry.updated_at > last_data_change:
                logger.info("✅ CACHE HIT: Serving dashboard data from cache")
                return cache_entry.insights_json

        logger.info("⚠️ CACHE MISS: Generating new AI analysis...")
        
        # --- START AI GENERATION (Slow Path) ---
        
        # Get user
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        # Get ALL tests
        all_tests_result = await db.execute(
            select(TestResult)
            .where(TestResult.user_id == user_id)
            .order_by(TestResult.test_date.desc())
        )
        all_tests = all_tests_result.scalars().all()
        
        # Get active medications
        meds_result = await db.execute(
            select(Medication)
            .where(Medication.user_id == user_id)
            .where(Medication.is_active == True)
        )
        active_meds = meds_result.scalars().all()
        
        # Prepare data for AI
        user_data = {
            "age": user.age,
            "gender": user.gender,
            "conditions_json": user.conditions_json or [],
            "limitations_json": user.limitations_json or []
        }
        
        test_results_data = [
            {
                "test_name": t.test_name,
                "value": t.value,
                "unit": t.unit,
                "category": t.category,
                "is_abnormal": t.is_abnormal,
                "reference_range": t.reference_range
            }
            for t in all_tests
        ]
        
        medications_data = [
            {
                "brand_name": m.brand_name,
                "active_molecule": m.active_molecule,
                "dosage": m.dosage
            }
            for m in active_meds
        ]
        
        # Generate AI summary
        logger.info("Generating AI health summary...")
        overall_health_summary = await generate_overall_health_summary(
            user_data,
            test_results_data,
            medications_data
        )
        
        # Analyze abnormal results (limit to 3 to avoid API rate limits)
        abnormal_results = []
        abnormal_tests = [t for t in all_tests if t.is_abnormal]
        
        logger.info(f"Found {len(abnormal_tests)} abnormal results, will analyze top 3 unique tests with AI")
        
        # Deduplicate by (test_name, test_date, value) - keep only one instance of identical tests
        # This handles cases where the same file was uploaded multiple times
        seen_tests = {}
        unique_abnormal_tests = []
        for test in abnormal_tests:
            # Create a unique key based on test name, date, and value
            test_key = (test.test_name, test.test_date, test.value)
            if test_key not in seen_tests:
                seen_tests[test_key] = test
                unique_abnormal_tests.append(test)
        
        logger.info(f"After deduplication: {len(unique_abnormal_tests)} unique abnormal tests (removed {len(abnormal_tests) - len(unique_abnormal_tests)} duplicates)")
        
        import asyncio
        for i, test in enumerate(unique_abnormal_tests[:3]):  # Take top 3 UNIQUE tests
            test_data = {
                "test_name": test.test_name,
                "value": test.value,
                "unit": test.unit,
                "reference_range": test.reference_range
            }
            
            analysis = await analyze_abnormal_result(test_data, user_data)
            abnormal_results.append(analysis)
            
            # Add delay between API calls to avoid rate limiting
        if len(all_tests) == 0:
            health_status = "no_data"
        elif len(abnormal_tests) == 0:
            health_status = "good"
        elif len(abnormal_tests) <= 3:
            health_status = "fair"
        else:
            health_status = "attention_needed"
        
        # Construct Final Response
        dashboard_data = {
            "user": {
                "id": str(user.id),
                "name": user.name or "User",
                "age": user.age,
                "gender": user.gender
            },
            "overall_health_summary": overall_health_summary,
            "health_status": health_status,
            "abnormal_results": abnormal_results,
            "total_tests": len(all_tests),
            "total_abnormal": len(abnormal_tests),
            "active_medications_count": len(active_meds),
            "active_medications": [
                {
                    "id": str(m.id),
                    "brand_name": m.brand_name,
                    "dosage": m.dosage
                }
                for m in active_meds
            ]
        }
        
        # 4. Save to Cache
        if cache_entry:
            cache_entry.insights_json = dashboard_data
            # Explicitly touch updated_at to ensure it's newer than the data we just read
            cache_entry.updated_at = func.now()
        else:
            new_cache = HealthInsightCache(
                user_id=user_id,
                insights_json=dashboard_data
            )
            db.add(new_cache)
            
        await db.commit()
        logger.info("✅ Dashboard data cached successfully")
        
        return dashboard_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load dashboard: {str(e)}"
        )


@router.post("/get-advice")
async def get_health_advice(
    user_id: UUID,
    test_name: str,
    test_value: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed AI health advice for a specific test result
    """
    logger.info(f"Generating advice for {test_name} (user {user_id})")
    
    try:
        from agent.health_analyzer import get_detailed_advice
        
        # Get user context
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        user_context = {
            "age": user.age,
            "gender": user.gender,
            "conditions_json": user.conditions_json or []
        }
        
        # Generate advice
        advice = await get_detailed_advice(test_name, test_value, user_context)
        
        return {
            "success": True,
            "test_name": test_name,
            "advice": advice
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating advice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate advice: {str(e)}"
        )
