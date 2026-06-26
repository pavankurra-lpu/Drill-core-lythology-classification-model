import asyncio
import logging
import os
from app.tasks.celery_app import celery_app
from app.database.session import AsyncSessionLocal
from app.models.report import Report
from app.models.user import User
from app.models.prediction import Prediction
from app.services.llm_service import llm_service
from app.services.report_service import report_service
from app.core.config import settings
from sqlalchemy import select

logger = logging.getLogger("app.tasks.report_tasks")

async def async_generate_report_task(report_id: int):
    logger.info(f"Generating PDF for report {report_id}")
    async with AsyncSessionLocal() as db:
        # Fetch report
        result = await db.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()
        if not report:
            logger.error(f"Report {report_id} not found.")
            return
        
        # Fetch user
        user_result = await db.execute(select(User).where(User.id == report.user_id))
        user = user_result.scalar_one_or_none()
        
        # Fetch prediction
        pred_result = await db.execute(select(Prediction).where(Prediction.id == report.prediction_id))
        prediction = pred_result.scalar_one_or_none()
        
        if not prediction or not user:
            logger.error(f"Missing user or prediction for report {report_id}")
            return
        
        try:
            # Generate markdown content from LLM if not already populated
            if not report.content:
                pred_dict = {
                    "id": prediction.id,
                    "rock_type": prediction.rock_type,
                    "lithology_class": prediction.lithology_class,
                    "confidence_score": prediction.confidence_score,
                    "mineral_predictions": prediction.mineral_predictions,
                    "model_used": prediction.model_used,
                    "image_path": prediction.image_path,
                    "original_filename": prediction.original_filename,
                    "created_at": str(prediction.created_at)
                }
                report.content = llm_service.generate_geological_report(pred_dict, borehole_info={})
            
            # Generate PDF bytes
            pdf_bytes = report_service.generate_pdf_report(
                prediction={
                    "id": prediction.id,
                    "rock_type": prediction.rock_type,
                    "lithology_class": prediction.lithology_class,
                    "confidence_score": prediction.confidence_score,
                    "mineral_predictions": prediction.mineral_predictions,
                    "model_used": prediction.model_used,
                    "image_path": prediction.image_path,
                    "original_filename": prediction.original_filename
                },
                user={
                    "username": user.username
                },
                report_content=report.content
            )
            
            # Save PDF to disk
            pdf_filename = f"report_{report_id}_{prediction.id}.pdf"
            pdf_path = os.path.join(settings.UPLOAD_DIR, pdf_filename)
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)
                
            # Update database
            report.pdf_path = f"/static/uploads/{pdf_filename}"
            logger.info(f"Successfully generated PDF at {pdf_path}")
            
        except Exception as e:
            logger.error(f"Error in generating report PDF: {e}", exc_info=True)
            
        await db.commit()

@celery_app.task(name="app.tasks.report_tasks.generate_report_task")
def generate_report_task(report_id: int):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(async_generate_report_task(report_id), loop)
        return future.result()
    else:
        return loop.run_until_complete(async_generate_report_task(report_id))
