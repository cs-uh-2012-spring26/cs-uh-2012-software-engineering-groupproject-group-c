[![CI Testing Pipeline](https://github.com/cs-uh-2012-spring26/cs-uh-2012-software-engineering-groupproject-group-c/actions/workflows/ci.yml/badge.svg)](https://github.com/cs-uh-2012-spring26/cs-uh-2012-software-engineering-groupproject-group-c/actions/workflows/ci.yml)

# Fitness Classes API

A REST API for managing **users**, **fitness classes**, **bookings**, and sending **reminder emails**.  
Built with **Flask-RESTX**, **MongoDB**, and **JWT authentication**.  

---

## Prerequisites

- Python 3.10 or higher  
- MongoDB installed and running  
  - [MongoDB Installation Guide](https://www.mongodb.com/docs/manual/installation/)  

---

## Tech Stack

- **Flask-RESTX** — REST API framework with automatic OpenAPI/Swagger generation  
- **PyMongo** — MongoDB driver  
- **Flask-JWT-Extended** — JWT authentication  
- **pytest** — Testing framework  
- **mongomock** — Mock MongoDB for unit tests  
- **Flask-CORS** — Enable cross-origin requests  

---

## Environment Setup

(1) Make sure MongoDB is already running:

 - macOS: `brew services restart mongodb-community`
 - Linux: `sudo systemctl restart mongod`

(2) Follow the instructions in .samplenv and create a `.env` file in the project root with following variables:

```env
MONGO_URI="mongodb://localhost:27017"
DB_NAME="fitness_db"
MOCK_DB="false"
DEBUG="true"
JWT_SECRET_KEY="your-secret-key"
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=eu-north-1        # must match the region where you verified identities
SES_SENDER_EMAIL=your_verified@email.com
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

(3) Create virtual environment:

```
make dev_env
```
Run the command above and it will create virtual environment as well as install all the dependencies. 

---

## Running the Server

```
make run_local_server
```
This will run the tests first and then run the server. 
For running the server without the tests, use the command below after running `make dev_env`:

```bash
source .venv/bin/activate
FLASK_APP=app flask run --debug --host=0.0.0.0 --port 8000       
```

* Open [http://127.0.0.1:8000](http://127.0.0.1:8000) for Swagger UI
* Stop server: `Ctrl+C`

---
## Authentication in Swagger

1. Register through `POST /Authentication/register`
2. Login through `POST /Authentication/login` to receive `access_token`
3. Copy the `access_token` from the login response
4. Click the **Authorize** button at the top of Swagger
5. In the "Bearer" field, enter: `Bearer <your_token>` (type the word Bearer followed by a space, then paste your token)
6. Click **Authorize** then **Close**

---

## Email Reminder Feature Setup (Feature 5)

This feature uses AWS Simple Email Service (SES) to send reminder emails to members booked in a fitness class.

### Prerequisites

1. An AWS account with SES access
2. Verified email identities in AWS SES

### Step 1: Verify Email Addresses in AWS SES

Since SES is in sandbox mode, both the sender and recipient emails must be verified.

1. Go to [AWS SES Console](https://console.aws.amazon.com/ses)
2. Make sure your region matches `AWS_REGION` in your `.env`
3. Go to **Configuration → Identities → Create Identity**
4. Select **Email address**, enter the email, click **Create Identity**
5. Check the inbox and click the verification link AWS sends
6. Repeat for all trainer/admin sender emails and member recipient emails you plan to test with.
7. Select the email address you want to send reminders from (must be verified) and set it as SES_SENDER_EMAIL in .env.
8. Select the AWS SES region where that verified email identity exists and set it as AWS_SES_REGION in .env.

### Step 2: Create AWS Access Keys

1. Go to AWS Console → click your name (top right) → **Security Credentials**
2. Scroll to **Access Keys** → **Create Access Key**
3. Copy the `Access Key ID` and `Secret Access Key` into .env as AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY respectively.


### Step 3: Configure Environment Variables

Add the following to your `.env` file:
```
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=eu-north-1        # must match the region where you verified identities
SES_SENDER_EMAIL=your_verified@email.com
```

### Step 4: Send Reminders

Call the remind endpoint as a trainer or admin:
```
POST /classes/<class_id>/remind
```

### Note on Sandbox Mode

Sandbox mode restricts sending emails to only verified addresses.


## Notification Preferences Feature (Feature 7)

This feature allows users to choose how they receive reminders: via email and/or Telegram.

### Email Notifications
Email notifications use AWS SES. Follow the Email Reminder Feature Setup section above.

### Telegram Notifications

#### Step 1: Create a Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the instructions
3. Copy the bot token provided

#### Step 2: Get Your Chat ID
1. Start a conversation with your bot on Telegram
2. Either:
   - Message `@myidbot` on Telegram and send `/getid`
   - Or visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` after messaging your bot and find `"chat":{"id":...}`

#### Step 3: Configure Environment Variables
Add to your `.env` file:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

#### Step 4: Register with Notification Preferences
When registering, optionally include your preferred notification channels and Telegram chat ID:
```json
POST /Authentication/register
{
  "username": "Ahmed",
  "email": "ahmed@gmail.com",
  "password": "Ahmed@123",
  "phone": "1234567890",
  "role": "member",
  "notification_preferences": ["email", "telegram"],
  "telegram_chat_id": "your_chat_id"
}
```
If `notification_preferences` is not provided, it defaults to `["email"]`.

#### Step 5: Update Preferences After Registration
```json
PATCH /Authentication/preferences
{
  "notification_preferences": ["email", "telegram"],
  "telegram_chat_id": "your_chat_id"
}
```
Requires a valid JWT token. Allowed channels: `email`, `telegram`.

#### Step 6: Receive Notifications
When a trainer sends reminders via `POST /classes/<class_id>/send-reminder`,
notifications are dispatched to each member based on their saved preferences.
Members on `["email"]` receive only emails. Members on `["email", "telegram"]`
receive both. The system records any failed dispatches without
interrupting other notifications.

#### Note on Telegram Access
The server must have access to `api.telegram.org` to send Telegram messages.
If running in a restricted network, configure a proxy before starting the server.

#### Note on Development Environment
This feature was developed in a region where Telegram is restricted (Pakistan). 
As a result, end-to-end Telegram testing was performed using unit tests with mocked 
API calls rather than live integration tests. The implementation has been verified to 
correctly construct and send the API request to Telegram's Bot API — the unit tests 
confirm the correct `chat_id`, message format, and token usage. Full end-to-end 
testing can be performed in an unrestricted network environment by following the 
setup steps above.

---

## Recurring Classes & Per-Occurrence Bookings (Feature 6)

Classes can optionally be made **recurring** (daily or weekly). Each occurrence of a recurring class has its own independent capacity and member list. Non-recurring classes work the same way — they simply have a single occurrence equal to their schedule date.

### How It Works

Every class (recurring or not) uses an `occurrence_date` to identify a specific session. When you call `GET /classes/`, recurring classes are expanded into one entry per occurrence, each with its own `enrolled` count. Use the `occurrence_date` value from that listing when booking, viewing members, or sending reminders.

### Creating a Recurring Class

```
POST /classes/
Auth: Trainer or Admin
```

Add a `recurrence` object to the standard class payload (remove this object to make class non-recurring and have just a single instance of a class):

```json
{
  "name": "Morning Yoga",
  "instructor": "Jane",
  "schedule": "2027-06-01T08:00",
  "capacity": 20,
  "location": "Studio A",
  "description": "Daily morning flow",
  "recurrence": {
    "frequency": "daily",
    "total_occurrences": 5
  }
}
```

**Recurrence options:**

| Field               | Required | Description                                                      |
|---------------------|----------|------------------------------------------------------------------|
| `frequency`         | Yes      | `"daily"` or `"weekly"`                                          |
| `days_of_week`      | Weekly   | List of day names, e.g. `["monday", "wednesday"]`                |
| `end_date`          | One of   | ISO 8601 end date — provide this **or** `total_occurrences`      |
| `total_occurrences` | One of   | Number of occurrences — provide this **or** `end_date`           |

### Viewing Classes

```
GET /classes/
Auth: None (public)
```

Returns a flat list. Each entry has:
- `occurrence_date` — the specific session datetime
- `enrolled` — how many members have booked that session
- `capacity` — maximum spots for that session

Recurring classes produce multiple entries (one per occurrence). Non-recurring classes produce one entry where `occurrence_date` equals the schedule.

### Booking a Specific Occurrence

```
POST /classes/<class_id>/book
Auth: Member
```

**Body (always required):**
```json
{
  "occurrence_date": "2027-06-01T08:00:00"
}
```

Copy the `occurrence_date` value from the `GET /classes/` listing. Each occurrence has independent capacity — booking one session full does **not** block other sessions.

### Viewing Members for an Occurrence

```
POST /classes/<class_id>/members
Auth: Trainer or Admin
```

**Body (optional):**
```json
{
  "occurrence_date": "2027-06-01T08:00:00"
}
```

- With `occurrence_date`: returns only members booked for that session.
- Without it: returns all members across all occurrences (deduplicated).

### Updating Recurrence

```
PATCH /classes/<class_id>/recurrence
Auth: Trainer or Admin
```

**Body:**
```json
{
  "frequency": "weekly",
  "days_of_week": ["tuesday", "thursday"],
  "total_occurrences": 8
}
```

Applies to future occurrences only. Existing bookings are preserved.

### Sending Occurrence-Scoped Reminders

```
POST /classes/<class_id>/send-reminder
Auth: Trainer or Admin
```

**Body (optional):**
```json
{
  "occurrence_date": "2027-06-01T08:00:00"
}
```

- With `occurrence_date`: sends reminders only to members booked for that session.
- Without it: sends reminders to all booked members across all occurrences.

---

## Running Tests

### Setup
Make sure your virtual environment is active and dependencies are installed

### Run All Tests
```bash
make tests
```
You can see a visual report by viewing /htmlcov/index.html

## Endpoints

### Authentication

| Method | Endpoint     | Auth | Description                                  |
| ------ | ------------ | ---- | -------------------------------------------- |
| POST   | `/register`  | None | Register a new user (Admin, Member, Trainer) |
| POST   | `/login`     | None | Login and receive JWT token                  |
| PATCH  |`/preferences`|Member| Update notification channel preferences      |

**Password policy:** ≥8 characters, at least one uppercase, one lowercase, one digit.

---


### Classes

| Method | Endpoint                            | Auth          | Description                          |
| ------ | ----------------------------------- | ------------- | ------------------------------------ |
| GET    | `/classes/`                         | None          | List all classes with occurrences    |
| POST   | `/classes/`                         | Trainer/Admin | Create a class (optionally recurring)|
| POST   | `/classes/<class_id>/book`          | Member        | Book a specific occurrence           |
| POST   | `/classes/<class_id>/members`       | Trainer/Admin | View booked members (by occurrence)  |
| PATCH  | `/classes/<class_id>/recurrence`    | Trainer/Admin | Update recurrence rule               |
| POST   | `/classes/<class_id>/send-reminder` | Trainer/Admin | Send reminders (by occurrence)       |



## Workflow Example

1. Register as a **Member** or **Trainer/Admin**
2. Login → copy the JWT token
3. Authorize in Swagger using `Bearer <JWT>`
4. Create a class (Trainer/Admin) → `POST /classes/` (optionally with `recurrence`)
5. List classes (anyone) → `GET /classes/` — note the `occurrence_date` values
6. Book a session (Member) → `POST /classes/<class_id>/book` with `{"occurrence_date": "..."}`
7. View booked members (Trainer/Admin) → `POST /classes/<class_id>/members`
8. Send reminders (Trainer/Admin) → `POST /classes/<class_id>/send-reminder`

---



### Test Structure

| Test File                       | What it covers                                             |
|---------------------------------|------------------------------------------------------------|
| `test_auth.py`                  | Register and login endpoints                               |
| `test_bookings.py`              | Class booking logic (non-recurring with occurrence_date)   |
| `test_classes.py`               | Class creation, public listing, and member viewing         |
| `test_recurring_classes.py`     | Recurring class creation, per-occurrence booking & members |
| `test_recurrence.py`            | Recurrence model validation and occurrence generation      |
| `test_reminders.py`             | Reminder endpoint (non-recurring and occurrence-scoped)    |
| `test_config.py`                | App configuration                                          |
| `test_db_utils.py`              | Database utility functions                                 |
| `test_notification_channels.py` | EmailChannel and TelegramChannel unit tests                |
| `test_notification_service.py`  | NotificationService dispatch logic                         |
| `test_preferences.py`           | Notification preferences endpoint and registration         |

### Testing Notes

- Tests use **mongomock** - no real MongoDB connection needed
- Tests use **mocked email service** - no real emails are sent during testing
- All AWS SES calls are mocked, so no AWS credentials are needed to run tests
- Test files are located in `tests/unit/`
- Tests use **mocked Telegram API** - no real Telegram messages are sent during testing
---

# Running with Docker

## Prerequisites

**1. Docker Desktop must be downloaded and running before using any docker commands.**

- Download: https://www.docker.com/products/docker-desktop
- Start Docker Desktop 
- Verify: `docker --version && docker ps`

**2. A `.env` file in the project root should be created with the following variables:**

```env
MONGO_URI="mongodb://localhost:27017"
DB_NAME="fitness_db"
MOCK_DB="false"
DEBUG="true"
JWT_SECRET_KEY="your-secret-key"
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=eu-north-1        # must match the region where you verified identities
SES_SENDER_EMAIL=your_verified@email.com
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

## Quick Start

```bash
docker compose up
```

Open http://localhost:8000 for Swagger UI.

## Stop

```bash
docker compose down
```

---



## Live Deployment

The application is deployed on a DigitalOcean VM and accessible at:

http://209.38.232.149:8000

The live system is automatically redeployed and .env file is automatically created  whenever code is pushed to main and CI passes.

## Frontend Access

Once the backend server is running, the frontend interface can be accessed at:

```text
http://209.38.232.149:8000/app
```

## Virtual Environment Management

* Activate: `source .venv/bin/activate`
* Deactivate: `deactivate`



## Contributors 

- Muhammad Shahzaib Hassan
- Sadaf Habib
- Muhammad Umair Hafeez

## Additional Documentation

See `/docs/BestPractices.md` for:

* Branch naming conventions
* Testing guidelines
* Coding style recommendations

---
