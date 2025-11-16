"""
Governance Agent - Security and policy enforcement

Responsibilities:
- Filter PII (Personally Identifiable Information)
- Filter PHI (Protected Health Information) for HIPAA compliance
- Enforce rate limits per user/action
- Validate permissions and access control
- Manage secrets securely (API keys, credentials)
- Audit logging for compliance
- Policy enforcement (allowed tools, max cost, etc.)

Platform agent (Tier 1 - Production Required).
"""

import asyncio
import logging
import re
import hashlib
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class GovernanceAgent:
    """
    Platform agent for security, compliance, and policy enforcement.
    Guards all inputs/outputs and manages sensitive data.
    """
    
    def __init__(self, llm=None):
        """
        Initialize Governance Agent.
        
        Args:
            llm: Language model for intelligent filtering (optional)
        """
        self.llm = llm or ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
        
        # Rate limiting storage
        self._rate_limits: Dict[str, List[datetime]] = defaultdict(list)
        
        # Audit log storage (production would use persistent store)
        self._audit_log: List[Dict[str, Any]] = []
        
        # Secrets storage (production would use vault like AWS Secrets Manager)
        self._secrets: Dict[str, Dict[str, str]] = {}
        
        # Policies (configurable per customer)
        self._policies = {
            'max_cost_per_request': 1.0,  # USD
            'max_tokens_per_request': 100000,
            'allowed_tools': None,  # None = all allowed
            'blocked_tools': [],
            'require_approval_for_tools': [],  # Tools requiring human approval
        }
        
        # PII patterns
        self._pii_patterns = {
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            'credit_card': re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            'ip_address': re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
        }
        
        # PHI patterns (HIPAA)
        self._phi_patterns = {
            'mrn': re.compile(r'\b(MRN|Medical Record Number)[:\s]+[\w-]+\b', re.IGNORECASE),
            'diagnosis': re.compile(r'\b(diagnosis|condition|disease)[:\s]+[\w\s]+\b', re.IGNORECASE),
            'medication': re.compile(r'\b(medication|prescription|drug)[:\s]+[\w\s]+\b', re.IGNORECASE),
        }
        
        logger.info("GovernanceAgent initialized")
    
    async def filter_pii(
        self,
        text: str,
        redact_mode: str = 'mask'
    ) -> Dict[str, Any]:
        """
        Filter PII from text.
        
        Args:
            text: Text to filter
            redact_mode: 'mask' (replace with ***), 'hash', or 'remove'
        
        Returns:
            Dict with filtered text and detected PII types
        """
        logger.debug("Filtering PII from text")
        
        filtered_text = text
        detected_pii = []
        
        for pii_type, pattern in self._pii_patterns.items():
            matches = pattern.findall(text)
            if matches:
                detected_pii.append({
                    'type': pii_type,
                    'count': len(matches)
                })
                
                logger.warning(f"Detected {len(matches)} {pii_type} in text")
                
                # Apply redaction
                if redact_mode == 'mask':
                    filtered_text = pattern.sub('[REDACTED_' + pii_type.upper() + ']', filtered_text)
                elif redact_mode == 'hash':
                    for match in matches:
                        hashed = hashlib.sha256(match.encode()).hexdigest()[:8]
                        filtered_text = filtered_text.replace(match, f'[HASH_{hashed}]')
                elif redact_mode == 'remove':
                    filtered_text = pattern.sub('', filtered_text)
        
        return {
            'original_length': len(text),
            'filtered_text': filtered_text,
            'filtered_length': len(filtered_text),
            'detected_pii': detected_pii,
            'has_pii': len(detected_pii) > 0
        }
    
    async def filter_phi(
        self,
        text: str,
        redact_mode: str = 'mask'
    ) -> Dict[str, Any]:
        """
        Filter PHI (Protected Health Information) for HIPAA compliance.
        
        Args:
            text: Text to filter
            redact_mode: 'mask', 'hash', or 'remove'
        
        Returns:
            Dict with filtered text and detected PHI types
        """
        logger.debug("Filtering PHI from text (HIPAA compliance)")
        
        filtered_text = text
        detected_phi = []
        
        for phi_type, pattern in self._phi_patterns.items():
            matches = pattern.findall(text)
            if matches:
                detected_phi.append({
                    'type': phi_type,
                    'count': len(matches)
                })
                
                logger.warning(f"Detected {len(matches)} {phi_type} in text (HIPAA)")
                
                # Apply redaction
                if redact_mode == 'mask':
                    filtered_text = pattern.sub('[REDACTED_PHI_' + phi_type.upper() + ']', filtered_text)
                elif redact_mode == 'hash':
                    for match in matches:
                        if isinstance(match, tuple):
                            match = ' '.join(match)
                        hashed = hashlib.sha256(match.encode()).hexdigest()[:8]
                        filtered_text = filtered_text.replace(match, f'[PHI_HASH_{hashed}]')
                elif redact_mode == 'remove':
                    filtered_text = pattern.sub('', filtered_text)
        
        return {
            'original_length': len(text),
            'filtered_text': filtered_text,
            'filtered_length': len(filtered_text),
            'detected_phi': detected_phi,
            'has_phi': len(detected_phi) > 0,
            'hipaa_compliant': True
        }
    
    async def filter_sensitive_data(
        self,
        text: str,
        filter_pii: bool = True,
        filter_phi: bool = False
    ) -> Dict[str, Any]:
        """
        Combined filtering of sensitive data.
        
        Args:
            text: Text to filter
            filter_pii: Whether to filter PII
            filter_phi: Whether to filter PHI
        
        Returns:
            Dict with filtered text and all detected issues
        """
        result = {
            'original_text': text,
            'filtered_text': text,
            'pii_detected': [],
            'phi_detected': [],
            'has_sensitive_data': False
        }
        
        # Apply PII filtering
        if filter_pii:
            pii_result = await self.filter_pii(text)
            result['filtered_text'] = pii_result['filtered_text']
            result['pii_detected'] = pii_result['detected_pii']
            result['has_sensitive_data'] = result['has_sensitive_data'] or pii_result['has_pii']
        
        # Apply PHI filtering
        if filter_phi:
            phi_result = await self.filter_phi(result['filtered_text'])
            result['filtered_text'] = phi_result['filtered_text']
            result['phi_detected'] = phi_result['detected_phi']
            result['has_sensitive_data'] = result['has_sensitive_data'] or phi_result['has_phi']
        
        # Log if sensitive data was found
        if result['has_sensitive_data']:
            await self._audit_log_event(
                event_type='sensitive_data_filtered',
                details={
                    'pii_types': [p['type'] for p in result['pii_detected']],
                    'phi_types': [p['type'] for p in result['phi_detected']],
                    'original_length': len(text),
                    'filtered_length': len(result['filtered_text'])
                }
            )
        
        return result
    
    async def enforce_rate_limit(
        self,
        user_id: str,
        action: str,
        limit: int = 100,
        window_seconds: int = 3600
    ) -> Dict[str, Any]:
        """
        Enforce rate limits for user actions.
        
        Args:
            user_id: User identifier
            action: Action being performed
            limit: Maximum actions allowed
            window_seconds: Time window in seconds
        
        Returns:
            Dict with allowed status and remaining quota
        """
        key = f"{user_id}:{action}"
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        
        # Clean old entries
        self._rate_limits[key] = [
            ts for ts in self._rate_limits[key]
            if ts > cutoff
        ]
        
        # Check limit
        current_count = len(self._rate_limits[key])
        
        if current_count >= limit:
            logger.warning(f"Rate limit exceeded for {user_id}:{action} ({current_count}/{limit})")
            await self._audit_log_event(
                event_type='rate_limit_exceeded',
                user_id=user_id,
                details={'action': action, 'count': current_count, 'limit': limit}
            )
            return {
                'allowed': False,
                'reason': 'Rate limit exceeded',
                'current_count': current_count,
                'limit': limit,
                'remaining': 0,
                'reset_in_seconds': window_seconds
            }
        
        # Record this action
        self._rate_limits[key].append(now)
        
        return {
            'allowed': True,
            'current_count': current_count + 1,
            'limit': limit,
            'remaining': limit - current_count - 1,
            'reset_in_seconds': window_seconds
        }
    
    async def validate_permissions(
        self,
        user_id: str,
        action: str,
        resource: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate user permissions for an action.
        
        Args:
            user_id: User identifier
            action: Action to validate
            resource: Optional resource identifier
        
        Returns:
            Dict with permission status
        """
        # TODO: Integrate with actual RBAC system (e.g., database, LDAP, OAuth)
        # For now, basic simulation
        
        logger.debug(f"Validating permissions: {user_id} -> {action} on {resource}")
        
        # Simulate permission check
        # In production, query user roles and permissions from database
        allowed = True  # Default allow for now
        
        result = {
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'allowed': allowed,
            'reason': 'Permission granted' if allowed else 'Permission denied'
        }
        
        # Audit log
        await self._audit_log_event(
            event_type='permission_check',
            user_id=user_id,
            details=result
        )
        
        return result
    
    async def inject_secrets(
        self,
        tool_name: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Securely inject secrets into tool configuration.
        
        Args:
            tool_name: Tool requiring secrets
            config: Tool configuration
        
        Returns:
            Config with secrets injected
        """
        logger.debug(f"Injecting secrets for tool: {tool_name}")
        
        # Get secrets for this tool
        tool_secrets = self._secrets.get(tool_name, {})
        
        # Inject secrets into config
        enriched_config = config.copy()
        for key, value in tool_secrets.items():
            if key not in enriched_config:
                enriched_config[key] = value
        
        # Audit log (without logging actual secrets)
        await self._audit_log_event(
            event_type='secrets_injected',
            details={
                'tool': tool_name,
                'secrets_count': len(tool_secrets)
            }
        )
        
        return enriched_config
    
    async def store_secret(
        self,
        tool_name: str,
        secret_key: str,
        secret_value: str
    ):
        """
        Store a secret securely.
        
        In production, this would use AWS Secrets Manager, HashiCorp Vault, etc.
        
        Args:
            tool_name: Tool the secret belongs to
            secret_key: Secret key (e.g., 'api_key')
            secret_value: Secret value
        """
        logger.info(f"Storing secret for {tool_name}: {secret_key}")
        
        if tool_name not in self._secrets:
            self._secrets[tool_name] = {}
        
        self._secrets[tool_name][secret_key] = secret_value
        
        # Audit log (without logging value)
        await self._audit_log_event(
            event_type='secret_stored',
            details={'tool': tool_name, 'key': secret_key}
        )
    
    async def enforce_policy(
        self,
        action: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enforce organizational policies.
        
        Args:
            action: Action being performed
            params: Action parameters
        
        Returns:
            Dict with policy enforcement result
        """
        logger.debug(f"Enforcing policies for action: {action}")
        
        violations = []
        
        # Check cost limit
        if 'estimated_cost' in params:
            if params['estimated_cost'] > self._policies['max_cost_per_request']:
                violations.append({
                    'policy': 'max_cost_per_request',
                    'limit': self._policies['max_cost_per_request'],
                    'value': params['estimated_cost']
                })
        
        # Check token limit
        if 'tokens' in params:
            if params['tokens'] > self._policies['max_tokens_per_request']:
                violations.append({
                    'policy': 'max_tokens_per_request',
                    'limit': self._policies['max_tokens_per_request'],
                    'value': params['tokens']
                })
        
        # Check allowed tools
        if action == 'tool_execution' and 'tool_name' in params:
            tool_name = params['tool_name']
            
            # Check if tool is blocked
            if tool_name in self._policies['blocked_tools']:
                violations.append({
                    'policy': 'blocked_tools',
                    'tool': tool_name,
                    'reason': 'Tool is explicitly blocked'
                })
            
            # Check if tool is in allowed list (if list exists)
            if self._policies['allowed_tools'] is not None:
                if tool_name not in self._policies['allowed_tools']:
                    violations.append({
                        'policy': 'allowed_tools',
                        'tool': tool_name,
                        'reason': 'Tool not in allowed list'
                    })
        
        # Log violations
        if violations:
            logger.warning(f"Policy violations detected: {violations}")
            await self._audit_log_event(
                event_type='policy_violation',
                details={'action': action, 'violations': violations}
            )
        
        return {
            'allowed': len(violations) == 0,
            'violations': violations,
            'action': action
        }
    
    async def _audit_log_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log event to audit trail.
        
        Args:
            event_type: Type of event
            user_id: Optional user identifier
            details: Event details
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'details': details or {}
        }
        
        self._audit_log.append(event)
        
        # Limit audit log size (production would use persistent store)
        if len(self._audit_log) > 10000:
            self._audit_log.pop(0)
        
        logger.debug(f"Audit log: {event_type}")
    
    async def get_audit_log(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get audit log entries.
        
        Args:
            user_id: Optional filter by user
            event_type: Optional filter by event type
            limit: Maximum entries to return
        
        Returns:
            List of audit log entries
        """
        filtered = self._audit_log
        
        if user_id:
            filtered = [e for e in filtered if e.get('user_id') == user_id]
        
        if event_type:
            filtered = [e for e in filtered if e['event_type'] == event_type]
        
        return list(reversed(filtered[-limit:]))
    
    async def update_policy(self, policy_updates: Dict[str, Any]):
        """
        Update governance policies.
        
        Args:
            policy_updates: Policies to update
        """
        logger.info(f"Updating policies: {list(policy_updates.keys())}")
        
        self._policies.update(policy_updates)
        
        await self._audit_log_event(
            event_type='policy_updated',
            details={'policies': list(policy_updates.keys())}
        )
    
    async def get_policies(self) -> Dict[str, Any]:
        """
        Get current policies.
        
        Returns:
            Current policy configuration
        """
        return self._policies.copy()
    
    async def check_compliance(
        self,
        text: str,
        compliance_standard: str = 'general'
    ) -> Dict[str, Any]:
        """
        Check if text complies with specific standards (HIPAA, GDPR, etc.).
        
        Args:
            text: Text to check
            compliance_standard: 'hipaa', 'gdpr', 'pci', or 'general'
        
        Returns:
            Compliance check result
        """
        logger.info(f"Checking compliance: {compliance_standard}")
        
        issues = []
        
        if compliance_standard in ['hipaa', 'general']:
            # Check for PHI
            phi_result = await self.filter_phi(text)
            if phi_result['has_phi']:
                issues.append({
                    'standard': 'HIPAA',
                    'issue': 'PHI detected',
                    'types': [p['type'] for p in phi_result['detected_phi']]
                })
        
        if compliance_standard in ['gdpr', 'pci', 'general']:
            # Check for PII
            pii_result = await self.filter_pii(text)
            if pii_result['has_pii']:
                issues.append({
                    'standard': 'GDPR/PCI',
                    'issue': 'PII detected',
                    'types': [p['type'] for p in pii_result['detected_pii']]
                })
        
        compliant = len(issues) == 0
        
        if not compliant:
            logger.warning(f"Compliance issues found: {issues}")
        
        return {
            'compliant': compliant,
            'standard': compliance_standard,
            'issues': issues,
            'timestamp': datetime.now().isoformat()
        }

