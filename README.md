
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
DATABASE_URI=mysql+mysqlconnector://<user>:<password>@<host>:<port>/<db_name>
GOOGLE_PLACES_API_KEY=your-google-places-api-key
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_email_password

5. python run.py