import asyncio
import logging
import time
from app.tasks.celery_app import celery_app
from app.database.session import AsyncSessionLocal
from app.models.prediction import Prediction
from app.services.ml_service import ml_service
from sqlalchemy import select

logger = logging.getLogger("app.tasks.prediction_tasks")

async def async_process_prediction(prediction_id: int):
    logger.info(f"Starting async processing for prediction {prediction_id}")
    async with AsyncSessionLocal() as db:
        # Fetch prediction
        result = await db.execute(select(Prediction).where(Prediction.id == prediction_id))
        prediction = result.scalar_one_or_none()
        if not prediction:
            logger.error(f"Prediction {prediction_id} not found in database.")
            return
        
        # Update status
        prediction.status = "processing"
        await db.commit()
        
        start_time = time.time()
        try:
            # Predict
            pred_res = ml_service.predict(prediction.image_path, prediction.model_used)
            
            # Update prediction details
            prediction.rock_type = pred_res.get("rock_type", "Unknown")
            prediction.lithology_class = pred_res.get("lithology_class", "Unknown")
            prediction.mineral_predictions = pred_res.get("mineral_predictions", {})
            prediction.confidence_score = float(pred_res.get("confidence_score", 0.0))
            prediction.top_predictions = pred_res.get("top_predictions", [])
            prediction.preprocessing_info = pred_res.get("preprocessing_info", {})
            prediction.processing_time = float(time.time() - start_time)
            prediction.status = "completed"
            
            logger.info(f"Successfully processed prediction {prediction_id} as {prediction.lithology_class}")
        except Exception as e:
            logger.error(f"Failed to process prediction {prediction_id}: {e}", exc_info=True)
            prediction.status = "failed"
            prediction.processing_time = float(time.time() - start_time)
            
        await db.commit()

@celery_app.task(name="app.tasks.prediction_tasks.process_prediction")
def process_prediction(prediction_id: int):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # Submit task to running loop
        future = asyncio.run_coroutine_threadsafe(async_process_prediction(prediction_id), loop)
        return future.result()
    else:
        return loop.run_until_complete(async_process_prediction(prediction_id))
