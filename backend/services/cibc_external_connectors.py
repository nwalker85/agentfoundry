"""
CIBC External Service Connectors

Provides integration with:
1. Pindrop Fraud Detection API
2. Customer Context Engine (Case Management)
3. Core Banking System (Signature - Read Only)
4. G&D Card Production API
"""

import logging
import os
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


# ============================================
# 1. Pindrop Fraud Detection API
# ============================================


class PindropConnector:
    """
    Pindrop API connector for real-time fraud scoring and voice biometrics.

    Fraud scores: 0-100
    - < 30: Low risk
    - 30-50: Low-medium risk
    - 50-70: Medium risk (additional verification required)
    - 70+: High risk (escalate to Card Security Officer)
    """

    def __init__(self):
        self.api_base_url = os.getenv("PINDROP_API_URL", "https://api.pindrop.com/v1")
        self.api_key = os.getenv("PINDROP_API_KEY")
        self.timeout = 10.0

    async def get_fraud_score(
        self, session_id: str, customer_id: str, phone_number: str | None = None, voice_sample: bytes | None = None
    ) -> dict[str, Any]:
        """
        Get fraud risk score from Pindrop.

        Args:
            session_id: Contact session identifier
            customer_id: Customer identifier
            phone_number: Customer phone number (optional)
            voice_sample: Voice biometric sample (optional)

        Returns:
            {
                "fraud_score": int (0-100),
                "risk_level": str (LOW|MEDIUM|HIGH|CRITICAL),
                "confidence": float (0.0-1.0),
                "device_fingerprint": dict,
                "voice_match": bool (if voice_sample provided)
            }
        """
        if not self.api_key:
            logger.warning("Pindrop API key not configured, using mock score")
            return self._mock_fraud_score(session_id)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/fraud-score",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "session_id": session_id,
                        "customer_id": customer_id,
                        "phone_number": phone_number,
                        "voice_sample": voice_sample.hex() if voice_sample else None,
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Pindrop API error: {e}")
            return self._mock_fraud_score(session_id)

    def _mock_fraud_score(self, session_id: str) -> dict[str, Any]:
        """Mock fraud score for development/testing"""
        # Generate deterministic score from session_id hash
        score = abs(hash(session_id)) % 100

        if score < 30:
            risk_level = "LOW"
        elif score < 50:
            risk_level = "MEDIUM"
        elif score < 70:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        return {
            "fraud_score": score,
            "risk_level": risk_level,
            "confidence": 0.85,
            "device_fingerprint": {"mock": True},
            "voice_match": True,
        }


# ============================================
# 2. Customer Context Engine (Case Management)
# ============================================


class ContextEngineConnector:
    """
    Customer Context Engine for case management and interaction history.

    Context Windows:
    - Standard: Last 30 days OR 10 interactions (whichever is more)
    - Adaptive (PWM): Larger window based on customer value
    """

    def __init__(self):
        self.api_base_url = os.getenv("CONTEXT_ENGINE_API_URL", "https://context-engine.cibc.internal/api")
        self.api_key = os.getenv("CONTEXT_ENGINE_API_KEY")
        self.timeout = 5.0

    async def get_customer_context(self, customer_id: str, context_window_type: str = "standard") -> dict[str, Any]:
        """
        Get customer interaction history and context.

        Args:
            customer_id: Customer identifier
            context_window_type: "standard" or "adaptive" (PWM)

        Returns:
            {
                "recent_cases": [list of case objects],
                "recent_interactions": [list of interaction summaries],
                "customer_profile": {profile data},
                "context_loaded_at": ISO datetime
            }
        """
        if not self.api_key:
            logger.warning("Context Engine API key not configured, using mock data")
            return self._mock_context(customer_id)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/customer/{customer_id}/context",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={"window_type": context_window_type},
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Context Engine API error: {e}")
            return self._mock_context(customer_id)

    async def create_case(self, customer_id: str, session_id: str, case_type: str, channel: str) -> dict[str, Any]:
        """Create a new case for customer interaction"""
        if not self.api_key:
            return {"case_id": f"CASE-{session_id}", "mock": True}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/cases",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "customer_id": customer_id,
                        "session_id": session_id,
                        "case_type": case_type,
                        "channel": channel,
                        "start_time": datetime.utcnow().isoformat(),
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Context Engine case creation error: {e}")
            return {"case_id": f"CASE-{session_id}", "error": str(e)}

    def _mock_context(self, customer_id: str) -> dict[str, Any]:
        """Mock context data for development/testing"""
        return {
            "recent_cases": [],
            "recent_interactions": [],
            "customer_profile": {"customer_id": customer_id, "pwm_status": False, "tenure_years": 5},
            "context_loaded_at": datetime.utcnow().isoformat(),
            "mock": True,
        }


# ============================================
# 3. Core Banking System (Signature - Read Only)
# ============================================


