# Mandatory Demo Flow=

This explains exactly what happens, step by step, when someone uses the
platform to run a real conference — from setting up the event, venue and
speakers, through an attendee registering, buying a ticket, attending, and
walking away with a certificate — including the background things (emails,
live check-in counts, generated files) that happen automatically without
anyone clicking a separate button for them.

---

## 1. Register

Before anything else can happen, people need accounts. Here's how each type
of account actually gets created:

- The very first account, the **Admin**, is created automatically the
  moment the app starts — nobody has to sign it up.
- The Admin then creates an **Event Organizer** account for someone who's
  actually going to run a real conference.
- That Event Organizer can create their own **Staff** accounts — the people
  who'll actually work the event in person, checking people in at the door.
- The Event Organizer also registers **Speaker** accounts — matching how a
  real conference works, where the organizer reaches out and books a
  speaker, rather than a speaker showing up and signing themselves up.
- An **Attendee** signs themselves up directly, with no login needed at
  all — exactly like creating your own account on Eventbrite.



---

## 2. Create Event

The Event Organizer sets up the actual conference — name, type, start and
end dates, when registration opens and closes, and how many people it can
hold overall.

**What's checked automatically:** the end date genuinely has to be after
the start date. Registration can't be set to close after the event has
already started. The event begins as a private "Draft" — it only becomes
something people can actually see and register for once the organizer
explicitly publishes it and opens registration.

---

## 3. Add Venue

Someone lists a real physical location — name, address, city, and how many
people it can hold overall. A big venue might later have several rooms
inside it.

**What's genuinely flexible here:** both the Admin and the Event Organizer
can add a venue — there's no unnecessary bottleneck where an organizer has
to wait on someone else just to register a one-off location they're only
using once.

---

## 4. Add Speaker

The Event Organizer registers a real person who's agreed to speak — their
bio, area of expertise, company, and years of experience.

**What's checked automatically, later on when this speaker actually gets
assigned to a talk:** a speaker can be temporarily marked unavailable for
new bookings (separate from their login account still working normally),
and a speaker who's genuinely marked unavailable simply can't be assigned
to a new session at all.

---

## 5. Create Sessions

The organizer schedules the actual talks — a specific title, in a specific
room, given by a specific speaker, at a specific time.

**A real amount of checking happens automatically here:** the session's own
timing has to genuinely fall within the event's overall dates — you can't
schedule a talk for a day the conference isn't even running. The room can't
already have a different talk scheduled at an overlapping time. And the
same speaker can't be double-booked into 2 overlapping talks either, even
across different rooms.

---

## 6. Open Registration

The organizer flips the event's status forward, moving it from "Published"
to "Registration Open" — the actual signal that real people can now start
signing up.

---

## 7. Register Attendee

The attendee commits to attending this specific event.

**What's checked automatically:** the same person can't register twice for
the same event — trying to do so is rejected outright. The event has to
genuinely still have room — once it's full, no more registrations are
accepted. And registration is only allowed while the event's own
registration window is actually open; too early or too late, and it's
rejected.

**What happens automatically the moment registration succeeds:** a
confirmation email gets queued to send in the background, and a real
attendance record is quietly created behind the scenes, ready to be filled
in later on the actual day of the event.

---

## 8. Purchase Ticket

The attendee picks a ticket category (Standard, VIP, Early Bird, Student)
and buys one.

**What's checked automatically:** the ticket category has to genuinely
still be within its own sale window — an expired or not-yet-open category
can't be purchased. There have to genuinely be enough tickets left in that
category. The moment a purchase is made, that quantity gets set aside
immediately, so 2 different people can't both successfully buy the very
last remaining ticket at the same moment.

---

## 9. Payment

The attendee pays for the ticket they just picked. This genuinely happens
in 2 real steps, worth understanding clearly:

**Step one** — the payment gets recorded, but only in a "pending" state, not
yet treated as successful.

**Step two** — the payment gets explicitly confirmed, one way or the other.
If it's confirmed as successful, several things cascade automatically all
at once: the payment itself flips to "Success," the ticket purchase flips
to "Confirmed," and the attendee's whole registration flips to "Confirmed"
too. A real PDF ticket gets generated on the spot, a real QR code image
gets created (encoding this attendee's own registration, ready to be
scanned later at check-in), and both a payment confirmation email and a
ticket confirmation email get queued to send, with that PDF attached.

