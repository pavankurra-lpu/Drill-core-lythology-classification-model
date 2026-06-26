import logging
from typing import Optional, Dict, Any, List
from llm.assistant import GeologicalAssistant
from llm.config import LLMConfig

logger = logging.getLogger("app.services.llm_service")

class LLMService:
    def __init__(self):
        self.config = LLMConfig()
        self.assistant = GeologicalAssistant(self.config)

    def explain_prediction(self, prediction_result: Dict[str, Any]) -> str:
        try:
            return self.assistant.explain_prediction(prediction_result)
        except Exception as e:
            logger.error(f"Error in explain_prediction: {e}")
            return f"Failed to generate explanation: {str(e)}"

    def answer_question(self, question: str, context: str = "") -> str:
        try:
            return self.assistant.answer_question(question, context)
        except Exception as e:
            logger.error(f"Error in answer_question: {e}")
            return f"Failed to answer question: {str(e)}"

    def generate_geological_report(self, prediction: Dict[str, Any], borehole_info: Optional[Dict[str, Any]] = None) -> str:
        try:
            info = borehole_info or {}
            return self.assistant.generate_report(prediction, info)
        except Exception as e:
            logger.error(f"Error in generate_geological_report: {e}")
            return f"Failed to generate report: {str(e)}"

    def explain_mineral(self, mineral_name: str) -> str:
        try:
            return self.assistant.explain_mineral(mineral_name)
        except Exception as e:
            logger.error(f"Error in explain_mineral: {e}")
            return f"Failed to explain mineral: {str(e)}"

    def explain_formation(self, formation_name: str) -> str:
        try:
            return self.assistant.explain_formation(formation_name)
        except Exception as e:
            logger.error(f"Error in explain_formation: {e}")
            return f"Failed to explain formation: {str(e)}"

    def summarize_borehole(self, borehole_data: Dict[str, Any]) -> str:
        try:
            return self.assistant.summarize_borehole(borehole_data)
        except Exception as e:
            logger.error(f"Error in summarize_borehole: {e}")
            return f"Failed to summarize borehole: {str(e)}"

    def generate_recommendations(self, prediction_result: Dict[str, Any]) -> str:
        try:
            return self.assistant.generate_recommendations(prediction_result)
        except Exception as e:
            logger.error(f"Error in generate_recommendations: {e}")
            return f"Failed to generate recommendations: {str(e)}"

# Singleton instance
llm_service = LLMService()