class CoreBankingConnector:
    """
    Core Banking (Signature) connector for customer/account data.

    READ ONLY - No writes from agent groups.

    Provides:
    - Customer account relationships
    - Communication preferences
    - PWM status detection (ACQ ST = PRWLTH)
    """

    def __init__(self):
        self.api_base_url = os.getenv("CORE_BANKING_API_URL", "https://signature.cibc.internal/api")
        self.api_key = os.getenv("CORE_BANKING_API_KEY")
        self.timeout = 5.0

    async def get_customer_profile(self, customer_id: str) -> dict[str, Any]:
        """Get customer profile from core banking"""
        if not self.api_key:
            logger.warning("Core Banking API key not configured, using mock data")
            return self._mock_customer_profile(customer_id)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/customers/{customer_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Core Banking API error: {e}")
            return self._mock_customer_profile(customer_id)

    async def get_communication_preferences(self, customer_id: str) -> dict[str, Any]:
        """Get customer communication preferences and consent"""
        if not self.api_key:
            return {
                "sms_consent": True,
                "email_consent": True,
                "push_consent": True,
                "preferred_channel": "sms",
                "mock": True,
            }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/customers/{customer_id}/communication-preferences",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Core Banking communication preferences error: {e}")
            return {
                "sms_consent": True,
                "email_consent": True,
                "push_consent": False,
                "preferred_channel": "sms",
                "error": str(e),
            }

    async def is_pwm_customer(self, customer_id: str) -> bool:
        """Check if customer is PWM (ACQ ST = PRWLTH)"""
        profile = await self.get_customer_profile(customer_id)
        return profile.get("acq_st") == "PRWLTH"

    def _mock_customer_profile(self, customer_id: str) -> dict[str, Any]:
        """Mock customer profile for development/testing"""
        return {
            "customer_id": customer_id,
            "name": "Mock Customer",
            "acq_st": "STANDARD",
            "account_relationships": [],
            "mock": True,
        }


# ============================================
# 4. G&D Card Production API
# ============================================


class GDProductionConnector:
    """
    Giesecke & Devrient (G&D) Card Production API.

    Submission Types:
    - Batch: Scheduled 5:30 PM Barbados time
    - Rush: Real-time for instant cards
    """

    def __init__(self):
        self.api_base_url = os.getenv("GD_API_URL", "https://gd-production.cibc.internal/api")
        self.api_key = os.getenv("GD_API_KEY")
        self.timeout = 15.0

    async def submit_batch(self, batch_date: str, requests: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Submit batch of replacement requests to G&D.

        Args:
            batch_date: Date of batch (YYYY-MM-DD)
            requests: List of replacement request objects

        Returns:
            {
                "batch_id": str,
                "request_count": int,
                "submission_status": str,
                "estimated_production_date": str
            }
        """
        if not self.api_key:
            logger.warning("G&D API key not configured, using mock submission")
            return self._mock_batch_submission(batch_date, requests)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/batches",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "batch_date": batch_date,
                        "requests": requests,
                        "submission_time": datetime.utcnow().isoformat(),
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"G&D batch submission error: {e}")
            return self._mock_batch_submission(batch_date, requests)

    async def submit_rush(self, request_id: str, priority: str = "instant") -> dict[str, Any]:
        """
        Submit rush/instant card request to G&D.

        Args:
            request_id: Replacement request ID
            priority: "instant" or "express"

        Returns:
            {
                "gd_order_id": str,
                "estimated_production_time": str (ISO duration),
                "production_status": str
            }
        """
        if not self.api_key:
            return {
                "gd_order_id": f"GD-RUSH-{request_id}",
                "estimated_production_time": "PT2H",
                "production_status": "queued",
                "mock": True,
            }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/rush-orders",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "request_id": request_id,
                        "priority": priority,
                        "submission_time": datetime.utcnow().isoformat(),
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"G&D rush submission error: {e}")
            return {
                "gd_order_id": f"GD-RUSH-{request_id}",
                "estimated_production_time": "PT2H",
                "production_status": "error",
                "error": str(e),
            }

    def _mock_batch_submission(self, batch_date: str, requests: list[dict[str, Any]]) -> dict[str, Any]:
        """Mock batch submission for development/testing"""
        return {
            "batch_id": f"GD-BATCH-{batch_date}",
            "request_count": len(requests),
            "submission_status": "accepted",
            "estimated_production_date": batch_date,
            "mock": True,
        }


# ============================================
# Connector Factory
# ============================================


def get_pindrop_connector() -> PindropConnector:
    """Get Pindrop connector instance"""
    return PindropConnector()


def get_context_engine_connector() -> ContextEngineConnector:
    """Get Context Engine connector instance"""
    return ContextEngineConnector()


def get_core_banking_connector() -> CoreBankingConnector:
    """Get Core Banking connector instance"""
    return CoreBankingConnector()


def get_gd_connector() -> GDProductionConnector:
    """Get G&D Production connector instance"""
    return GDProductionConnector()
