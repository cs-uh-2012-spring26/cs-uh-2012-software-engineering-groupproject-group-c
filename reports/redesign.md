## Redesign Report

## Feature 6

## Feature 7 + Design Pattern 

### Design Pattern: Strategy Pattern

**Why the Strategy Pattern was chosen:**
Feature 7 requires users to choose how they receive notifications (email, Telegram, or both). The core challenge is extensibility — the system must support adding new channels (SMS, WhatsApp, Slack) in the future with minimal changes to existing code. The Strategy Pattern was the natural fit because it defines a family of interchangeable algorithms (notification channels) behind a common interface, allowing the system to select and combine them at runtime based on user preferences.

**Implementation:**

The Strategy Pattern was implemented across four new files:

1. `app/services/notification_channel.py` — Abstract base class defining the interface:
```python
class NotificationChannel(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, body: str) -> dict:
        pass

    @property
    @abstractmethod
    def channel_name(self) -> str:
        pass
```

2. `app/services/email_channel.py` — Concrete strategy wrapping existing AWS SES email:
```python
class EmailChannel(NotificationChannel):
    @property
    def channel_name(self) -> str:
        return 'email'

    def send(self, to, subject, body):
        return send_email(to, subject, body)
```

3. `app/services/telegram_channel.py` — Concrete strategy using Telegram Bot API:
```python
class TelegramChannel(NotificationChannel):
    @property
    def channel_name(self) -> str:
        return 'telegram'

    def send(self, to, subject, body):
        # sends via Telegram Bot API using chat_id as recipient
```

4. `app/services/notification_service.py` — Orchestrator that dispatches to correct channels:
```python
class NotificationService:
    def __init__(self, channels: List[NotificationChannel]):
        self.channels = {channel.channel_name: channel for channel in channels}

    def notify(self, to, subject, body, preferences, telegram_chat_id=None):
        # dispatches only to channels matching user preferences
```

**How user preferences work:**
- At registration, users can optionally specify `notification_preferences` (e.g. `['email']`, `['email', 'telegram']`) and a `telegram_chat_id`
- Preferences are stored per user in the MongoDB users collection
- After registration, users can update preferences via `PATCH /Authentication/preferences`
- When a trainer sends reminders, `send_class_reminders()` looks up each member's preferences and passes them to `NotificationService`, which dispatches only to their chosen channels

**Extensibility:**
Adding a new notification channel (e.g. SMS) requires only:
1. Creating a new class `SMSChannel(NotificationChannel)` implementing `send()` and `channel_name`
2. Registering it in `class_service.py`: `NotificationService([EmailChannel(), TelegramChannel(), SMSChannel()])`
3. Adding `'sms'` to `ALLOWED_CHANNELS` in `user_service.py`

No existing code needs to be modified — this is the open/closed principle in action alongside the Strategy Pattern.

**How `class_service.py` was refactored:**

The original hardcoded email dispatch:
```python
sent, failed = email_service.send_batch_reminders(cls)
```

Was replaced with per-member preference-aware dispatch:
```python
for member_email in members:
    prefs = users_db.get_user_preferences(member_email)
    preferences = prefs.get('notification_preferences', ['email'])
    telegram_chat_id = prefs.get('telegram_chat_id')

    results = notification_service.notify(
        to=member_email,
        subject=subject,
        body=body,
        preferences=preferences,
        telegram_chat_id=telegram_chat_id
    )
```


## Refactoring for Design Principles

1. Single Responsibility Principle (SRP) File: app/apis/classes.py | Method: SendReminders.post() - line 153 - 224

**Problem**: The original implementation of SendReminders.post() in app/apis/classes.py violated the Single Responsibility Principle (SRP) because the endpoint handled multiple unrelated concerns within one controller method.

**Fix**: To resolve this, the reminder email logic was extracted into app/services/email_service.py. A new helper function, get_class_reminder_template(class_data), was introduced to generate the reminder email subject and body, 
while send_class_reminders(class_data) was added to handle the recipient loop, email dispatch, and failure collection. The SendReminders.post() endpoint was simplified to only handle authorization, delegate the reminder processing to the service layer, and return the final API response.
This refactoring ensures that the API route is responsible only for request and response handling, while email formatting and dispatch logic are handled in separate service functions. 


2. Encapsulation / Information Hiding File: app/apis/classes.py | Method: ClassList.get() - line 84 - 89

**Problem:** The original ClassList.get() implementation violated Encapsulation because cls_db.get_all_classes() returned raw database class documents containing the internal booked_members field, and the API layer manually removed this field using pop() before returning the response. 
This meant the API route had direct knowledge of the database document’s internal structure, which should have remained hidden within the lower layers of the application.

