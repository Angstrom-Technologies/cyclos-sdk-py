"""User models.

Users and members share the same underlying Cyclos resource. These aliases
keep the user-facing API consistent with the requested package structure.
"""

from angstrom_cyclos.members.models import (
    Member as User,
)
from angstrom_cyclos.members.models import (
    MemberBase as UserBase,
)
from angstrom_cyclos.members.models import (
    MemberCreate as UserCreate,
)
from angstrom_cyclos.members.models import (
    MemberRegistrationResult as UserRegistrationResult,
)

__all__ = ["User", "UserBase", "UserCreate", "UserRegistrationResult"]
