"""
DingTalk Adapter - Handles DingTalk specific webhook processing and signature verification.
"""

import hmac
import hashlib
import base64
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DingtalkSigner:
    """Helper for DingTalk signature verification."""
    
    @staticmethod
    def verify(timestamp: str, sign: str, secret: str) -> bool:
        """
        Verify the DingTalk signature.
        
        Args:
            timestamp: The timestamp from the query string
            sign: The signature from the query string
            secret: The app secret for the bot
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not secret:
            logger.warning("No secret provided for DingTalk signature verification")
            return False
            
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()
        
        calculated_sign = base64.b64encode(hmac_code).decode("utf-8")
        return calculated_sign == sign

    @staticmethod
    def is_timestamp_valid(timestamp_str: str, window_seconds: int = 3600) -> bool:
        """Check if the timestamp is within a reasonable window."""
        try:
            timestamp = int(timestamp_str) / 1000 # DingTalk uses ms
            now = time.time()
            return abs(now - timestamp) < window_seconds
        except (ValueError, TypeError):
            return False
