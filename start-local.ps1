# start-local.ps1
# Starts Cloud SQL Proxy and Flask app together

# Change this if you used a different port
$PORT = 3306

# Start Cloud SQL Proxy in a new background process
Start-Process powershell -ArgumentList "-NoExit", "-Command `".\cloud-sql-proxy.exe --port $PORT friendaligner:us-east4:friend-aligner --credentials-file=proxy-key.json`""

# Give the proxy a few seconds to start
Start-Sleep -Seconds 5

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Start Flask app
flask run
