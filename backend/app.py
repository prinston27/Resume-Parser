from flask import Flask, request, jsonify, send_file, render_template
import os
import json
import requests
import openai
import io
from PyPDF2 import PdfReader
import docx2txt
from dotenv import load_dotenv

app = Flask(__name__, template_folder='../frontend', static_folder='../frontend')

# Load environment variables from .env file
load_dotenv()

@app.route('/')
def index():
    return render_template('index.html')

# Set up API keys and connection details
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key
pdfco_api_key = os.getenv("PDFCO_API_KEY")

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

Make sure the JSON output is not malformed, follows this exact structure, and uses the keys exactly as specified. The output should remain consistent across multiple requests."""
)


    headers = {
        'Authorization': f'Bearer {openai.api_key}',
        'Content-Type': 'application/json'
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": f"{prompt}\n\n{cv_text}"}],
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

def extract_text_from_file(file, file_extension):
    text = ""
    try:
        if file_extension == ".pdf":
            pdf = PdfReader(file)
            for page in pdf.pages:
                text += page.extract_text()
        elif file_extension in [".doc", ".docx"]:
            text = docx2txt.process(file)
    except Exception as e:
        print(f"Error extracting text from file: {e}")
    return text


@app.route('/process-cv', methods=['POST'])
def process_cv():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".pdf", ".doc", ".docx"]:
        return jsonify({"error": f"Unsupported file type: {file_ext}"}), 400

    # Use in-memory file
    file_content = io.BytesIO(file.read())

    # Extract text from the file
    text = extract_text_from_file(file_content, file_ext)

    if isinstance(text, dict) and "error" in text:
        return jsonify(text), 400

    formatted_data = process_cv_with_chatgpt(text)
    if formatted_data and isinstance(formatted_data, dict) and "error" not in formatted_data:
        template_id = "2993" 
        template = fetch_html_template_by_id(pdfco_api_key, template_id)
        
        if template:
            formatted_cv = format_document_with_pdfco(pdfco_api_key, formatted_data, template)
            
            if formatted_cv:
                # Send the generated PDF as a downloadable file
                return send_file(
                    io.BytesIO(formatted_cv), 
                    download_name="formatted_cv.pdf", 
                    mimetype="application/pdf"
                )
            else:
                return jsonify({"error": "Failed to format document with PDF.co"}), 500
        else:
            return jsonify({"error": "Failed to fetch HTML template from PDF.co"}), 500
    else:
        return jsonify({"error": "Failed to process CV with ChatGPT"}), 500


if __name__ == '__main__':
    app.run(debug=True)
