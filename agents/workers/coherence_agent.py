"""
Coherence Agent - Async response buffering and conflict resolution

Responsibilities:
- Buffer responses from multiple worker agents
- Deduplicate similar/identical responses
- Resolve conflicting information using LLM
- Compile final coherent response

Platform agent (always available, not domain-specific).
"""

import logging
from datetime import datetime
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage

logger = logging.getLogger(__name__)


class CoherenceAgent:
    """
    Platform agent for assembling coherent responses from multiple workers.
    Handles deduplication, conflict resolution, and response compilation.
    """

    def __init__(self):
        """Initialize Coherence Agent."""
        self.llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
        logger.info("CoherenceAgent initialized")

    async def process(self, worker_responses: dict[str, str]) -> str:
        """
        Process worker responses into a single coherent output.

        Args:
            worker_responses: Dictionary of {worker_name: response_text}

        Returns:
            Final compiled response string
        """
        logger.info(f"Processing {len(worker_responses)} worker responses")

        if not worker_responses:
            logger.warning("No worker responses to process")
            return "I'm not sure how to help with that. Could you rephrase?"

        # Single worker - return directly (no compilation needed)
        if len(worker_responses) == 1:
            response = list(worker_responses.values())[0]
            logger.info("Single worker response, returning directly")
            return response

        # Multiple workers - need compilation
        try:
            # Buffer responses
            buffered = await self._buffer_responses(worker_responses)

            # Deduplicate
            deduplicated = await self._deduplicate(buffered)

            # Resolve conflicts (if any)
            resolved = await self._resolve_conflicts(deduplicated)

            # Compile final output
            compiled = await self._compile_output(resolved)

            logger.info(f"Coherent response compiled ({len(compiled)} chars)")
            return compiled

        except Exception as e:
            logger.error(f"Error compiling responses: {e}", exc_info=True)
            # Fallback: concatenate responses with separators
            fallback = "\n\n".join(f"**{worker}:** {response}" for worker, response in worker_responses.items())
            logger.warning("Using fallback concatenation due to compilation error")
            return fallback

    async def _buffer_responses(self, worker_responses: dict[str, str]) -> list[dict[str, Any]]:
        """
        Buffer async responses from multiple workers.

        Args:
            worker_responses: Dictionary of worker responses

        Returns:
            List of buffered response objects with metadata
        """
        logger.debug(f"Buffering {len(worker_responses)} responses")

        buffered = []
        for worker_name, response_text in worker_responses.items():
            buffered.append(
                {
                    "worker": worker_name,
                    "response": response_text,
                    "timestamp": datetime.now().isoformat(),
                    "length": len(response_text),
                    "word_count": len(response_text.split()),
                }
            )

        logger.debug(f"Buffered {len(buffered)} responses")
        return buffered

    async def _deduplicate(self, buffered_responses: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Remove duplicate or highly similar responses.

        Uses simple string matching for now. Future: Use embeddings for semantic similarity.

        Args:
            buffered_responses: Buffered responses with metadata

        Returns:
            Deduplicated responses
        """
        logger.debug(f"Deduplicating {len(buffered_responses)} responses")

        if len(buffered_responses) <= 1:
            return buffered_responses

        deduplicated = []
        seen_responses = set()

        for response_obj in buffered_responses:
            response_text = response_obj["response"].strip().lower()

            # Simple exact match deduplication
            if response_text not in seen_responses:
                deduplicated.append(response_obj)
                seen_responses.add(response_text)
            else:
                logger.debug(f"Duplicate response removed from {response_obj['worker']}")

        logger.debug(f"Deduplicated to {len(deduplicated)} unique responses")
        return deduplicated

    async def _resolve_conflicts(self, deduplicated_responses: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Resolve contradictory information using LLM.

        For now, this is a pass-through. Future: Use LLM to detect and resolve conflicts.

        Args:
            deduplicated_responses: Deduplicated responses

        Returns:
            Responses with conflicts resolved
        """
        logger.debug(f"Checking {len(deduplicated_responses)} responses for conflicts")

        if len(deduplicated_responses) <= 1:
            return deduplicated_responses

        # TODO: Implement LLM-based conflict detection and resolution
        # For now, return as-is (no conflict resolution)

        logger.debug("No conflicts detected (conflict resolution not yet implemented)")
        return deduplicated_responses

    async def _compile_output(self, resolved_responses: list[dict[str, Any]]) -> str:
        """
        Assemble final coherent response from resolved worker outputs.

        Uses LLM to synthesize a natural, unified response.

        Args:
            resolved_responses: Responses with conflicts resolved

        Returns:
            Final compiled response string
        """
        logger.debug(f"Compiling {len(resolved_responses)} responses into final output")

        if not resolved_responses:
            return "I'm not sure how to help with that. Could you rephrase?"

        # Single response - return directly
        if len(resolved_responses) == 1:
            return resolved_responses[0]["response"]

        # Multiple responses - use LLM to synthesize
        try:
            # Build context for LLM
            responses_text = "\n\n".join(
                [f"Response from {resp['worker']}:\n{resp['response']}" for resp in resolved_responses]
            )

            system_prompt = """You are a response synthesis agent. You receive multiple responses from different specialized agents and must combine them into a single, coherent, natural-sounding response.

Your task:
1. Identify the key information from each agent's response
2. Remove redundancy and duplication
3. Organize information logically
4. Synthesize a unified response that sounds natural (not like multiple agents talking)
5. Maintain all important details from each agent
6. Use a consistent tone and style

Do NOT mention "Agent X said..." or "According to the PM agent...". Just provide the unified response as if from a single assistant.

Below are the responses from different agents:

{responses}

Provide a single, coherent, natural response:"""

            # Call LLM to synthesize
            response = await self.llm.ainvoke([SystemMessage(content=system_prompt.format(responses=responses_text))])

            compiled_response = response.content.strip()

            logger.debug(f"Compiled response: {len(compiled_response)} chars")
            return compiled_response

        except Exception as e:
            logger.error(f"Error during LLM compilation: {e}", exc_info=True)

            # Fallback: simple concatenation with headers
            fallback = "\n\n".join([resp["response"] for resp in resolved_responses])

            logger.warning("Using fallback concatenation due to LLM error")
            return fallback

    async def validate_coherence(self, compiled_response: str) -> dict[str, Any]:
        """
        Validate the coherence of the compiled response.

        Optional quality check - can be used for monitoring/debugging.

        Args:
            compiled_response: The compiled response to validate

        Returns:
            Validation results dictionary
        """
        logger.debug("Validating response coherence")

        # Basic validation metrics
        validation = {
            "length": len(compiled_response),
            "word_count": len(compiled_response.split()),
            "sentence_count": compiled_response.count(".")
            + compiled_response.count("!")
            + compiled_response.count("?"),
            "has_content": len(compiled_response.strip()) > 0,
            "quality_score": 0.0,
        }

        # Calculate simple quality score
        if validation["word_count"] > 0:
            # Favor responses with moderate length (not too short, not too long)
            word_count = validation["word_count"]
            if 10 <= word_count <= 200:
                validation["quality_score"] = 1.0
            elif word_count < 10:
                validation["quality_score"] = 0.5
            else:
                validation["quality_score"] = 0.8

        logger.debug(f"Coherence validation: {validation['quality_score']:.2f} score")
        return validation
