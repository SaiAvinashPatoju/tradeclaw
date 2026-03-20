"""
TradeClaw — Firebase Cloud Messaging Module
Sends push notifications for signal alerts.
"""
import json
import logging
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger("tradeclaw.fcm")

_app = None

# Firebase service account key path
_SERVICE_ACCOUNT_PATH = Path(__file__).resolve().parent.parent / "firebase-service-account.json"

# Confidence tier → emoji mapping
CONFIDENCE_EMOJI = {
    "SNIPER": "🎯",
    "HIGH": "🔥",
    "MODERATE": "⚡",
}


def init_fcm():
    """Initialize Firebase Admin SDK. Call once at startup."""
    global _app
    try:
        if _app is not None:
            return

        if not _SERVICE_ACCOUNT_PATH.exists():
            logger.warning(f"Firebase service account not found at {_SERVICE_ACCOUNT_PATH}. "
                           f"FCM notifications will be disabled.")
            return

        cred = credentials.Certificate(str(_SERVICE_ACCOUNT_PATH))
        _app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")


def is_initialized() -> bool:
    """Check if FCM is ready to send."""
    return _app is not None


async def send_signal_push(signal: dict, device_token: str | None = None) -> bool:
    """
    Send an FCM push notification for a signal.

    Args:
        signal: signal dict with id, symbol, score, confidence, etc.
        device_token: FCM device token (if None, sends to topic 'signals')

    Returns:
        True if sent successfully, False otherwise.
    """
    if not is_initialized():
        logger.warning("FCM not initialized — skipping push notification")
        return False

    try:
        emoji = CONFIDENCE_EMOJI.get(signal.get("confidence", ""), "📊")
        confidence = signal.get("confidence", "SIGNAL")
        symbol = signal.get("symbol", "").replace("USDT", "/USDT")

        title = f"{emoji} {confidence}: {symbol}"
        body = (
            f"Score {signal.get('score', 0)} | "
            f"TP +{signal.get('target_pct', 5)}% | "
            f"SL -{signal.get('stop_loss_pct', 1)}%"
        )

        # Data payload (full signal JSON for app processing)
        data_payload = {}
        for key, value in signal.items():
            data_payload[key] = str(value)

        notification = messaging.Notification(title=title, body=body)

        if device_token:
            message = messaging.Message(
                notification=notification,
                data=data_payload,
                token=device_token,
            )
        else:
            # Send to topic (all subscribers)
            message = messaging.Message(
                notification=notification,
                data=data_payload,
                topic="signals",
            )

        response = messaging.send(message)
        logger.info(f"FCM push sent: {signal.get('id')} → {response}")
        return True

    except Exception as e:
        logger.error(f"FCM push failed for {signal.get('id', '?')}: {e}")
        return False
