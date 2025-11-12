from flask import Flask, url_for, request, render_template, redirect

#Here is where we call the pages. 
# pip install flask so flask works. 
# To run application: python app.py

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")


#Here we select the port we want to run on
if __name__ == "__main__":
    app.run(debug=True, port=5045)