from monoco.core.config import DomainConfig, DomainItem
from monoco.features.issue.domain_service import DomainService


def test_domain_service_aliasing():
    config = DomainConfig(
        items=[
            DomainItem(name="backend.auth", aliases=["login", "auth"]),
            DomainItem(name="frontend.ui", aliases=["ui"]),
        ],
        strict=True,
    )
    service = DomainService(config)

    # Canonical check
    assert service.is_defined("backend.auth")
    assert service.is_canonical("backend.auth")

    # Alias check
    assert service.is_defined("login")
    assert service.is_alias("login")
    assert service.get_canonical("login") == "backend.auth"

    assert service.is_defined("auth")
    assert service.get_canonical("auth") == "backend.auth"

    # Unknown check
    assert not service.is_defined("random")

    # Normalize
    assert service.normalize("login") == "backend.auth"
    assert service.normalize("backend.auth") == "backend.auth"
    assert service.normalize("unknown") == "unknown"
