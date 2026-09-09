"""Organization models.

Organizations are created in Cyclos as users belonging to a configured business,
corporate or merchant group. This module provides organization-specific aliases.
"""

from __future__ import annotations

from angstrom_cyclos.members.models import Member as Organization
from angstrom_cyclos.members.models import MemberBase as OrganizationBase
from angstrom_cyclos.members.models import (
    MemberRegistrationResult as OrganizationRegistrationResult,
)

__all__ = [
    "Organization",
    "OrganizationBase",
    "OrganizationRegistrationResult",
]
