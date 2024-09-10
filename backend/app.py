from flask import Flask, request, jsonify, send_from_directory, render_template, redirect,session
import os
import json
import requests
import openai
import oracledb
from PyPDF2 import PdfReader
import docx2txt
import re
from docx import Document
import werkzeug.utils
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import bcrypt

app = Flask(__name__, template_folder='../frontend', static_folder='../frontend')


# Allow specific sources for stylesheets, scripts, etc.
csp = {
    'default-src': [
        "'self'",
        "https://cdnjs.cloudflare.com"
    ],
    'style-src': [
        "'self'",
        "https://cdnjs.cloudflare.com"
    ],
    'script-src': [
        "'self'",
        "https://cdnjs.cloudflare.com"
    ]
}

# Initialize Talisman with a custom CSP
Talisman(app, content_security_policy=csp)


# Rate limiting to prevent abuse
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# Set up API keys and connection details from environment variables
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key
pdfco_api_key = os.getenv("PDFCO_API_KEY")
oracle_user = os.getenv("ORACLE_USER")
oracle_password = os.getenv("ORACLE_PASSWORD")
oracle_host = os.getenv("ORACLE_HOST")
oracle_port = os.getenv("ORACLE_PORT", 1521)
oracle_service_name = os.getenv("ORACLE_SERVICE_NAME")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")


dsn_tns = oracledb.makedsn(oracle_host, oracle_port, service_name=oracle_service_name)

try:
    connection = oracledb.connect(user=oracle_user, password=oracle_password, dsn=dsn_tns)
except oracledb.DatabaseError as e:
    print(f"Database connection failed: {str(e)}")
    connection = None



@app.route('/')
#@limiter.limit("5 per minute")
def index():
    return render_template('login.html')


########################################
#Sign up Page
########################################

@app.route('/signup', methods=['POST'])
def signup():
    # Get JSON data from the request body
    data = request.get_json()

    firstname = data.get('firstname')
    lastname = data.get('lastname')
    country_code = data.get('country-code','')
    phoneno = data.get('phoneno','')
    email_id = data.get('email_id')
    password = data.get('password')

    # Combine country code and phone number
    full_phone_number = country_code + phoneno

    # Hash the password
    hashed_password = hash_password(password)

    # Insert user into the database
    try:
        connection = oracledb.connect(user=oracle_user, password=oracle_password, dsn=dsn_tns)
        cursor = connection.cursor()

        query = """
        INSERT INTO cv_users (firstname, lastname, phoneno, email_id, password)
        VALUES (:firstname, :lastname, :phoneno, :email_id, :password)
        """
        cursor.execute(query, {
            'firstname': firstname,
            'lastname': lastname,
            'phoneno': full_phone_number,
            'email_id': email_id,
            'password': hashed_password.decode('utf-8')
        })

        connection.commit()
        cursor.close()
        connection.close()

         # Return a JSON response instead of redirect
        return jsonify({"success": True}), 201

    except oracledb.DatabaseError as e:
        print(f"Database error: {str(e)}")
        return jsonify({"success": False, "message": "Error signing up"}), 500

    
@app.route('/login')
def login():
    return render_template('login.html')

# Helper function to hash passwords
def hash_password(password):
    # bcrypt will automatically generate a salt and hash the password
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed

# Check the password during login
def check_password(hashed_password, user_password):
    # Compare the stored hash with the password provided by the user
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password)

# Validate file extensions
def is_allowed_file(filename):
    ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

###################################
#LOGIN PAGE
###################################

@app.route('/login', methods=['POST'])
def login_post():
    data = request.get_json()

    email_id = data.get('username')  # Match the username field in your form with the corresponding field
    password = data.get('password')

    # Validate login credentials
    if validate_login(email_id, password):
        session['logged_in'] = True
        return jsonify({"success": True,"redirect_url": "/index.html"}), 200
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401


def validate_login(email_id, password):
    try:
        connection = oracledb.connect(user=oracle_user, password=oracle_password, dsn=dsn_tns)
        cursor = connection.cursor()

        # Fetch the stored hashed password from the database
        query = "SELECT email_id, password FROM cv_users WHERE email_id = :email_id"
        cursor.execute(query, [email_id])
        user = cursor.fetchone()

        if user is not None:
            stored_email_id, stored_password_hash = user

            # Compare the stored hashed password with the entered password
            if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
                return True
            else:
                return False
        else:
            return False

    except oracledb.DatabaseError as e:
        print(f"Database error: {str(e)}")
        return False

    finally:
        cursor.close()
        connection.close()

