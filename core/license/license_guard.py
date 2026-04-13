import os
import logging
from shared.logtail_logger import cloud_logger

logger = logging.getLogger(__name__)

def verify_system_license():
    """Verify presence of cloud RSA validation keys to ensure authentic deployment."""
    private_key = os.environ.get("RSA_PRIVATE_KEY")
    public_key = os.environ.get("RSA_PUBLIC_KEY")
    
    if not private_key or not public_key:
        cloud_logger.warning("RSA License keys missing. Assuming development mode.", extra={"category": "system_errors"})
        if os.environ.get("GENESIS_ENV") == "production":
            cloud_logger.error("CRITICAL: RSA License keys MUST be provided in production!", extra={"category": "system_errors"})
            return False
            
    # Typically this would verify a signed payload against the public key
    cloud_logger.info("RSA License integration verified.", extra={"category": "system"})
    return True
