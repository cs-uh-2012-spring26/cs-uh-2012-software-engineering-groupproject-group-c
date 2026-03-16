# Requirements Document for Fitness Class Management System

## 1. Requirements Elicitation and Analysis

**Meeting Date:** February 10, 2026

**Elicitation Techniques Used:**

* **Structured Interview / Q&A:** We conducted a direct question-and-answer session with the client to define the exact scope and user permissions for Sprint 1. By asking targeted questions, we successfully identified the four distinct actors (Guest, Member, Trainer, Admin) and mapped out their specific privileges (e.g., Guests can only browse classes, Members can book, while Trainers and Admins manage classes and view rosters).
* **Constraint Analysis & Scope Bounding:** We intentionally asked about advanced features like password recovery, payment gateways, cancellations, and filtering/sorting. The client clarified that these are out of scope for this sprint. This technique was vital for explicitly bounding our work strictly to backend REST API development without a frontend interface.
* **Use Cases & UML Diagramming (Post-Meeting):** Following the meeting, we synthesized the rough notes into a formal UML use case diagram and fleshed out detailed written use cases. This translation from raw client answers to standardized technical specifications helped us validate that no logical gaps existed in the booking flow.

**Reflections:**

* **Utility of Techniques:** The structured interview was highly effective for preventing feature creep. By explicitly asking about edge case, we learned that bookings are final and limitless for this sprint. Without these direct questions, we likely would have wasted development time over-engineering a cancellation endpoint, payment system, or email verification flow.
* **Important Clarifications Gained:** * **Class Scheduling & Capacity:** A critical clarification was that while class times are permitted to overlap in the system, the trainer must have the authority to set a strict, custom capacity limit for each individual session. 
    * **Authentication Requirements:** We learned that while the system demands a strong password during registration (requiring uppercase, lowercase, and numbers), we do not need to implement an email verification step or a "forgot password" flow. 
    * **System Feedback:** We clarified that the system does not require automated SMS/email notifications upon booking; a simple "booking successful" API response is sufficient for the user experience in this iteration.

## 2. Requirements Specification

### 2.1 Use Case Diagram

![Use Case Diagram](S2_UML.png)


### 2.2 Use Cases

---
### Actors
- Member
- Guest
- Admin/Trainer (They come under the same rule & have equal roles so we will just refer to them both as 'Trainer' in our use cases for now)
---

### Feature 1: Create Class

---

**Use Case Name:** Create Class

**Actor:** Trainer

**Preconditions:** The trainer must be authenticated with a valid session/token and hold either a "Trainer" or "Admin" role.

**Main Success Scenario:**

1. The trainer sends a request to create a new fitness class, including their authorization token in the request header.
2. The system validates the authorization token to ensure the trainer is logged in (Authentication Check).
3. The system inspects the token's payload to verify the user possesses either the "Trainer" or "Admin" role (Authorization Check).
4. The trainer provides the required class details: name, instructor, schedule, capacity, location, and an optional description.
5. The system validates the input, ensuring no required fields are blank and the capacity is a positive integer.
6. The system successfully saves the new fitness class to the database.
7. The system returns a 201 Created status code and the JSON payload of the newly created class.

**Alternative Flows:**

* **2a/3a. Unauthorized Access:** If the authorization token is missing, expired, invalid, or the user has a "Member" role instead of trainer/admin, the system aborts the operation and returns a 401 Unauthorized or 403 Forbidden error.

* **5a. Invalid Input:** If mandatory fields are missing or the capacity is not a positive integer, the system aborts the operation and returns a 400 Bad Request error detailing the specific missing or invalid fields.

**Postconditions:**

* A new fitness class is successfully stored in the system and is immediately available for viewing and booking.

---

### Feature 2: View Class List

---

**Use Case Name:** View Classes

**Actor:** User (can be guest, member, or trainer)

**Preconditions:** None for guest. Must be logged in and authenticated with the assigned role for member/trainer

**Main Success Scenario:**

1. The user requests to see a list of upcoming fitness classes so they can decide what to book.
2. The system retrieves all scheduled fitness classes from the database.
3. The system filters out sensitive internal data (such as the list of specific members who have booked the class) from the output payload.
4. The system returns a 200 OK status code and displays the filtered list of classes to the user.

**Alternative Flows:**

* **2a. No Classes Available:** If there are no fitness classes currently scheduled in the database, the system returns a 200 OK status code with an empty list.

**Postconditions:**

* The user successfully receives a list of all current fitness classes. The database state remains unchanged.

---

