
Local: 
DATABASE_URI=mysql+pymysql://root:23Baljaa1607!@127.0.0.1:3306/FriendAligner

Google Cloud:
DATABASE_URI=mysql+pymysql://Baljinnyam:123456@34.186.120.145/FriendAligner

After pulling from dev branch:
from root:
1. python -m venv .venv
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
DATABASE_URI=mysql+pymysql://<DB_USER>:<DB_PASSWORD>@127.0.0.1:3306/FriendAligner
GOOGLE_PLACES_API_KEY=your-google-places-api-key
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password


5. python run.py


# Connect to Google Cloud SQL and Run Locally

### 1. I included .env to my commit this time, running with:

python run.py (from project root) should start and connect to the google cloud sql

However, to connect to this google cloud db, you should add your current
IP address to: Google Cloud Console -> Google Cloud SQL -> Connections 
--> Networking tab -->and add your IP address in the authorized networks
section and save. 

### 2. If you want to test it on your own mysql instance locally, 
I uploaded my sql schema in the FriendAligner_v2.sql in the commit. 
You can use it to create the db locally and connect to your own
local mysql instead. (If you wanna do this, change the DATABASE_URI 
in the .env to use your local connection instead).
