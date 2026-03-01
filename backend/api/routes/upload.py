import logging
import os
import hashlib
from datetime import datetime, date
from uuid import UUID
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import aiofiles

from database import get_db
from models import User, TestResult, Medication
from schemas import UploadResponse, TestResultCreate, TestResultResponse
from config import settings
from agent.graph import run_healthloom_agent

logger = logging.getLogger(__name__)

router = APIRouter()


def parse_date(date_str: str) -> date:
    """Parse date string to python date object"""
    if not date_str:
        return None
    try:
        # Try ISO format first (YYYY-MM-DD)
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        try:
            # Try other common formats
            return datetime.strptime(date_str, "%d/%m/%Y").date()
        except ValueError:
            try:
                return datetime.strptime(date_str, "%m/%d/%Y").date()
            except ValueError:
                # Return None if parsing fails
                return None


@router.get("/history/{user_id}")
async def get_upload_history(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get history of uploaded documents with summaries
    """
    try:
        # Query distinct source files
        query = (
            select(
                TestResult.source_file_path,
                TestResult.upload_date,
                func.count(TestResult.id).label('test_count'),
                func.array_agg(TestResult.category).label('categories')
            )
            .where(TestResult.user_id == UUID(user_id))
            .where(TestResult.source_file_path.isnot(None))
            .group_by(TestResult.source_file_path, TestResult.upload_date)
            .order_by(TestResult.upload_date.desc())
        )
        
        result = await db.execute(query)
        uploads = result.all()
        
        history = []
        for upload in uploads:
            # Extract filename from path
            file_path = upload.source_file_path
            filename = os.path.basename(file_path)
            # Remove UUID prefix if present (format: uuid_filename)
            if '_' in filename:
                parts = filename.split('_', 1)
                if len(parts[0]) == 36:  # UUID length
                    filename = parts[1]
            
            # Determine primary category
            categories = [c for c in upload.categories if c]
            primary_category = max(set(categories), key=categories.count) if categories else "General"
            
            history.append({
                "filename": filename,
                "upload_date": upload.upload_date,
                "test_count": upload.test_count,
                "summary": f"{primary_category} ({upload.test_count} tests)",
                "file_path": file_path
            })
            
        return history
        
    except Exception as e:
        logger.error(f"Error fetching upload history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch history: {str(e)}"
        )


@router.get("/details/{user_id}")
async def get_upload_details(
    user_id: str,
    file_path: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed test results for a specific upload
    """
    try:
        # Get all test results for this file
        result = await db.execute(
            select(TestResult)
            .where(TestResult.user_id == UUID(user_id))
            .where(TestResult.source_file_path == file_path)
        )
        tests = result.scalars().all()
        
        if not tests:
            raise HTTPException(status_code=404, detail="Upload not found")
            
        return {
            "success": True,
            "extracted_tests": [
                {
                    "test_name": t.test_name,
                    "category": t.category,
                    "value": t.value,
                    "unit": t.unit,
                    "is_abnormal": t.is_abnormal,
                    "test_date": t.test_date
                }
                for t in tests
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching upload details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{user_id}")
async def delete_upload(
    user_id: str,
    file_path: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an upload and its associated test results.
    Uses exact path match first, then basename fallback for cross-platform compatibility.
    """
    try:
        logger.info(f"DELETE request: user_id={user_id}, file_path={file_path}")
        
        from sqlalchemy import delete
        
        # Cross-platform basename extraction
        basename = file_path.replace('\\', '/').split('/')[-1]
        
        # Try exact path match first
        result = await db.execute(
            delete(TestResult)
            .where(TestResult.user_id == UUID(user_id))
            .where(TestResult.source_file_path == file_path)
        )
        deleted_count = result.rowcount
        
        # Fallback: if no exact match, try matching by the robust basename
        if deleted_count == 0:
            logger.warning(f"No exact path match, trying robust basename fallback: {basename}")
            result = await db.execute(
                delete(TestResult)
                .where(TestResult.user_id == UUID(user_id))
                .where(TestResult.source_file_path.like(f"%{basename}%"))
            )
            deleted_count = result.rowcount
            
        if deleted_count == 0:
            logger.warning(f"Database delete yielded 0 rows for file: {file_path}. Will attempt to clean physical file anyway.")
        else:
            logger.info(f"Deleted {deleted_count} test results from database")
        
        # Eradicate physical files robustly
        try:
            docker_path = f"/app/uploads/{basename}"
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted physical file matches explicit path: {file_path}")
            elif os.path.exists(docker_path):
                os.remove(docker_path)
                logger.info(f"Deleted physical file via robust Docker path lookup: {docker_path}")
            else:
                from glob import glob
                matches = glob(f"/app/uploads/*{basename}")
                if matches:
                    os.remove(matches[0])
                    logger.info(f"Deleted physical file via glob wildcard: {matches[0]}")
                else:
                    logger.warning(f"Physical file not found at either path or via wildcard.")
        except Exception as file_error:
            logger.warning(f"Failed to delete physical file: {file_error}")
            
        # Invalidate AI Cache for this user
        from models import HealthInsightCache
        await db.execute(
            delete(HealthInsightCache)
            .where(HealthInsightCache.user_id == UUID(user_id))
        )
        logger.info(f"Invalidated AI cache for user {user_id}")
            
        await db.commit()
        logger.info(f"Delete operation completed: {deleted_count} records removed")
        return {"success": True, "message": "Upload deleted successfully", "deleted_count": deleted_count}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload medical document for AI analysis
    
    Accepts: Images (JPEG, PNG) and PDFs
    Returns: Extracted test results and AI analysis
    """
    logger.info(f"📄 Upload request from user {user_id}: {file.filename}")
    
    start_time = datetime.now()
    
    try:
        # Validate user
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        # Validate file type
        if file.content_type not in settings.allowed_file_types_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file.content_type} not allowed. Allowed types: {settings.allowed_file_types}"
            )
        
        # Validate file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB"
            )
        
        # Read file content for hash calculation
        content = await file.read()
        
        # Calculate SHA-256 hash for duplicate detection
        file_hash = hashlib.sha256(content).hexdigest()
        logger.info(f"📊 File hash: {file_hash}")
        
        # Check for duplicate file upload
        duplicate_check = await db.execute(
            select(TestResult)
            .where(TestResult.user_id == UUID(user_id))
            .where(TestResult.file_hash == file_hash)
            .limit(1)
        )
        existing_upload = duplicate_check.scalar_one_or_none()
        
        if existing_upload:
            logger.warning(f"🚫 Duplicate file detected for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This file already exists in your uploads."
            )
        
        # Save file
        file_extension = os.path.splitext(file.filename)[1]
        safe_filename = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
        file_path = settings.upload_dir / safe_filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        logger.info(f"📁 File saved: {file_path}")
        
        # Get user's recent test results and medications for context
        
        # Get recent tests
        test_results = await db.execute(
            select(TestResult)
            .where(TestResult.user_id == UUID(user_id))
            .order_by(TestResult.test_date.desc())
            .limit(20)
        )
        recent_tests = [
            {
                "test_name": t.test_name,
                "value": t.value,
                "unit": t.unit,
                "test_date": str(t.test_date),
                "is_abnormal": t.is_abnormal
            }
            for t in test_results.scalars().all()
        ]
        
        # Get current medications
        medications = await db.execute(
            select(Medication)
            .where(Medication.user_id == UUID(user_id))
            .where(Medication.is_active == True)
        )
        current_meds = [
            {
                "brand_name": m.brand_name,
                "active_molecule": m.active_molecule,
                "dosage": m.dosage,
                "is_active": m.is_active
            }
            for m in medications.scalars().all()
        ]
        
        # Run AI agent to process document
        logger.info("🤖 Running HealthLoom agent for document processing...")
        
        agent_result = await run_healthloom_agent(
            user_id=user_id,
            input_type="document_upload",
            uploaded_file_path=str(file_path),
            uploaded_file_type=file.content_type,
            user_profile={
                "age": user.age,
                "gender": user.gender,
                "limitations_json": user.limitations_json,
                "conditions_json": user.conditions_json
            },
            recent_tests=recent_tests,
            current_medications=current_meds
        )
        
        if not agent_result["success"]:
            logger.error(f"Agent processing failed: {agent_result.get('errors')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Document processing failed: {', '.join(agent_result.get('errors', ['Unknown error']))}"
            )
        
        # Update user profile with extracted demographics if available
        patient_info = agent_result.get("patient_info", {})
        if patient_info:
            if patient_info.get("age") and isinstance(patient_info["age"], int):
                user.age = patient_info["age"]
            if patient_info.get("gender"):
                user.gender = patient_info["gender"]
            
            # We could also store the name if the User model had a name field, 
            # but currently it only has ID, age, gender, etc.
            # If we wanted to store name, we'd need to add a column or put it in profile_data
            if patient_info.get("name"):
                current_profile = user.profile_data or {}
                current_profile["extracted_name"] = patient_info["name"]
                user.profile_data = current_profile
                
            db.add(user)
            logger.info(f"👤 Updated user profile from document: Age={user.age}, Gender={user.gender}")

        # Save extracted tests to database
        extracted_tests = agent_result.get("extracted_tests", [])
        saved_tests = []
        
        # Extract and enforce a single test date for all extracted results
        all_dates = [t.get("test_date") for t in extracted_tests if t.get("test_date")]
        if all_dates:
            from collections import Counter
            most_common_date = Counter(all_dates).most_common(1)[0][0]
            logger.info(f"Enforcing single date {most_common_date} across all {len(extracted_tests)} extracted tests")
            for test in extracted_tests:
                test["test_date"] = most_common_date
        
        for test_data in extracted_tests:
            # Safely truncate fields to match database constraints
            t_name = str(test_data.get("test_name", ""))[:255] if test_data.get("test_name") else "Unknown Test"
            t_type = str(test_data.get("test_type_normalized", ""))[:255] if test_data.get("test_type_normalized") else None
            t_cat = str(test_data.get("category", ""))[:100] if test_data.get("category") else None
            t_val = str(test_data.get("value", ""))[:500] if test_data.get("value") else None
            t_unit = str(test_data.get("unit", ""))[:50] if test_data.get("unit") else None
            t_ref = str(test_data.get("reference_range", ""))[:500] if test_data.get("reference_range") else None

            # Strictly enforce boolean for asyncpg
            raw_abnormal = test_data.get("is_abnormal", False)
            if isinstance(raw_abnormal, str):
                is_abn = raw_abnormal.lower() in ("true", "1", "yes", "y", "t")
            else:
                is_abn = bool(raw_abnormal)

            test_result = TestResult(
                user_id=UUID(user_id),
                test_name=t_name,
                test_type_normalized=t_type,
                category=t_cat,
                value=t_val,
                unit=t_unit,
                reference_range=t_ref,
                is_abnormal=is_abn,
                test_date=parse_date(test_data.get("test_date")),
                source_file_path=str(file_path),
                source_file_type=file.content_type[:50] if file.content_type else None,
                file_hash=file_hash,  # Add file hash for duplicate detection
                ai_analysis=agent_result.get("ai_analysis", {}),
                extracted_data=test_data
            )
            
            db.add(test_result)
            saved_tests.append(test_result)
        
        await db.commit()
        
        # Refresh all saved tests
        for test in saved_tests:
            await db.refresh(test)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Clean up the file if no tests were found
        if len(saved_tests) == 0 and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.warning(f"Cleaned up file {file_path} because AI extracted 0 tests. Prevented orphanage.")
            except Exception as e:
                logger.error(f"Failed to clean up zero-test physical file: {e}")
                
        logger.info(f"✅ Upload complete: {len(saved_tests)} tests extracted in {processing_time:.2f}s")
        
        return UploadResponse(
            success=True,
            message=f"Successfully processed document and extracted {len(saved_tests)} test results",
            file_path=str(file_path),
            extracted_tests=[TestResultResponse.model_validate(t) for t in saved_tests],
            ai_analysis=agent_result.get("ai_analysis", {}),
            processing_time_seconds=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {e}", exc_info=True)
        # Clean up orphaned physical file if DB transaction fails
        if 'file_path' in locals() and file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up orphaned file: {file_path}")
            except Exception as cleanup_error:
                logger.error(f"Failed to clean up orphaned file: {cleanup_error}")
                
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload processing failed: {str(e)}"
        )


@router.get("/file/{user_id}")
async def serve_uploaded_file(
    user_id: str,
    file_path: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Serve the original uploaded file (image or PDF)
    """
    try:
        from fastapi.responses import FileResponse
        import mimetypes
        
        # Verify user owns this file
        result = await db.execute(
            select(TestResult)
            .where(TestResult.user_id == UUID(user_id))
            .where(TestResult.source_file_path == file_path)
            .limit(1)
        )
        test = result.scalar_one_or_none()
        
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found or you don't have permission to access it"
            )
        
        # Check if file exists on disk
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on server"
            )
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"
        
        filename = os.path.basename(file_path)
        
        logger.info(f"Serving file: {filename} to user {user_id}")
        
        # For images, display inline; for PDFs, also display inline
        # Only download for other file types
        disposition_type = "inline" if mime_type and (mime_type.startswith("image/") or mime_type == "application/pdf") else "attachment"
        
        return FileResponse(
            path=file_path,
            media_type=mime_type,
            filename=filename,
            headers={
                "Content-Disposition": f'{disposition_type}; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