##########################################
#AI RESUME PARSER DASHBOARD
##########################################

@app.route('/dashboard')
def index_page():
    return render_template('index.html')


# Limit file upload size to 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

@app.before_request
def before_request():
    # Enforce HTTPS in production
    # Instead of using `ENV`, check the app's debug mode or environment variable
    if not request.is_secure and not app.debug and os.getenv('FLASK_ENV') == 'production':
        return redirect(request.url.replace("http://", "https://"))



def fetch_html_template_by_id(api_key, template_id):
    url = f"https://api.pdf.co/v1/templates/html/{template_id}"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching template by ID: {e}")
        return None

def format_document_with_pdfco(api_key, json_data, template):
    url = "https://api.pdf.co/v1/pdf/convert/from/html"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }

    json_string = json.dumps(json_data)

    payload = {
        "html": template['body'],
        "templateData": json_string,
        "outputFormat": "pdf"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        response_json = response.json()
        pdf_url = response_json['url']
        pdf_response = requests.get(pdf_url)
        pdf_response.raise_for_status()

        return pdf_response.content
    except requests.exceptions.RequestException as e:
        print(f"Error formatting document: {e}")
        return None

def process_cv_with_chatgpt(cv_text):
    prompt = (
"""Rewrite the attached resume in the following strict JSON format. Do not deviate from the structure provided:

{
  "name": "Full Name",
  "overall_summary": "Overall summary of the resume.",
  "key_skills": ["Skill 1", "Skill 2", "Skill 3"],
  "problems_they_solve": "Problems they solve.",
  "career_history": [
    {
      "organisation_name": "Name of organisation",
      "job_title": "Job title",
      "dates_employed": "Dates of employment",
      "summary_of_responsibilities": "Summary of responsibilities",
      "summary_of_achievements": [
        "Achievement 1",
        "Achievement 2"
      ]
    },
    {
      "organisation_name": "Name of organisation",
      "job_title": "Job title",
      "dates_employed": "Dates of employment",
      "summary_of_responsibilities": "Summary of responsibilities",
      "summary_of_achievements": [
        "Achievement 1",
        "Achievement 2"
      ]
    },
    {
      "organisation_name": "Name of organisation",
      "job_title": "Job title",
      "dates_employed": "Dates of employment",
      "summary_of_responsibilities": "Summary of responsibilities",
      "summary_of_achievements": [
        "Achievement 1",
        "Achievement 2"
      ]
    },
    {
      "organisation_name": "Name of organisation",
      "job_title": "Job title",
      "dates_employed": "Dates of employment",
      "summary_of_responsibilities": "Summary of responsibilities",
      "summary_of_achievements": [
        "Achievement 1",
        "Achievement 2"
      ]
    },
    {
      "organisation_name": "Name of organisation",
      "job_title": "Job title",
      "dates_employed": "Dates of employment",
      "summary_of_responsibilities": "Summary of responsibilities",
      "summary_of_achievements": [
        "Achievement 1",
        "Achievement 2"
      ]
    }
  ],
  "technologies_experience": [
    {
      "Technology_Name": "Technology name",
      "years_of_experience": "Years of experience",
      "level_of_competency": "Level of competency"
    },
    {
      "Technology_Name": "Technology name",
      "years_of_experience": "Years of experience",
      "level_of_competency": "Level of competency"
    },
    {
      "Technology_Name": "Technology name",
      "years_of_experience": "Years of experience",
      "level_of_competency": "Level of competency"
    },
    {
      "Technology_Name": "Technology name",
      "years_of_experience": "Years of experience",
      "level_of_competency": "Level of competency"
    },
    {
      "Technology_Name": "Technology name",
      "years_of_experience": "Years of experience",
      "level_of_competency": "Level of competency"
    }
  ],
  "education_and_qualifications": {
    "qualification": [
      "Qualification 1 - Institution",
      "Qualification 2 - Institution"
    ],
    "professional_development": [
      "Professional Development 1",
      "Professional Development 2"
    ]
  },
  "interests_and_hobbies": {
    "interests": ["Interest 1", "Interest 2"],
    "hobbies": ["Hobby 1", "Hobby 2"]
  },
  "appendix": [
    "experience :{
      "organisation_name": "Organisation name",
      "job_title": "Job title",
      "dates_of_employment": "Dates employed",
      "responsibilities": "Detailed responsibilities",
      "activities": "Activities",
      "achievements": "Achievements"
    },
    {
      "organisation_name": "Organisation name",
      "job_title": "Job title",
      "dates_of_employment": "Dates employed",
      "responsibilities": "Detailed responsibilities",
      "activities": "Activities",
      "achievements": "Achievements"
    },
    {
      "organisation_name": "Organisation name",
      "job_title": "Job title",
      "dates_of_employment": "Dates employed",
      "responsibilities": "Detailed responsibilities",
      "activities": "Activities",
      "achievements": "Achievements"
    },
    {
      "organisation_name": "Organisation name",
      "job_title": "Job title",
      "dates_of_employment": "Dates employed",
      "responsibilities": "Detailed responsibilities",
      "activities": "Activities",
      "achievements": "Achievements"
    },
    {
      "organisation_name": "Organisation name",
      "job_title": "Job title",
      "dates_of_employment": "Dates employed",
      "responsibilities": "Detailed responsibilities",
      "activities": "Activities",
      "achievements": "Achievements"
    }
  ]
}

Make sure the JSON output is not malformed, follows this exact structure, and uses the keys exactly as specified. The output should remain consistent across multiple requests. Make sure that the appendix section is filled out unless you run out of information."""
)

    headers = {
        'Authorization': f'Bearer {openai.api_key}',
        'Content-Type': 'application/json'
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": f"{prompt}\n\n{cv_text}"}
        ],
        "max_tokens": 2000
    }

    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)

    if response.status_code == 200:
        raw_response = response.json()["choices"][0]["message"]["content"]

        try:
            cleaned_response = json.loads(raw_response)
            return cleaned_response
        except json.JSONDecodeError:
            print("JSON decoding failed: Raw response may be incomplete or malformed.")
            return None
    else:
        print(f"Request failed with status code {response.status_code}: {response.text}")
        return None

