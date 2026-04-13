import os
import logging
from logtail import LogtailHandler

def get_cloud_logger(name: str):
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if already configured
    if any(isinstance(h, LogtailHandler) for h in logger.handlers):
        return logger
        
    logger.setLevel(logging.INFO)
    
    token = os.environ.get("LOGTAIL_SOURCE_TOKEN")
    if token:
        try:
            handler = LogtailHandler(source_token=token)
            
            class CustomFormatter(logging.Formatter):
                def format(self, record):
                    # Attach specific logtail required categories manually if not natively captured
                    log_data = {
                        "module": record.module,
                        "severity": record.levelname,
                        "message": record.getMessage()
                    }
                    if hasattr(record, "user_id"):
                        log_data["user_id"] = record.user_id
                    if hasattr(record, "request_id"):
                        log_data["request_id"] = record.request_id
                    if hasattr(record, "category"):
                        log_data["category"] = record.category
                        
                    return super().format(record)
                    
            handler.setFormatter(CustomFormatter("%(message)s"))
            logger.addHandler(handler)
        except Exception:
            pass
            
    # Always keep console fallback for development/Railway logs view
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(console)
        
    return logger

# Shared instance for quick imports
cloud_logger = get_cloud_logger("genesis.cloud")
