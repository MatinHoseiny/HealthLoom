"""
HealthLoom Chat API Routes
AI chatbot with health context
"""

import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from database import get_db
from models import User, Conversation, SessionState, TestResult, Medication
from schemas import ChatRequest, ChatResponse
from agent.graph import run_healthloom_agent
from agent.nodes.conversation_manager import stream_gemini_response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with HealthLoom AI
    
    The AI has access to user's complete health profile and provides
    personalized, context-aware responses.
    """
    logger.info(f"💬 Chat request from user {chat_request.user_id}")
    
    try:
        # Validate user
        result = await db.execute(select(User).where(User.id == chat_request.user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {chat_request.user_id} not found"
            )
        
        # Get user context if requested
        recent_tests = []
        current_meds = []
        chat_history = []
        
        if chat_request.include_context:
            # Get recent test results
            test_results = await db.execute(
                select(TestResult)
                .where(TestResult.user_id == chat_request.user_id)
                .order_by(TestResult.test_date.desc())
                .limit(20)
            )
            recent_tests = [
                {
                    "test_name": t.test_name,
                    "value": t.value,
                    "unit": t.unit,
                    "reference_range": t.reference_range,
                    "test_date": str(t.test_date),
                    "is_abnormal": t.is_abnormal,
                    "category": t.category
                }
                for t in test_results.scalars().all()
            ]
            
            # Get medications
            medications = await db.execute(
                select(Medication)
                .where(Medication.user_id == chat_request.user_id)
                .where(Medication.is_active == True)
            )
            current_meds = [
                {
                    "brand_name": m.brand_name,
                    "active_molecule": m.active_molecule,
                    "dosage": m.dosage,
                    "frequency": m.frequency,
                    "is_active": m.is_active
                }
                for m in medications.scalars().all()
            ]
            
            # Get recent conversation history
            conversations = await db.execute(
                select(Conversation)
                .where(Conversation.user_id == chat_request.user_id)
                .order_by(Conversation.created_at.desc())
                .limit(10)
            )
            chat_history = [
                {
                    "role": c.role,
                    "content": c.content
                }
                for c in reversed(list(conversations.scalars().all()))  # Reverse to get chronological order
            ]
        
        # Save User Message FIRST to ensure correct timestamp order
        user_message = Conversation(
            user_id=chat_request.user_id,
            role="user",
            content=chat_request.message
        )
        db.add(user_message)
        await db.commit()
        
        # Load user preferences
        from models import UserPreferences
        prefs_result = await db.execute(
            select(UserPreferences).where(UserPreferences.user_id == chat_request.user_id)
        )
        user_prefs = prefs_result.scalar_one_or_none()
        
        preferences_data = None
        if user_prefs:
            preferences_data = {
                "health_goals": user_prefs.health_goals or [],
                "dietary_restrictions": user_prefs.dietary_restrictions or [],
                "exercise_frequency": user_prefs.exercise_frequency,
                "health_concerns": user_prefs.health_concerns or [],
                "sleep_hours": user_prefs.sleep_hours,
                "stress_level": user_prefs.stress_level
            }
        
        # Run AI agent
        logger.info("🤖 Running HealthLoom agent for chat...")
        
        agent_result = await run_healthloom_agent(
            user_id=str(chat_request.user_id),
            input_type="chat",
            user_message=chat_request.message,
            user_profile={
                "name": user.name,
                "age": user.age,
                "gender": user.gender,
                "limitations_json": user.limitations_json,
                "conditions_json": user.conditions_json
            },
            user_preferences=preferences_data,
            recent_tests=recent_tests,
            current_medications=current_meds
        )
        
        if not agent_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Chat processing failed: {', '.join(agent_result.get('errors', ['Unknown error']))}"
            )
        
        # Save Assistant Message
        assistant_message = Conversation(
            user_id=chat_request.user_id,
            role="assistant",
            content=agent_result.get("response", ""),
            context_used=agent_result.get("context_used", {})
        )
        
        db.add(assistant_message)
        await db.commit()
        
        logger.info("✅ Chat response generated and saved")
        
        return ChatResponse(
            message=agent_result.get("response", ""),
            context_used=agent_result.get("context_used", {}),
            suggestions=agent_result.get("ai_analysis", {}).get("suggestions", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


@router.post("/stream")
async def chat_stream(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Stream chat response in real-time (Server-Sent Events)
    
    Returns a streaming response for better UX
    """
    logger.info(f"📡 Stream chat request from user {chat_request.user_id}")
    
    try:
        # Validate user and get context (same as above)
        result = await db.execute(select(User).where(User.id == chat_request.user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {chat_request.user_id} not found"
            )
        
        # Get context
        recent_tests = []
        current_meds = []
        chat_history = []
        
        if chat_request.include_context:
            pass
        
        # Create streaming generator
        async def generate_stream():
            """Generate SSE stream"""
            try:
                full_response = ""
                
                async for chunk in stream_gemini_response(
                    user_message=chat_request.message,
                    user_profile={
                        "age": user.age,
                        "gender": user.gender,
                        "limitations_json": user.limitations_json,
                        "conditions_json": user.conditions_json
                    },
                    recent_tests=recent_tests,
                    current_medications=current_meds,
                    chat_history=chat_history
                ):
                    full_response += chunk
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                
                # Send completion event
                yield f"data: {json.dumps({'done': True})}\n\n"
                
                # Save conversation after streaming completes
                user_msg = Conversation(
                    user_id=chat_request.user_id,
                    role="user",
                    content=chat_request.message
                )
                assistant_msg = Conversation(
                    user_id=chat_request.user_id,
                    role="assistant",
                    content=full_response
                )
                
                db.add(user_msg)
                db.add(assistant_msg)
                await db.commit()
                
            except Exception as e:
                logger.error(f"Error in stream: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up stream: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stream setup failed: {str(e)}"
        )


@router.get("/history/{user_id}")
async def get_chat_history(
    user_id: UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Get conversation history for a user
    """
    logger.info(f"Fetching chat history for user {user_id}")
    
    try:
        conversations = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
        )
        
        messages = [
            {
                "id": str(c.id),
                "role": c.role,
                "content": c.content,
                "timestamp": c.created_at.isoformat(),
                "context_used": c.context_used
            }
            for c in reversed(list(conversations.scalars().all()))
        ]
        
        return {
            "user_id": str(user_id),
            "messages": messages,
            "total_count": len(messages)
        }
        
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch chat history: {str(e)}"
        )
