# core/vision/vision_runner.py
"""
GENESIS Brain — LLaVA Vision Reasoning Pipeline
Receives images from the Lite client and generates scene descriptions.
Ensures model is loaded once at startup for low latency.
"""

import time
import logging
import os
from io import BytesIO
from PIL import Image

try:
    import torch
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

os.environ["HF_HUB_OFFLINE"] = "1"

logger = logging.getLogger(__name__)

class VisionRunner:
    def __init__(self):
        # Genesis root is two levels up from core/vision
        genesis_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.model_id = os.path.join(genesis_root, "models", "tinyllava")
        self.pipe = None
        self.ready = False
        try:
            self._load_model()
        except Exception as e:
            logger.error(f"[VISION] LLaVA initialization failed. Running YOLO-only mode: {e}")
            print(f"[VISION] LLaVA initialization failed. Running YOLO-only mode: {e}")

    def _load_model(self):
        if not TRANSFORMERS_AVAILABLE:
            logger.error("[VISION] Transformers/Torch not installed. LLaVA pipeline disabled.")
            return
            
        logger.info(f"[VISION] Loading LLaVA model: {self.model_id}")
        start_t = time.time()
        
        # Load the pipeline. Use GPU if available to speed up inference.
        device = 0 if torch.cuda.is_available() else -1
        
        tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            local_files_only=True,
            trust_remote_code=True
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            local_files_only=True,
            trust_remote_code=True,
            use_safetensors=True,
            low_cpu_mem_usage=True
        )
        
        if getattr(model.config, 'pad_token_id', None) is None:
            model.config.pad_token_id = tokenizer.eos_token_id
            
        self.pipe = pipeline(
            "image-text-to-text", 
            model=model,
            tokenizer=tokenizer,
            device=device,
            model_kwargs={"local_files_only": True}
        )
        
        logger.info(f"[VISION] Model loaded in {time.time() - start_t:.2f}s")
        self.ready = True

    def describe_scene(self, image_bytes, prompt="USER: <image>\nDescribe what you see in this scene.\nASSISTANT:"):
        """
        Process an incoming camera frame and run LLaVA reasoning.
        """
        if not self.ready or not self.pipe:
            return "Vision system is not ready."

        try:
            image = Image.open(BytesIO(image_bytes))
            
            # Standard LLaVA prompt
            outputs = self.pipe(image, prompt=prompt, generate_kwargs={"max_new_tokens": 50})
            result = outputs[0]["generated_text"]
            
            # Clean up the returned string if it includes the prompt
            if "ASSISTANT:" in result:
                result = result.split("ASSISTANT:")[-1].strip()
                
            logger.info(f"[VISION] Scene description: {result}")
            return result
            
        except Exception as e:
            logger.error(f"[VISION] Inference error: {e}")
            return f"Error processing vision frame: {e}"

# Singleton instance
_runner = None

def get_vision_runner():
    global _runner
    if _runner is None:
        _runner = VisionRunner()
    return _runner

def start_llava_reasoner():
    """Startup wrapper for thread daemonization."""
    logger.info("[VISION] LLaVA reasoner thread started.")
    get_vision_runner()
    while True:
        time.sleep(1)

