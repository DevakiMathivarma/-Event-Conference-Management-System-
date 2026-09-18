# ER Diagram — Event & Conference Management System

This diagram shows all 17 tables and how they connect. GitHub renders this
automatically when viewing this file in a repository — no separate image or
tool needed. Full field lists for every table are in `app/models/` and the
Alembic migration file.

```mermaid
erDiagram
    USER ||--o| SPEAKER : "has profile"
    USER ||--o| ATTENDEE : "has profile"
    USER ||--o{ EVENT : "organizes"
    USER ||--o{ VENUE : "creates (optional)"
    USER ||--o{ SPEAKER : "registers (optional)"
    USER ||--o{ AUDIT_LOG : "performs (optional)"

    VENUE ||--o{ HALL : "contains"

    EVENT ||--o{ SESSION : "schedules"
    HALL ||--o{ SESSION : "hosts"
    SPEAKER ||--o{ SESSION : "presents (optional)"

    ATTENDEE ||--o{ REGISTRATION : "makes"
    EVENT ||--o{ REGISTRATION : "receives"

    REGISTRATION ||--o{ PURCHASE : "includes"
    TICKET ||--o{ PURCHASE : "sold as"
    EVENT ||--o{ TICKET : "offers"

    PURCHASE ||--o{ PAYMENT : "settled by"
    PURCHASE ||--o| REFUND : "may have"

    REGISTRATION ||--o{ SESSION_BOOKING : "reserves"
    SESSION ||--o{ SESSION_BOOKING : "booked via"

    REGISTRATION ||--|| CHECK_IN : "tracked by"

    REGISTRATION ||--o| CERTIFICATE : "may earn"
    ATTENDEE ||--o{ CERTIFICATE : "receives"
    EVENT ||--o{ CERTIFICATE : "issues"

    REGISTRATION ||--o{ FEEDBACK : "submits"
    EVENT ||--o{ FEEDBACK : "receives"
    SPEAKER ||--o{ FEEDBACK : "rated in (optional)"
    SESSION ||--o{ FEEDBACK : "rated in (optional)"

    USER {
        int id PK
        string full_name
        string email UK
        string phone UK
        string password_hash
        enum role
        bool is_active
    }

    EVENT {
        int id PK
        string event_name
        int organizer_id FK
        enum event_type
        datetime start_date
        datetime end_date
        datetime registration_start
        datetime registration_end
        int capacity
        enum status
    }

    VENUE {
        int id PK
        string venue_name
        string city
        int capacity
        string facilities
        enum status
        int created_by_user_id FK
    }

    HALL {
        int id PK
        int venue_id FK
        string hall_name
        int capacity
        int floor
        enum availability_status
    }

    SPEAKER {
        int id PK
        int user_id FK
        string bio
        string expertise
        string company
        int experience
        bool is_active
        int created_by_user_id FK
    }

    SESSION {
        int id PK
        int event_id FK
        int speaker_id FK
        int hall_id FK
        string title
        datetime start_time
        datetime end_time
        int capacity
        string session_type
    }

    ATTENDEE {
        int id PK
        int user_id FK
        string organization
        string designation
    }

    REGISTRATION {
        int id PK
        int attendee_id FK
        int event_id FK
        datetime registration_date
        enum registration_status
    }

    TICKET {
        int id PK
        int event_id FK
        enum ticket_type
        decimal price
        int quantity
        int available_quantity
        datetime sale_start
        datetime sale_end
    }

    PURCHASE {
        int id PK
        int registration_id FK
        int ticket_id FK
        int quantity
        decimal subtotal
        decimal discount
        decimal tax
        decimal total_amount
        enum status
    }

    PAYMENT {
        int id PK
        int purchase_id FK
        string transaction_id UK
        enum payment_method
        decimal amount
        enum payment_status
    }

    SESSION_BOOKING {
        int id PK
        int registration_id FK
        int session_id FK
        datetime booked_at
    }

    CHECK_IN {
        int id PK
        int registration_id FK "unique"
        datetime check_in_time
        datetime check_out_time
        enum check_in_method
        int checked_in_by_user_id FK
    }

    CERTIFICATE {
        int id PK
        string certificate_number UK
        int registration_id FK "unique"
        int attendee_id FK
        int event_id FK
        datetime issue_date
        enum certificate_type
        enum status
    }

    FEEDBACK {
        int id PK
        int registration_id FK
        int event_id FK
        int speaker_id FK
        int session_id FK
        int rating
        string feedback
    }

    REFUND {
        int id PK
        int purchase_id FK "unique"
        string cancellation_reason
        decimal refund_amount
        enum status
        int processed_by_user_id FK
    }

    AUDIT_LOG {
        int id PK
        int user_id FK
        string action
        string entity_type
        int entity_id
    }
```

---

## Relationships explained in plain words

- **One User can have one Speaker profile, and separately, one Attendee
  profile** — a single account only ever holds one of these, matching its
  role, but the schema itself allows both relationships from `User`.
- **One User (an Event Organizer) can organize many Events**, and optionally
  create Venues and register Speakers (both tracked by `created_by_user_id`,
  since Admin can also do both).
- **One Venue contains many Halls.**
- **One Event schedules many Sessions**; each Session belongs to exactly one
  Hall and, optionally, one Speaker (a session's speaker can be assigned
  later, so it stays nullable).
- **One Attendee makes many Registrations, one per Event** (a real database
  constraint prevents registering for the same event twice).
- **One Registration branches into several things:** one or more Purchases
  (buying tickets), any number of Session Bookings (reserving seats at
  specific talks), exactly **one** Check-In record (created the moment
  registration happens, updated — never duplicated — when the attendee
  actually arrives), at most **one** Certificate, and any number of Feedback
  submissions.
- **One Purchase branches into Payments (typically one) and at most one
  Refund** — both enforced through real database constraints where the task
  calls for "one" of something (unique transaction IDs, one refund per
  purchase).
- **Feedback deliberately allows 3 different, independent targets** — always
  tied to an Event, and optionally narrowing down to a specific Speaker or
  Session, matching the task's own "rate Event, Speaker, or Session"
  wording rather than forcing all 3 into one fixed combination every time.

## How to view this diagram

- **On GitHub:** just open this file in your repository — it renders
  automatically, no setup needed.
- **Locally, before pushing:** paste the code block above (without the triple
  backticks) into [mermaid.live](https://mermaid.live) to preview it instantly.