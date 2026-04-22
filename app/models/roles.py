from enum import Enum

class UserRole(Enum):
    ADMIN = "admin"
    TRAINER = "trainer"
    MEMBER = "member"

    @classmethod
    def values(cls):
        return [role.value for role in cls]