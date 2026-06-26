import asyncio
import logging
import time
from app.tasks.celery_app import celery_app
from app.database.session import AsyncSessionLocal
from app.models.dataset import Dataset
from sqlalchemy import select

logger = logging.getLogger("app.tasks.training_tasks")

async def async_retrain_model(dataset_id: int, model_name: str):
    logger.info(f"Starting retraining of model {model_name} on dataset {dataset_id}")
    async with AsyncSessionLocal() as db:
        # Fetch dataset
        result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
        dataset = result.scalar_one_or_none()
        if not dataset:
            logger.error(f"Dataset {dataset_id} not found.")
            return
        
        dataset.status = "training"
        await db.commit()
        
        try:
            # Simulate training steps (e.g. 5 seconds)
            for epoch in range(1, 6):
                await asyncio.sleep(1.0)
                logger.info(f"Epoch {epoch}/5: Loss={0.5 - epoch*0.08:.4f}, Val Acc={75.0 + epoch*3.5:.2f}%")
                
            dataset.status = "completed"
            logger.info(f"Model retraining completed successfully for {model_name}.")
        except Exception as e:
            logger.error(f"Error retraining model: {e}", exc_info=True)
            dataset.status = "failed"
            
        await db.commit()

@celery_app.task(name="app.tasks.training_tasks.retrain_model")
def retrain_model(dataset_id: int, model_name: str):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(async_retrain_model(dataset_id, model_name), loop)
        return future.result()
    else:
        return loop.run_until_complete(async_retrain_model(dataset_id, model_name))
