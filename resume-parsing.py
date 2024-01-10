import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import PyPDF2
import spacy
from dotenv import load_dotenv

from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

# Define the upload folder and allowed file extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_file_path):
    text = ""
    with open(pdf_file_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for pageNumber in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[pageNumber].extract_text()
    return text

# Load the spaCy model for English
nlp = spacy.load("en_core_web_sm")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Extract text from the uploaded PDF
        extracted_text = extract_text_from_pdf(file_path)

        # Extract structured information using spaCy NLP
        # doc = nlp(extracted_text)
        
        prompt = f"""
            Given a resume in PDF format, I need help extracting and categorizing information to autofill a resume form. The resume includes fields like name, experience, skills, education, and contact information. Here's a snippet of the resume text:

            Resume Text:
            {extracted_text}
            Extract the following information:
                Name: [Enter Name Here]
                Experience: [Enter Experience Here]
                Skills: [Enter Skills Here]
                Education: [Enter Education Here]
                Contact: [Enter Contact Here]
            """
        response = client.completions.create(model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=300)

        print("response >> ", response)

        extracted_info = response.choices[0].text
        print("extracted_info >> ", extracted_info)

        # Assume 'extracted_info' contains the generated text from the GPT-3 response

        # Split the generated text into lines
        extracted_lines = extracted_info.split('\n')

        # # Initialize variables for storing categorized information
        name = ""
        experience = ""
        skills = ""
        education = ""
        contact = ""

        # # Loop through each line and categorize information based on patterns or context
        # for line in extracted_lines:
        #     if "Name:" in line:
        #         name = line.split("Name:")[-1].strip()
        #     elif "Experience:" in line:
        #         experience = line.split("Experience:")[-1].strip()
        #     elif "Skills:" in line:
        #         skills = line.split("Skills:")[-1].strip()
        #     elif "Education:" in line:
        #         education = line.split("Education:")[-1].strip()
        #     elif "Contact:" in line:
        #         contact = line.split("Contact:")[-1].strip()

        # # Now, 'name', 'experience', 'skills', 'education', 'contact' variables contain categorized information
        # print("Name:", name)
        # print("Experience:", experience)
        # print("Skills:", skills)
        # print("Education:", education)
        # print("Contact:", contact)
        # Initialize dictionaries to store categorized information
        categorized_info = {
            'Name': '',
            'Experience': '',
            'Skills': '',
            'Education': '',
            'Contact': ''
        }

        # Keep track of the current field and join multiline values
        current_field = None
        for line in extracted_lines:
            line = line.strip()  # Remove leading/trailing whitespace

            # Check if the line represents a field indicator
            if any(field in line for field in categorized_info.keys()):
                splitted_val = line.split(':')
                current_field = splitted_val[0]
                categorized_info[current_field] = splitted_val[1] if len(splitted_val) > 1 else '' # Initialize the field
            else:
                # Append line to the current field if it's not empty
                if current_field and line:
                    categorized_info[current_field] += line + '\n'  # Append the line
        print(categorized_info)

        # Filter out empty or whitespace lines and strip trailing newline characters
        filtered_info = {key: value.strip() for key, value in categorized_info.items() if value.strip()}

        print(filtered_info)
        # Process 'filtered_info' for autofilling the resume form
        name = filtered_info['Name']
        experience = filtered_info['Experience']
        skills = filtered_info['Skills']
        education = filtered_info['Education']
        contact = filtered_info['Contact']


        # Now you can use these values to populate the respective fields or store them as needed
        # For instance, in your Flask application, pass these values to the fill_form.html template
        return render_template('fill_form.html', name=name, experience=experience, skills=skills, education=education, contact=contact)

    return 'Invalid file format. Please upload a PDF file.'

if __name__ == '__main__':
    app.run(debug=True)
