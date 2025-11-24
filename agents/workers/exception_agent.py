"""
Exception Agent - Runtime error handling and resilience

Responsibilities:
- Wrap node executions with error handling
- Implement retry logic with exponential backoff
- Execute fallback paths on failures
- Circuit breaker pattern for external services
- Human-in-the-loop (HITL) escalation
- Dead letter queue for unrecoverable errors

Platform agent (Tier 1 - Production Required).
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class ExceptionAgent:
    """
    Platform agent for runtime error handling and resilience.
    Wraps all customer worker executions with safety mechanisms.
    """

    def __init__(self, llm=None):
        """
        Initialize Exception Agent.

        Args:
            llm: Language model for intelligent error recovery (optional)
        """
        self.llm = llm or ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)

        # Circuit breaker state per service
        self._circuit_breakers: dict[str, dict[str, Any]] = {}

        # Dead letter queue for unrecoverable errors
        self._dead_letter_queue: list[dict[str, Any]] = []

        logger.info("ExceptionAgent initialized")

    async def execute_with_resilience(
        self, node_func: Callable, state: dict[str, Any], config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute a node function with full resilience: retries, timeout, fallback.

        This is the main entry point for executing any customer worker node.

        Args:
            node_func: The node function to execute
            state: Current state
            config: Execution configuration (retries, timeout, fallback, etc.)

        Returns:
            Result dict with success status and data or error
        """
        config = config or {}

        # Extract configuration
        max_retries = config.get("max_retries", 3)
        timeout_seconds = config.get("timeout_seconds", 60)
        fallback_func = config.get("fallback_func", None)
        circuit_breaker_key = config.get("circuit_breaker_key", None)
        enable_hitl = config.get("enable_hitl", False)

        logger.info(f"Executing node with resilience: retries={max_retries}, timeout={timeout_seconds}s")

        # Check circuit breaker if configured
        if circuit_breaker_key:
            if not await self._check_circuit_breaker(circuit_breaker_key):
                logger.warning(f"Circuit breaker OPEN for {circuit_breaker_key}, skipping execution")
                return {
                    "success": False,
                    "error": f"Circuit breaker open for {circuit_breaker_key}",
                    "fallback_executed": False,
                }

        # Attempt execution with retries
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1}/{max_retries}")

                # Execute with timeout
                result = await self._execute_with_timeout(node_func, state, timeout_seconds)

                # Success! Record for circuit breaker
                if circuit_breaker_key:
                    await self._record_success(circuit_breaker_key)

                logger.info(f"Node execution succeeded on attempt {attempt + 1}")
                return {"success": True, "data": result, "attempts": attempt + 1}

            except TimeoutError as e:
                last_error = e
                logger.warning(f"Timeout on attempt {attempt + 1}: {e}")

            except Exception as e:
                last_error = e
                logger.warning(f"Error on attempt {attempt + 1}: {e}")

                # Record failure for circuit breaker
                if circuit_breaker_key:
                    await self._record_failure(circuit_breaker_key)

            # Exponential backoff before retry (except on last attempt)
            if attempt < max_retries - 1:
                backoff_seconds = await self._calculate_backoff(attempt)
                logger.info(f"Backing off {backoff_seconds}s before retry")
                await asyncio.sleep(backoff_seconds)

        # All retries exhausted
        logger.error(f"All {max_retries} attempts failed. Last error: {last_error}")

        # Try fallback if configured
        if fallback_func:
            logger.info("Attempting fallback execution")
            try:
                fallback_result = await fallback_func(state, last_error)
                return {
                    "success": True,
                    "data": fallback_result,
                    "fallback_executed": True,
                    "original_error": str(last_error),
                }
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")

        # HITL escalation if enabled
        if enable_hitl:
            logger.info("Escalating to human-in-the-loop")
            await self._escalate_to_human(node_func, state, last_error)

        # Add to dead letter queue
        await self._add_to_dead_letter_queue(
            {
                "node_func": str(node_func),
                "state": state,
                "error": str(last_error),
                "timestamp": datetime.now().isoformat(),
                "attempts": max_retries,
            }
        )

        return {"success": False, "error": str(last_error), "attempts": max_retries, "fallback_executed": False}

    async def _execute_with_timeout(self, node_func: Callable, state: dict[str, Any], timeout_seconds: float) -> Any:
        """
        Execute function with timeout.

        Args:
            node_func: Function to execute
            state: State to pass to function
            timeout_seconds: Timeout in seconds

        Returns:
            Function result

        Raises:
            asyncio.TimeoutError: If execution exceeds timeout
        """
        try:
            return await asyncio.wait_for(node_func(state), timeout=timeout_seconds)
        except TimeoutError:
            logger.error(f"Node execution timed out after {timeout_seconds}s")
            raise

    async def _calculate_backoff(self, attempt: int, base_delay: float = 1.0) -> float:
        """
        Calculate exponential backoff delay.

        Args:
            attempt: Current attempt number (0-indexed)
            base_delay: Base delay in seconds

        Returns:
            Delay in seconds with jitter
        """
        # Exponential backoff: base_delay * 2^attempt
        # Max 30 seconds
        delay = min(base_delay * (2**attempt), 30.0)

        # Add jitter (±20%)
        import random

        jitter = delay * 0.2 * (random.random() - 0.5)

        return delay + jitter

    async def _check_circuit_breaker(self, service_key: str) -> bool:
        """
        Check if circuit breaker allows execution.

        Args:
            service_key: Service identifier

        Returns:
            True if execution allowed, False if circuit is open
        """
        if service_key not in self._circuit_breakers:
            # Initialize circuit breaker
            self._circuit_breakers[service_key] = {
                "state": CircuitState.CLOSED,
                "failure_count": 0,
                "last_failure_time": None,
                "success_count": 0,
                "open_until": None,
            }

        breaker = self._circuit_breakers[service_key]

        # If OPEN, check if timeout expired
        if breaker["state"] == CircuitState.OPEN:
            if breaker["open_until"] and datetime.now() >= breaker["open_until"]:
                logger.info(f"Circuit breaker {service_key} transitioning to HALF_OPEN")
                breaker["state"] = CircuitState.HALF_OPEN
                breaker["success_count"] = 0
            else:
                return False  # Still open, reject

        return True  # CLOSED or HALF_OPEN, allow execution

    async def _record_success(self, service_key: str):
        """
        Record successful execution for circuit breaker.

        Args:
            service_key: Service identifier
        """
        if service_key not in self._circuit_breakers:
            return

        breaker = self._circuit_breakers[service_key]
        breaker["success_count"] += 1

        # If HALF_OPEN and got enough successes, close circuit
        if breaker["state"] == CircuitState.HALF_OPEN and breaker["success_count"] >= 3:
            logger.info(f"Circuit breaker {service_key} closing (recovered)")
            breaker["state"] = CircuitState.CLOSED
            breaker["failure_count"] = 0

    async def _record_failure(self, service_key: str):
        """
        Record failed execution for circuit breaker.

        Args:
            service_key: Service identifier
        """
        if service_key not in self._circuit_breakers:
            return

        breaker = self._circuit_breakers[service_key]
        breaker["failure_count"] += 1
        breaker["last_failure_time"] = datetime.now()

        # Threshold to open circuit: 5 failures
        if breaker["failure_count"] >= 5:
            logger.warning(f"Circuit breaker {service_key} opening (too many failures)")
            breaker["state"] = CircuitState.OPEN
            breaker["open_until"] = datetime.now() + timedelta(seconds=60)  # Open for 60s

    async def _escalate_to_human(self, node_func: Callable, state: dict[str, Any], error: Exception):
        """
        Escalate error to human operator (HITL - Human In The Loop).

        Args:
            node_func: The failed function
            state: State when error occurred
            error: The error that occurred
        """
        logger.info("Escalating to human operator")

        # TODO: Integrate with notification system (Slack, email, PagerDuty)
        # For now, log detailed information

        escalation = {
            "timestamp": datetime.now().isoformat(),
            "node_func": str(node_func),
            "error": str(error),
            "error_type": type(error).__name__,
            "state_summary": {"keys": list(state.keys()), "message_count": len(state.get("messages", []))},
        }

        logger.critical(f"HITL ESCALATION: {escalation}")

        # TODO: Store escalation in database for human review dashboard
        # TODO: Send notification to on-call engineer
        # TODO: Pause agent execution until human resolves

    async def _add_to_dead_letter_queue(self, error_record: dict[str, Any]):
        """
        Add failed execution to dead letter queue.

        Args:
            error_record: Record of the failed execution
        """
        self._dead_letter_queue.append(error_record)
        logger.info(f"Added to dead letter queue (total: {len(self._dead_letter_queue)})")

        # Limit DLQ size
        if len(self._dead_letter_queue) > 1000:
            self._dead_letter_queue.pop(0)

    async def get_dead_letter_queue(self) -> list[dict[str, Any]]:
        """
        Get all items in dead letter queue.

        Returns:
            List of error records
        """
        return self._dead_letter_queue.copy()

    async def retry_dead_letter_item(self, index: int, node_func: Callable) -> dict[str, Any]:
        """
        Retry a specific item from dead letter queue.

        Args:
            index: Index in DLQ
            node_func: Function to retry with

        Returns:
            Result of retry attempt
        """
        if index >= len(self._dead_letter_queue):
            return {"success": False, "error": "Invalid DLQ index"}

        item = self._dead_letter_queue[index]
        logger.info(f"Retrying DLQ item {index}")

        # Retry with resilience
        result = await self.execute_with_resilience(
            node_func,
            item["state"],
            {"max_retries": 1},  # Single retry for DLQ items
        )

        # If successful, remove from DLQ
        if result["success"]:
            self._dead_letter_queue.pop(index)
            logger.info(f"DLQ item {index} successfully retried and removed")

        return result

    async def get_circuit_breaker_status(self) -> dict[str, dict[str, Any]]:
        """
        Get status of all circuit breakers.

        Returns:
            Dict of service -> circuit breaker state
        """
        return {
            service: {
                "state": breaker["state"].value,
                "failure_count": breaker["failure_count"],
                "last_failure_time": breaker["last_failure_time"].isoformat() if breaker["last_failure_time"] else None,
                "open_until": breaker["open_until"].isoformat() if breaker["open_until"] else None,
            }
            for service, breaker in self._circuit_breakers.items()
        }

    async def reset_circuit_breaker(self, service_key: str):
        """
        Manually reset a circuit breaker (admin operation).

        Args:
            service_key: Service to reset
        """
        if service_key in self._circuit_breakers:
            logger.info(f"Manually resetting circuit breaker: {service_key}")
            self._circuit_breakers[service_key] = {
                "state": CircuitState.CLOSED,
                "failure_count": 0,
                "last_failure_time": None,
                "success_count": 0,
                "open_until": None,
            }

    async def analyze_error_pattern(self, errors: list[str]) -> dict[str, Any]:
        """
        Use LLM to analyze error patterns and suggest solutions.

        Args:
            errors: List of error messages

        Returns:
            Analysis with suggested fixes
        """
        if not errors:
            return {"analysis": "No errors to analyze"}

        logger.info(f"Analyzing {len(errors)} errors with LLM")

        # Build prompt
        errors_text = "\n".join([f"- {err}" for err in errors[:10]])  # Limit to 10

        system_prompt = """You are an expert at analyzing software errors and suggesting solutions.
        
Analyze the following errors and provide:
1. Common patterns or root causes
2. Suggested fixes or mitigations
3. Whether this needs immediate human attention

Be concise and actionable."""

        user_prompt = f"""Analyze these errors:

{errors_text}

Provide your analysis:"""

        try:
            response = await self.llm.ainvoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])

            return {"analysis": response.content, "error_count": len(errors), "timestamp": datetime.now().isoformat()}

        except Exception as e:
            logger.error(f"Error during LLM analysis: {e}")
            return {"analysis": f"Failed to analyze: {e}", "error_count": len(errors)}
