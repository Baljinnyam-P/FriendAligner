**Overview**
- FriendAligner is a collaborative scheduling app that helps small groups find the best time and place to meet. It combines shared calendars, availability tracking, event discovery, invitations, and group chat—so planning together feels effortless.

**Key Features**
- **Shared Calendars:** Create personal or group calendars and keep everyone aligned on dates.
- **Availability Tracking:** Members mark availability; see aggregated views including “everyone available” slots.
- **Event Finder:** Search places (via Google Places) and turn selections into suggested or finalized events.
- **Invitations:** Send invite links or tokens; recipients can accept and join directly.
- **Notifications:** In-app updates for invites, member changes, and finalized events.
- **Reminders:** Nudge non-responders and send day-before reminders for upcoming events.
- **Admin Tools:** Organizer controls for membership, sessions, and event management.

**How It Works**
- **Organize a Group:** Create a new group and shared calendar for a specific month/year.
- **Invite Members:** Share invite links or add users by email; members can accept and join.
- **Track Availability:** Members set their availability; view combined availability to pick the best date.
- **Discover & Create:** Use the event finder to choose a venue; create a suggested or finalized event.
- **Confirm & Notify:** Finalize the event; notifications keep your group in sync.
- **Reminder:** Coordinate details and rely on reminders for follow-through.

**Tech Highlights**
- **Backend:** Flask + SQLAlchemy with JWT-based auth.
- **Database:** MySQL with normalized schema for users, groups, calendars, events, invites, chat, and notifications.
- **Integration:** Google Places API for venue data and maps links.
- **Frontend:** Responsive templates with JavaScript for interactive flows.

**Why FriendAligner**
- **Practical:** Resolves the hardest part of planning—finding a time/place everyone can do.
- **Collaborative:** Puts discovery, availability, and discussion in one place.
- **Lightweight:** Clean UI and straightforward flows that make adoption easy.



After pulling cloning from the repository:
from root:
1. python -m venv .venv  (Create python virtual environment)
2. Activate python virtual environment
Windows:
.\venv\Scripts\Activate.ps1

Windows Powershell:
.venv\Scripts\Activate.ps1

Mac:
source .venv/bin/activate

3. (Install dependencies)
pip install -r requirements.txt

4. Create .env at root:
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

DATABASE_URI=mysql+mysqlconnector://<user>:<password>@<PUBLIC_IP>/<db_name>

GOOGLE_PLACES_API_KEY=your-google-places-api-key
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

5. Create local MySQL database using the provided sql script in FrendAligner_v2.sql

6. python run.py


# Connect to Google Cloud SQL and Run Locally

### 1. I included .env to my commit this time, running with:

python run.py (from project root) should start and connect to the google cloud sql

However, to connect to this google cloud db, you should add your current
IP address to: Google Cloud Console -> Google Cloud SQL -> Connections 
--> Networking tab -->and add your IP address in the authorized networks
section and save. 


Google Cloud:
DATABASE_URI=mysql+pymysql://<USER_NAME>:<PASSWORD>@<IP_ADDRESS>/FriendAligner

### 2. If you want to test it on your own mysql instance locally, 
I uploaded my sql schema in the FriendAligner_v2.sql in the commit. 
You can use it to create the db locally and connect to your own
local mysql instead. (If you wanna do this, change the DATABASE_URI 
in the .env to use your local connection instead).

Local: 
DATABASE_URI=mysql+pymysql://<USER_NAME>:<PASSWORD>@127.0.0.1:3306/FriendAligner