**If it's instead confirmed as failed**, none of that happens — the
purchase and registration stay exactly where they were, and importantly,
the ticket quantity that was set aside earlier gets released back,
genuinely making that ticket available for someone else to buy again.

**What's also checked automatically:** the same payment transaction
reference can never be used twice, and the amount charged always comes
from the purchase's own real total — never something the client could type
in themselves.

---

## 10. Book Session

The now-confirmed attendee reserves a seat at one specific talk they're
interested in.

**What's checked automatically:** only an attendee whose overall
registration has genuinely reached "Confirmed" can book a session at
all — someone who registered but never actually paid can't reserve seats.
The session can't be booked past its own capacity. And the same attendee
can't book the same session twice.

---

## 11. Check-In

On the actual day of the event, the attendee shows up and gets checked in —
in one of 2 genuinely different ways.

**The direct way:** a staff member already knows (or looks up) the
attendee's registration, and manually marks them checked in right there.

**The QR way:** the attendee shows the QR code they received earlier (in
their ticket confirmation email, or from their own account). Staff scans
or uploads that image, the system decodes it, figures out exactly which
registration it belongs to, and performs the same check-in automatically —
no manual lookup needed at all.

**What's checked automatically, either way:** only a genuinely confirmed
registration can be checked in. And the same attendee can't be checked in
twice — trying again just tells you they've already arrived.

**What else happens automatically, for anyone watching:** a live, running
count of how many attendees have checked in so far updates instantly for
anyone with that specific event's check-in screen open — like watching a
live scoreboard, not a page you have to keep refreshing.

---

## 12. Attend Event

This step isn't a separate action by itself — it's genuinely represented by
everything already covered: a confirmed registration, a completed check-in,
and optionally, having reserved seats at specific sessions along the way.
By this point, the attendee has a complete, real record of having actually
shown up.

---

## 13. Feedback

The attendee shares their experience — rating the event overall, and
optionally, a specific speaker or a specific session they particularly
enjoyed (or didn't).

**What's checked automatically:** only someone who genuinely checked in can
leave feedback at all — you can't rate an event you never actually
attended. And you can't submit feedback twice for the exact same
thing — one honest rating per event, per speaker, per session.

---

## 14. Generate Certificate

The organizer (or Admin) issues a real certificate for the attendee.

**What's checked automatically:** a certificate can only be generated for
someone who genuinely checked in — attendance is the real, honest
requirement here, not just having registered or paid.

**What happens automatically the moment it's generated:** a real, unique
certificate number gets assigned, a genuine PDF certificate gets created on
the spot with the attendee's name and the event's details, and an email
letting them know it's ready goes out, with that PDF attached.

---

## The Big Picture

```
Register (Admin -> Organizer -> Staff/Speaker, Attendee self-serve)
   -> Create Event (dates validated)
   -> Add Venue (hall capacity checked against venue capacity)
   -> Add Speaker (availability tracked separately from login access)
   -> Create Sessions (event-timing, hall overlap, and speaker overlap all checked)
   -> Open Registration (event status moved forward)
   -> Register Attendee (duplicate-blocked, capacity-checked, window-checked)
   -> Purchase Ticket (sale window checked, quantity reserved immediately)
   -> Payment (2-step: pending, then confirmed success or failure,
              cascading to confirm the purchase and registration together)
   -> Book Session (confirmed-only, capacity-checked, duplicate-blocked)
   -> Check-In (manual or real QR scanning, duplicate-blocked, live count updates)
   -> Attend Event (represented by the confirmed, checked-in record itself)
   -> Feedback (checked-in-only, one rating per target)
   -> Generate Certificate (attendance-gated, real PDF generated and emailed)
```

Every step that changes something important — a ticket's remaining
quantity, a registration's confirmed status, a speaker's availability —
happens automatically, as a direct result of the action taken. Nobody has
to do the math by hand, remember to send a notification, or manually check
whether a room or speaker is double-booked. The system keeps everything
accurate and connected on its own, from the very first venue listing all
the way through to a checked-in attendee walking away with a certificate.