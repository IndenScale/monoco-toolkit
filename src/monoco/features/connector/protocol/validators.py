"""
Mailbox Protocol Validators - Schema validation utilities.
"""

from typing import List, Optional, Tuple
from datetime import datetime

from pydantic import ValidationError

from .schema import InboundMessage, OutboundMessage, Provider, ContentType


def validate_inbound_message(data: dict) -> Tuple[bool, Optional[str]]:
    """
    Validate inbound message data against the schema.

    Args:
        data: Dictionary containing message data

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        InboundMessage.model_validate(data)
        return True, None
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"{field}: {msg}")
        return False, "; ".join(errors)


def validate_outbound_message(data: dict) -> Tuple[bool, Optional[str]]:
    """
    Validate outbound message data against the schema.

    Args:
        data: Dictionary containing message data

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        OutboundMessage.model_validate(data)
        return True, None
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"{field}: {msg}")
        return False, "; ".join(errors)


def validate_provider(provider: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a provider string against known providers.

    Args:
        provider: Provider identifier string

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        Provider(provider.lower())
        return True, None
    except ValueError:
        valid_providers = [p.value for p in Provider]
        return False, f"Invalid provider '{provider}'. Valid: {', '.join(valid_providers)}"


def validate_content_type(content_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a content type string.

    Args:
        content_type: Content type identifier

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        ContentType(content_type.lower())
        return True, None
    except ValueError:
        valid_types = [ct.value for ct in ContentType]
        return False, f"Invalid content type '{content_type}'. Valid: {', '.join(valid_types)}"


def validate_message_id(message_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a message ID format.

    Format should be: {provider}_{uid}

    Args:
        message_id: Message identifier

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not message_id:
        return False, "Message ID cannot be empty"

    if "_" not in message_id:
        return False, f"Message ID must follow format {{provider}}_{{uid}}, got: {message_id}"

    parts = message_id.split("_", 1)
    if len(parts) != 2:
        return False, f"Invalid message ID format: {message_id}"

    provider_part, uid_part = parts

    if not provider_part or not uid_part:
        return False, f"Message ID cannot have empty provider or uid: {message_id}"

    # Validate provider part
    is_valid, error = validate_provider(provider_part)
    if not is_valid:
        return False, error

    return True, None


def validate_filename(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a message filename format.

    Format should be: {ISO8601}_{Provider}_{UID}.md

    Args:
        filename: Message filename

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filename.endswith(".md"):
        return False, f"Filename must end with .md: {filename}"

    # Remove .md extension
    base = filename[:-3]

    parts = base.split("_", 2)
    if len(parts) < 3:
        return False, f"Filename must follow format {{ISO8601}}_{{Provider}}_{{UID}}.md, got: {filename}"

    timestamp, provider, uid = parts[0], parts[1], parts[2]

    # Validate timestamp format (YYYYMMDDTHHMMSS)
    if len(timestamp) != 15 or timestamp[8] != "T":
        return False, f"Invalid timestamp format in filename (expected YYYYMMDDTHHMMSS): {timestamp}"

    try:
        datetime.strptime(timestamp, "%Y%m%dT%H%M%S")
    except ValueError:
        return False, f"Invalid timestamp in filename: {timestamp}"

    # Validate provider
    is_valid, error = validate_provider(provider)
    if not is_valid:
        return False, error

    return True, None


def get_validation_errors(data: dict, as_inbound: bool = True) -> List[str]:
    """
    Get a list of all validation errors for a message.

    Args:
        data: Dictionary containing message data
        as_inbound: Whether to validate as inbound (True) or outbound (False)

    Returns:
        List of error messages
    """
    if as_inbound:
        is_valid, error = validate_inbound_message(data)
    else:
        is_valid, error = validate_outbound_message(data)

    if is_valid:
        return []

    return error.split("; ") if error else ["Unknown validation error"]