def extract_text_from_file(file_path, file_extension):
    text = ""
    try:
        if file_extension == ".pdf":
            with open(file_path, "rb") as file:
                pdf = PdfReader(file)
                for page in pdf.pages:
                    text += page.extract_text()
        elif file_extension in [".doc", ".docx"]:
            text = docx2txt.process(file_path)
    except Exception as e:
        print(f"Error extracting text from file: {e}")
    return text

@app.route('/process-cv', methods=['POST'])
@limiter.limit("10 per hour")
def process_cv():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if not is_allowed_file(file.filename):
        return jsonify({"error": "Invalid or unsupported file type"}), 400

    file_ext = os.path.splitext(file.filename)[1].lower()
    temp_file_path = os.path.join('temp', werkzeug.utils.secure_filename(file.filename))
    file.save(temp_file_path)

    text = extract_text_from_file(temp_file_path, file_ext)
    os.remove(temp_file_path)

    if text:
        formatted_data = process_cv_with_chatgpt(text)
        if formatted_data:
            template_id = "2993"
            template = fetch_html_template_by_id(pdfco_api_key, template_id)

            if template:
                formatted_cv = format_document_with_pdfco(pdfco_api_key, formatted_data, template)

                if formatted_cv:
                    formatted_cv_path = os.path.join('downloads', 'formatted_cv.pdf')
                    with open(formatted_cv_path, 'wb') as f:
                        f.write(formatted_cv)

                    file_url = request.host_url + 'download/formatted_cv.pdf'
                    return jsonify({"message": "CV processed successfully", "file_url": file_url})

    return jsonify({"error": "Failed to process CV. Please make sure the uploaded file is either a txt, pdf, or doc"}), 500

@app.route('/download/<filename>')
def download_file(filename):
    safe_filename = werkzeug.utils.secure_filename(filename)
    return send_from_directory('../downloads', safe_filename)

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Server Error: {error}")
    return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    # Ensure the download and temp directories exist
    if not os.path.exists('../downloads'):
        os.makedirs('../downloads')
    if not os.path.exists('temp'):
        os.makedirs('temp')

    app.config['SESSION_COOKIE_SECURE'] = True  # Secure cookies over HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to cookies
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Prevent CSRF attacks
    app.run(debug=True)

