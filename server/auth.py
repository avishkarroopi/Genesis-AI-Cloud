import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth, credentials
import logging

logger = logging.getLogger(__name__)

try:
    if not firebase_admin._apps:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
            "private_key": os.environ.get("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
            "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
            "token_uri": "https://oauth2.googleapis.com/token",
        })
        firebase_admin.initialize_app(cred)
except Exception as e:
    logger.warning(f"Firebase initialization bypassed or failed safely: {e}")

security = HTTPBearer(auto_error=False)

async def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if not credentials:
        if os.environ.get("DEV_BYPASS_AUTH") == "true":
            return {"uid": "test_dev_user"}
        raise HTTPException(status_code=401, detail="Missing authorization token")
        
    token = credentials.credentials
    try:
        if os.environ.get("DEV_BYPASS_AUTH") == "true" and token == "test_token":
            return {"uid": "test_dev_user"}
            
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token")