**Fix:** To resolve this, the data filtering responsibility was moved into the service layer via the get_public_classes() function in app/services/class_service.py. 
This function retrieves raw class data through the repository and explicitly constructs a sanitized, public-facing representation containing only allowed fields (such as id, name, instructor, schedule, capacity, enrolled, location, and description).
The ClassList.get() endpoint was then simplified to directly call class_service.get_public_classes() without performing any manual data manipulation.
This refactoring ensures that internal database structure remains encapsulated within the lower layers (repository/service layer), while the API only handles returning already-processed safe data. 


3. Open/Closed Principle (OCP) File: app/apis/auth.py - line 73 and app/apis/classes.py - line 45 & 106 

**Problem**: The original implementation violated the Open/Closed Principle because user roles were hardcoded as string literals across multiple route handlers in app/apis/auth.py and app/apis/classes.py. Role checks such as if claims['role'] not in ('trainer', 'admin') were duplicated in several endpoints.
This meant that introducing a new role (e.g., “Coach”) required modifying multiple already-tested files, leading to tight coupling and a high risk of inconsistencies and errors.

**Fix:** To resolve this, role definitions were centralized into a single UserRole Enum (app/models/roles.py), providing a single source of truth for all valid roles. This removed hardcoded strings and made role management extensible and consistent across the application.
Additionally, authorization logic was extracted into a reusable @require_roles decorator (app/utils/auth_decorators.py), which standardizes role-based access control across all endpoints.
API routes were then refactored to use declarative access control (e.g., @require_roles(UserRole.ADMIN, UserRole.TRAINER)) instead of inline conditionals. The authentication layer was also updated to validate roles using UserRole.values() instead of hardcoded strings.
This refactoring makes the system open for extension but closed for modification.


4. Dependency Inversion Principle (DIP) File: app/db/classes.py | All database operation functions - e.g line 65 - 72

**Problem:** DIP states that high-level modules should not depend on low-level modules — both should depend on abstractions. In the current implementation, every function in db/classes.py is tightly coupled to the concrete global DB object (from app.db import DB). 
This creates a rigid dependency on a specific database implementation and prevents easy substitution of the database layer.

**Fix:** To resolve this, the database logic was refactored using the Repository Pattern. A ClassRepository class was introduced, and all database functions were moved into it as methods.
Instead of directly accessing the global database object, the repository now receives a db_provider through constructor injection. This removes direct dependency on concrete database implementation and introduces abstraction between service logic and data access.
The service layer interacts only with the repository instance (class_repo) rather than the database itself. This improves modularity, enables easier testing using mock databases, and allows future database replacement without modifying business logic.


5. Low Coupling File: app/apis/classes.py | Method: SendReminders.post() - line 153 - 224 | Also: app/apis/auth.py | Method: Register.post() - line 40 - 89

**Problem:** The original implementations of Register.post() in app/apis/auth.py and SendReminders.post() in app/apis/classes.py violated the Low Coupling principle because both API route handlers communicated directly with the database layer. 
Register.post() called users_db.get_user_by_email() and users_db.add_user() directly, while SendReminders.post() called cls_db.get_class_by_id() and other class-related database functions. 
This created tight dependency between the API and database modules, meaning any changes in database function names, parameters, or return structures would require immediate modifications in the route handlers.

**Fix:** To reduce coupling, an intermediate service layer was introduced to decouple the API layer from direct database access.
For user-related operations, a user_service.py layer was introduced containing register_user() and authenticate_user(). This layer handles validation, business logic, and interaction with the database.
For class-related operations, a class_service.py layer was used to handle orchestration logic such as class retrieval and reminder processing via send_class_reminders().
The API endpoints were then refactored to depend only on these service functions instead of directly calling database methods.


## Refactoring for code smells



## Task Distribution Summary

1. **Sadaf Habib:**
      - Task 1: Fixed design principle violations
      - Task 4: CI pipeline setup (GitHub Actions + Secrets, no hardcoded env vars)
      - Task 5: Updated class diagram + documentation
2. **Muhammad Shahzaib:**
      - Task 1: Fixed code smells from Sprint 3A
      - Task 2: Implemented Feature 6 (Create Recurring Classes)
3. **Umair Hafeez:**
      - Task 1: Identified and applied design patterns
      - Task 2: Implemented Feature 7 (Notifications system: Email + Telegram)
4. **Everyone:**
      - Task 3: Updated and added tests after refactoring. Ensured all tests pass and maintain ≥90% coverage


