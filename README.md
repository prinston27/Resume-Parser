# AI Resume Parser

AI Resume Parser is a web application that allows users to upload their resumes in various formats (PDF, DOC, DOCX, TXT), processes them, and provides a formatted CV. The application uses Flask for the backend, HTML/CSS/JavaScript for the frontend, and various tools for processing and formatting resumes.

## Features

- **Resume Upload**: Users can upload resumes in PDF, DOC, DOCX, and TXT formats.
- **Processing**: The application processes the uploaded resume and formats it according to predefined templates.
- **Download**: Users can download the processed and formatted CV.
- **Responsive Design**: The web application is designed to work on various devices, including desktops, tablets, and mobile phones.
- **Loading Indicators**: Visual feedback during the upload and processing stages.

## Technologies Used

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Styling**: Font Awesome, Custom CSS animations
- **Version Control**: Git, GitHub

Project Structure

├── backend 
│   └── app.py                     <- Main Flask application 
├── downloads 
│   └── formatted_cv.pdf           <- Example of processed CV 
├── frontend 
│   ├── images 
│   │   ├── bg.jpg                 <- Background image 
│   │   ├── overlay.jpg            <- Overlay image 
│   │   └── pm-partners-logo-stacked-white.png 
│   ├── index.html                 <- Main HTML File 
│   ├── script.js                  <- Javascript File for frontend interactions 
│   └── style.css                  <- CSS file for Styling 
├── uploads                        <- Folder for uploaded resumes 
├── .gitignore                     <- Git ignore file 
└── README.md


## Setup Instructions

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/ai-resume-parser.git
   cd ai-resume-parser

2. **Create a Virtual Environment**
    
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate   # On Windows use: .venv\Scripts\activate

3. **Install the required Packages**

    ```bash
    pip install -r backend/requirements.txt

4. **Run the Flask Application**
    
    ```bash
    python backend/app.py

5. **Access from your localhold browser**
    
    Open your web browser and go to http://127.0.0.1:5000.

# Usage

- **Upload Your Resume**: Click on the "Choose CV" button to upload your resume.
- **Submit**: Once uploaded, click on the "Submit" button.
- **Download:** After processing, a download link will appear. Click the link to download your formatted CV.
Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue.

# License
This project is licensed under the MIT License. See the LICENSE file for details.

# Contact
For any questions or feedback, please reach out to prinston.mascarenhas@gmail.com.
