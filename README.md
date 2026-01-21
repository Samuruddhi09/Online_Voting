# Online Voting System

A secure, role-based **Online Voting System** built using **Flask and SQLite**, following a **backend-first and security-first approach**.  
The system supports admin-controlled elections, candidate management, secure voting with **one-vote-per-election enforcement**, and accurate result calculation.

This project demonstrates **software engineering fundamentals**, **manual testing mindset**, **data integrity**, and **real-world system logic**.

---

## Features

### User Management
- Secure user registration with:
  - Aadhaar number validation (12-digit)
  - Unique voter ID and email
- Password hashing using **PBKDF2-SHA256**
- Session-based login and logout

### Authentication & Authorization
- Role-based access control:
  - Voter
  - Admin
  - Super Admin
- Protected routes using decorators
- Super Admin protection (cannot be deleted or downgraded)

### Election & Voting System
- Admin-controlled election lifecycle:
  - Upcoming → Active → Closed
- Candidate management with strict rules:
  - Admin cannot be a candidate
  - One candidate per user per election
- Secure voting:
  - One vote per user per election
  - Voting allowed only for active elections
  - Backend + database-level enforcement

### Results & Analytics
- Dynamic vote counting (results are **not stored** to prevent tampering)
- Winner determination with tie handling
- No-votes handling
- Results visible **only after election closure**

### UI & Navigation
- Home page, voter dashboard, admin dashboard
- Bootstrap-based responsive UI
- Role-aware navigation
- Clean separation of backend logic and UI

---

## Tech Stack

| Layer | Technology |
|------|------------|
| Backend | Python (Flask) |
| Database | SQLite |
| Frontend | HTML, Bootstrap 5 |
| Authentication | Session-based |
| Security | Password hashing, role-based access |
| Version Control | Git & GitHub |

---

## System Design Principles

- Backend-first development
- Security-first approach
- No trust in frontend
- Immutable voting data
- Results derived dynamically
- Phase-wise development with clean Git commits

---

## Database Schema (Overview)

### Users
- `id`
- `full_name`
- `email` (unique)
- `password` (hashed)
- `aadhaar_number` (unique)
- `voter_id` (unique)
- `role` (voter / admin)

### Elections
- `id`
- `title`
- `description`
- `status` (upcoming / active / closed)
- `created_by`

### Candidates
- `id`
- `election_id`
- `user_id`
- `display_name`
- `party_or_description`
- **UNIQUE (election_id, user_id)**

### Votes
- `id`
- `user_id`
- `election_id`
- `candidate_id`
- `voted_at`
- **UNIQUE (user_id, election_id)**

---
## QA & Testing

Manual testing was performed for this project.

### Testing Activities:
- Created manual test cases in Excel
- Executed positive and negative scenarios
- Validated role-based access and voting rules
- Captured screenshots as execution evidence

### QA Artifacts:
- Test Cases: Online_Voting_Test_Cases.xlsx
- Screenshots: /Screenshots

This project demonstrates a practical manual QA approach.

