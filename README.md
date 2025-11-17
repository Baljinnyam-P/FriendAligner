
After pulling from dev branch:
from root:
1. python -m venv .venv
2. 
Windows:
.venv\Scripts\activate 

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


5. python run.py


Notes: If you want to setup your own environment:
1.Own Google Cloud SQL Database:
Create Google Cloud Project-> Enable billing and Google CLoud SQL API -> Create SQL Instance-> Create Database & User -> Go to Connections, Enable public IP -> Add your IP address to authorized networks -> add to connection details to .env. 

2.SMTP config to send notifications from your own email:
Go to your Google Account, enable "App Passwords", ensure 2-factor verification, and create your "App Password". You can change .env SMTP_USER and SMTP_PASSWORD with your own email, and app password. 

3. If you want to create your own google places api key:
I enabled Places API, Geocoding API, Maps JavaScript API (for frontend) on Google Cloud. 



