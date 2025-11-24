"""Validation helpers for manifest-defined schemas."""

from __future__ import annotations

from typing import Any

from jsonschema import Draft7Validator, ValidationError

from .models import SchemaDefinition


def validate_payload(payload: dict[str, Any], schema: SchemaDefinition) -> None:
    """
    Validate payload against the schema definition.

    Raises ValueError with aggregated messages if validation fails.
    """

    validator = Draft7Validator(schema.model_dump())
    errors: list[ValidationError] = list(validator.iter_errors(payload))
    if not errors:
        return

    message = "; ".join(f"{'/'.join(map(str, err.path)) or 'root'}: {err.message}" for err in errors)
    raise ValueError(message)
