from flask import Flask, render_template, request
from transformers import pipeline
from dotenv import load_dotenv, find_dotenv
import os
from pymongo import MongoClient
from pytrends.request import TrendReq
import logging
import openai
from werkzeug.utils import secure_filename

load_dotenv(find_dotenv())

app = Flask(__name__)
# Set the OpenAI API key


app.config['MONGO_URI'] = 'mongodb+srv://username:passwordcluster0.vsrdrs2.mongodb.net/'

try:
    client = MongoClient('mongodb+srv://pranesh:Database24@cluster0.vsrdrs2.mongodb.net/')
except:
    print("cannot Connect")
db = client['Gureka']
users_collection = db['Datas']


app.config['UPLOAD_FOLDER'] = 'upload'
# Load the text generation pipeline


@app.route('/')
def rout():
    return render_template('login.html')


@app.route('/user', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')  # You should hash the password before storing it
    # Insert the new user into the database
    users_collection.insert_one({'email': email, 'password': password})
    return render_template('user.html')


# Set the OpenAI API key
openai.api_key = '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'

# Define the route for the index page
@app.route('/index', methods=['GET', 'POST'])
def home():
    generated_text = " "
    if request.method == 'POST':
        user_message = request.form['prompt']
        
        # Process the message with OpenAI's API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ]
        )
        
        # For now, we'll just echo the message back to the user
        generated_text = response.choices[0].message['content']
 
    return render_template("index.html", generated_text=generated_text)


@app.route('/home')
def index():
    return render_template('home.html')


@app.route('/upload', methods=['GET','POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file selected."
    
    file = request.files['file']
    if file.filename == '':
        return "No file selected."

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Ensure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    file.save(file_path)

    if os.path.exists(file_path):
        text = img2text(file_path)
        return render_template('result.html', text=text)
    else:
        return "File not saved correctly."

def img2text(image_path):
    pipe = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")
    text = pipe(image_path)[0]['generated_text']
    return text



@app.route('/keyindex', methods=['GET', 'POST'])
def search_by_country():
    if request.method == 'POST':
        country = request.form['country'].upper()  # Ensure country code is uppercase
        keyword = request.form['keyword']
        
        # Check if country code and keyword are provided
        if not country or not keyword:
            return "Please enter both a country code and a keyword."
        
        pytrend = TrendReq()
        
        try:
            # Build payload with the provided keyword and country
            pytrend.build_payload(kw_list=[keyword], geo=country)
            
            # Fetch interest by region data
            data = pytrend.interest_by_region()
            
            # Select top regions
            top_data = data.head(30).reset_index()
            
            # Render the HTML template with data
            return render_template('key_index.html', top_data=top_data.values.tolist(), search_keyword=keyword)
        except Exception as e:
            logging.exception("An error occurred while fetching data from Google Trends.")
            return f"An error occurred: {e}"
    else:
        # Render the HTML template without data
        return render_template('key_index.html')

if __name__ == '__main__':
    app.run(debug=True)









"""from flask import Flask, render_template, request
from io import BytesIO
import base64
from pytrends.request import TrendReq
import matplotlib.pyplot as plt
import pandas as pd

app = Flask(__name__)

@app.route('/Keyindex', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Retrieve keyword from form submission
        keyword = request.form['keyword']
        
        # Initialize pytrends request
        pytrend = TrendReq()
        
        # Build payload with the provided keyword
        pytrend.build_payload(kw_list=[keyword])
        
        # Fetch interest by region data
        data = pytrend.interest_by_region()
        
        # Select top 20 regions
        top_data = data.head(20).reset_index()
        
        # Generate the plot
        fig, ax = plt.subplots(figsize=(120, 10))
        top_data.plot(x='geoName', y=keyword, kind='bar', ax=ax)
        
        # Convert plot to PNG image
        img = BytesIO()
        plt.savefig(img, format='png')
        plt.close()
        img.seek(0)
        
        # Encode PNG image to base64 string
        plot_url = base64.b64encode(img.getvalue()).decode('utf8')

        # Render the HTML template with data
        return render_template('inde.html', top_data=top_data.values.tolist(), search_keyword=keyword, plot_url=plot_url)
    else:
        # Render the HTML template without data
        return render_template('inde.html')

# Additional functionalities
@app.route('/trending_searches', methods=['GET'])
def trending_searches():
    pytrend = TrendReq()
    data = pytrend.trending_searches(pn="india")
    return render_template('trending_searches.html', data=data)

@app.route('/top_charts', methods=['GET'])
def top_charts():
    pytrend = TrendReq()
    data = pytrend.top_charts(2020, hl='en-US', tz=300, geo='GLOBAL')
    return render_template('top_charts.html', data=data)

@app.route('/suggestions', methods=['GET', 'POST'])
def suggestions():
    if request.method == 'POST':
        keyword = request.form['keyword']
        pytrend = TrendReq()
        suggestions = pytrend.suggestions(keyword=keyword)
        data = pd.DataFrame(suggestions).drop(columns='mid')
        return render_template('suggestions.html', data=data)
    else:
        return render_template('suggestions.html')

@app.route('/related_queries', methods=['GET', 'POST'])
def related_queries():
    if request.method == 'POST':
        keyword = request.form['keyword']
        pytrend = TrendReq()
        pytrend.build_payload(kw_list=[keyword])
        queries = pytrend.related_queries()
        values = queries.values()
        return render_template('related_queries.html', data=values)
    else:
        return render_template('related_queries.html')

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
"""
