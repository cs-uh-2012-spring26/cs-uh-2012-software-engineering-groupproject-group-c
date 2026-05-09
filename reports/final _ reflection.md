# Final Project Reflection

## Sadaf Habib

Working on this project was honestly one of the most complete software engineering experiences I’ve had so far. It helped me connect everything we’ve learned, from backend development to deployment, into one real system that actually works end-to-end. 
I got more comfortable with Flask, JWT authentication, MongoDB design, and structuring REST APIs, especially when things got more complex with recurring classes and occurrence-based bookings. 
I also learned that small design decisions early on can really shape how smooth (or painful) later features become.

One of the parts I genuinely enjoyed was building features that felt practical, especially the notification system with AWS SES. It was satisfying to see backend logic actually trigger real messages. 
I also really liked the refactoring phase of the project. Cleaning up messy parts of the code, improving structure, and making everything more modular made the whole system feel more solid and readable. 

The hardest part was debugging issues across the system, particularly AWS SES configuration, along with collaboration challenges when integrating different team members’ work. It taught me how important communication and version control discipline are in team projects.
Overall, I feel a lot more confident working on backend systems and debugging full-stack applications. 

## Muhammad Umair Hafeez

This project gave me a clearer picture of what it actually means to build software that other people will maintain. Early on, decisions like hardcoding an email dispatch or skipping an abstraction layer feel harmless. By the time we were refactoring in Sprint 3B, I understood exactly why those decisions matter.

The part I found most satisfying was implementing Feature 7 using the Strategy Pattern. Building the abstract NotificationChannel class and then having EmailChannel and TelegramChannel slot in as concrete implementations made the design feel genuinely clean. When a trainer sends a reminder, NotificationService dispatches to whichever channels each member prefers. Adding a new channel like SMS would take one new file. Seeing that extensibility work in practice, not just as a concept from lecture, was the highlight of the project for me.

The hardest parts were designing the Telegram notification flow and keeping up with teammate changes. Getting the webhook right took more thought than I expected. The initial approach asked users to manually provide their chat_id, which the professor flagged as a poor design. Rethinking it from the user's perspective(they register with a phone number, message the bot once, share their contact, and the system handles everything else) required understanding not just what the code needed to do but what made sense for an actual person using the app. The integration side was a different kind of difficult. When a teammate merged a PR that introduced past class booking validation, test fixture dates across multiple files broke overnight. Nothing in my code changed but tests started failing, and tracking down every affected fixture taught me how much a shared codebase means your work is never fully isolated from what everyone else is doing.

Overall, I feel much more confident working across the full stack now, from writing a service layer with proper abstractions to setting up SSH keys for GitHub Actions and watching a deployment pipeline run end to end. 