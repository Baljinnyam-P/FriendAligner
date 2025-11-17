from flask import Flask, url_for, request, render_template, redirect
from dotenv import load_dotenv
load_dotenv()
#Here is where we call the pages. 
# pip install flask so flask works. 
# To run application: python app.py

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000, use_reloader=True)
