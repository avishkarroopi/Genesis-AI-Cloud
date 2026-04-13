"""
GENESIS Self-Improvement: Reflection Engine
Analyzes trace failures using the LLM and extracts actionable learning strategies.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ReflectionEngine:
    def reflect_on_failure(self, trace_data: Dict[str, Any]):
        """Passes the trace to the Groq LLM to figure out what went wrong."""
        prompt = trace_data.get("prompt", "")
        response = trace_data.get("llm_response", "")
        intent = trace_data.get("detected_intent", "GENERAL")
        
        reflection_prompt = f"""
        You are a Self-Improvement System for the GENESIS AI.
        An AI reasoning failure occurred during this trace:
        
        Intent: {intent}
        User Prompt: {prompt}
        Bot Response: {response}
        
        Analyze what went wrong and provide a correction strategy.
        Format your response exactly as:
        [MISTAKE]: <brief description of error>
        [CORRECTION]: <brief instruction on what to do next time>
        """
        
        # We fire this off to Groq non-blocking
        try:
            from core.ai_router import OR_REASONING_MODEL
            import os, requests
            groq_key = os.environ.get("GROQ_API_KEY")
            if not groq_key: return
            
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            payload = {
                "model": "llama3-70b-8192", 
                "messages": [{"role": "user", "content": reflection_prompt}],
                "temperature": 0.2
            }
            r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
            if r.status_code == 200:
                answer = r.json()["choices"][0]["message"]["content"]
                mistake_line = [l for l in answer.split('\n') if '[MISTAKE]' in l]
                correction_line = [l for l in answer.split('\n') if '[CORRECTION]' in l]
                
                if mistake_line and correction_line:
                    mistake = mistake_line[0].replace("[MISTAKE]:", "").strip()
                    correction = correction_line[0].replace("[CORRECTION]:", "").strip()
                    
                    from core.self_improvement.learning_memory import get_learning_memory
                    get_learning_memory().store_insight(intent, mistake, correction)
        except Exception as e:
            logger.error(f"[REFLECTION] Engine failed: {e}")

_engine = None
def get_reflection_engine() -> ReflectionEngine:
    global _engine
    if _engine is None: _engine = ReflectionEngine()
    return _engine
