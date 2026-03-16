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
This will run the tests first and then run the server. For running the server without the tests, use the command below:

```bash
python -m flask --app app run --debug --host=0.0.0.0 --port 8000
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

## Email Reminder Feature Setup

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
6. Repeat for every email address you want to send reminders to

### Step 2: Create AWS Access Keys

1. Go to AWS Console → click your name (top right) → **Security Credentials**
2. Scroll to **Access Keys** → **Create Access Key**
3. Copy the `Access Key ID` and `Secret Access Key`

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

The response will show which emails succeeded and which failed:
```json
{
  "message": "Reminders sent: 2 succeeded, 0 failed.",
  "sent": ["member1@email.com", "member2@email.com"],
  "failed": []
}
```

### Note on Sandbox Mode

AWS SES sandbox mode only allows sending to verified email addresses. 
To send to any email without verification, request production access  from AWS SES console → Account Dashboard → Request Production Access.



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

| Method | Endpoint    | Auth | Description                                  |
| ------ | ----------- | ---- | -------------------------------------------- |
| POST   | `/register` | None | Register a new user (Admin, Member, Trainer) |
| POST   | `/login`    | None | Login and receive JWT token                  |

**Password policy:** ≥8 characters, at least one uppercase, one lowercase, one digit.

---


### Classes

| Method | Endpoint                            | Auth          | Description               |
| ------ | ----------------------------------- | ------------- | ------------------------- |
| GET    | `/classes/`                         | None          | List all upcoming classes |
| POST   | `/classes/`                         | Trainer/Admin | Create a new class        |
| POST   | `/classes/<class_id>/book`          | Member        | Book a spot in a class    |
| GET    | `/classes/<class_id>/members`       | Trainer/Admin | View booked members       |
| POST   | `/classes/<class_id>/send-reminder` | Trainer/Admin | Send reminder emails      |



## Workflow Example

1. Register as a **Member** or **Trainer/Admin**
2. Login → copy the JWT token
3. Authorize in Swagger using `Bearer <JWT>`
4. Create a class (Trainer/Admin) → `POST /classes/`
5. Book a class (Member) → `POST /classes/<class_id>/book`
6. View booked members (Trainer/Admin) → `GET /classes/<class_id>/members`
7. Send reminders (Trainer/Admin) → `POST /classes/<class_id>/send-reminder`

---



### Test Structure

| Test File               | What it covers                              |
|-------------------------|---------------------------------------------|
| `test_auth.py`          | Register and login endpoints                |
| `test_bookings.py`      | Class booking logic                         |
| `test_classes.py`       | Class creation and member viewing           |
| `test_reminders.py`     | Email reminder endpoint and email service   |
| `test_config.py`        | App configuration                           |
| `test_db_utils.py`      | Database utility functions                  |

### Testing Notes

- Tests use **mongomock** - no real MongoDB connection needed
- Tests use **mocked email service** - no real emails are sent during testing
- All AWS SES calls are mocked, so no AWS credentials are needed to run tests
- Test files are located in `tests/unit/`

---

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
