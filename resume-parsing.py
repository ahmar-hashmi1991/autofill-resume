import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import PyPDF2
import spacy
from dotenv import load_dotenv

from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("api_key"))

# Set your OpenAI GPT API key


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
        doc = nlp(extracted_text)
        
        # Create a prompt for generating content for a job application form
        prompt = f"Generate content for a job application form based on the following resume:\n\n{extracted_text}\n\n"

        # Specify the fields you want to fill in the form
        fields = ["Name", 
        "Experience", 
        "Skills", 
        "Education", 
        "Contact"]

        name = "Ahmar"

        experience = "7 years"

        # Generate content for each field
        for field in fields:
            prompt += f"Field: {field}\n"
            prompt += "Content:"

            # Use the spaCy doc to provide context for the model
        prompt += f" {doc.text}\n"
        #print("prompt >> ", prompt)
        #return

        # Set the temperature and max tokens for GPT-3
        temperature = 0.7
        max_tokens = 150

        # Split the text into chunks of 4096 tokens
        chunk_size = 4096
        chunks = [prompt[i:i+chunk_size] for i in range(0, len(prompt), chunk_size)]

        generated_content = []

        # Use the OpenAI GPT-3 API to generate content for the job application form
        # Process each chunk
        for i, chunk in enumerate(chunks):
            prompt = chunk if i == 0 else ''  # Use only the first chunk as prompt, others as continuation
    
            response = client.completions.create(model="text-davinci-003",  # You may need to adjust the engine depending on your API version
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens)
            
            #print(response)

            # Extract the generated content from the response
            generated_content.append(response.choices[0].text)

        for i in range(len(generated_content)):
            print(generated_content[i])
        
        return render_template('fill_form.html', name=name, experience=experience)

    return 'Invalid file format. Please upload a PDF file.'

if __name__ == '__main__':
    app.run(debug=True)