### Feature 3: Book a Class

---

**Use Case Name:** Book Classes

**Actor:** Member

**Preconditions:** The user must be authenticated with a valid session/token and hold the "Member" role. The requested class must exist in the system.

**Main Success Scenario:**

1. The Member requests to book a spot in a specific fitness class using the class ID, passing their authorization token in the request header.
2. The system validates the authorization token to confirm the user's identity (Authentication Check).
3. The system checks the user's role in the token to verify they are a "Member" (Authorization Check).
4. The system queries the database to ensure the requested class exists and checks that it has available capacity (spots remaining > 0).
5. The system adds the Member's email/ID to the class's booked_members list and updates the enrollment count.
6. The system returns a 200 OK status code along with a success message, the class ID, the new enrolled count, and the total capacity.

**Alternative Flows:**

* **2a/3a. Unauthorized Role:** If the token is invalid/missing (401 Unauthorized), or if a guest or Staff member (Admin/Trainer) attempts to book a class, the system aborts and returns a 403 Forbidden error stating only members can book.

* **4a. Class Not Found:** If the provided class ID does not match any existing class in the database, the system aborts and returns a 404 Not Found error.

* **4b. Class Full or Already Booked:** If the class has reached maximum capacity or the member is already in the booked_members list, the system aborts and returns a 400 Bad Request error.

**Postconditions:**

* The Member is successfully registered for the specific fitness class, and the enrolled count for that class is incremented by one in the database.

---

### Feature 4: View Member List of a class

---

**Use Case Name:** View Member List

**Actor:** Trainer

**Preconditions:** The user must be authenticated with a valid session/token and hold either a "Trainer" or "Admin" role.

**Main Success Scenario:**

1. The trainer requests to view the roster of members booked for a specific class using the class ID, including their authorization token in the request header.
2. The system validates the token to ensure the user is securely logged in (Authentication Check).
3. The system inspects the token payload to verify the user has the "Trainer" or "Admin" role (Authorization Check).
4. The system queries the database to confirm the class ID exists.
5. The system retrieves the booked members list associated with that class.
6. The system returns a 200 OK status code, displaying the total number of enrolled members along with their specific details (e.g., emails/names).

**Alternative Flows:**

* **2a/3a. Unauthorized Access:** If the token is missing/invalid (401 Unauthorized) or if a Member or Guest attempts to access this endpoint, the system aborts the operation and returns a 403 Forbidden error.

* **4a. Class Not Found:** If the provided class ID does not map to an existing fitness class, the system aborts the operation and returns a 404 Not Found error.

**Postconditions:**

* The trainer successfully receives the list of members enrolled in the specified class. The database state remains unchanged.

---

### Feature 5: Send Class Reminders

---

**Use Case Name:** Send reminder emails

**Actor:** Trainer

**Preconditions:** The trainer must be authenticated with a valid session/token and hold either a "Trainer" or "Admin" role. The requested fitness class must exist in the system.

**Main Success Scenario:**

1. The trainer requests to send reminder emails to all members booked for a specific class using the class ID, including their authorization token in the request header.
2. The system validates the authorization token to ensure the trainer is securely logged in (Authentication Check).
3. The system inspects the token payload to verify the user possesses either the "Trainer" or "Admin" role (Authorization Check).
4. The system queries the database to confirm the class ID exists and retrieves the class details (name, instructor, schedule, location, description).
5. The system retrieves the booked_members list containing the enrolled users' email addresses.
6. The system constructs and successfully dispatches an email containing the full class details to each booked member via the external email service.
7. The system returns a 200 OK status code along with a JSON payload summarizing the number of successfully sent emails and any failures.

**Alternative Flows:**

* **2a/3a. Unauthorized Access:** If the authorization token is missing/invalid (401 Unauthorized), or if a Member or Guest attempts to trigger the reminders, the system aborts the operation and returns a 403 Forbidden error.

* **4a. Class Not Found:** If the provided class ID does not map to an existing fitness class in the database, the system aborts and returns a 404 Not Found error.

* **5a. No Booked Members:** If the class exists but has no members enrolled, the system returns a 200 OK status code with a message indicating that there are no members to remind, without attempting to send any emails.

* **6a. Partial Email Failure:** If the system fails to send an email to a specific member (e.g., due to an SMTP or third-party service error), it logs the failure, continues sending emails to the remaining members in the list, and includes the failed email addresses in the final response payload.

**Postconditions:**

* Reminder emails are successfully dispatched to the enrolled members. The database state remains completely unchanged.
