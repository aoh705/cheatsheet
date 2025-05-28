from flask import Flask, render_template, request, redirect, jsonify, send_file
from openai import OpenAI
import re

import os
from dotenv import load_dotenv
from pathlib import Path
import glob
import PyPDF2
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__)

load_dotenv(Path(".env"))
key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=key)


UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# DATA
rec_data = {
    "major": "",
    "subject": "",
    "topics": [],
    "options": [],
    "files": [],
}

# PAGE ROUTES
@app.route('/')
def home():
    return render_template('generate.html')

# AJAX FUNCTION
# upload user info to dict
@app.route('/user', methods=['POST'])
def user_info():
    json_data = request.get_json()
    rec_data["major"] = json_data["major"]
    rec_data["subject"] = json_data["subject"]

    print(rec_data)

    return jsonify({'subject': rec_data['subject'], 'major': rec_data['major']})

# upload files from local machine
@app.route('/upload', methods=['POST']) 
def upload(): 
    # first remove previous files
    prev_files = glob.glob(os.path.join(UPLOAD_FOLDER, '*'))
    for f in prev_files:
        os.remove(f)

    # save files
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    files = request.files.getlist('file')  # Get list of files
    file_paths = []

    for file in files:
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)  # Save file to the uploads folder
        file_paths.append(file_path)
    
    rec_data["files"] = file_paths
    
    return jsonify({"message": "Files successfully uploaded", "subject": rec_data['subject'], "file_paths": file_paths}), 200

# get topics from PDF files
@app.route('/topics', methods=['GET', 'POST'])
def topic_summary():
    subject = rec_data["subject"]

    # go through each file in uploads and send over prompt
    files = glob.glob(os.path.join(UPLOAD_FOLDER, '*.pdf'))
    # prompt and layout
    all_res = process_files(files, subject)
    print(all_res)

    # split response by new line and put into array
    rec_data['topics'] = []
    topics = all_res.split('\n')
    for t in topics:
        if t:
            new_t = t.lstrip('- ')
            rec_data['topics'].append(new_t)

    
    return jsonify({"subject": rec_data['subject'], "topics": rec_data['topics']})

# change pdf to text / string
def pdf_to_text(file):
    with open(file, 'rb') as pdf_file:
        # Create a PdfReader object instead of PdfFileReader
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # Initialize an empty string to store the text
        text = ''

        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
    
    return text

def process_files(files, subject):
    all_res = ""
    for file in files:
        info3 = pdf_to_text(file)
        prompt = f'''
        Give me three topics from {info3} in {subject} class. Format it like this:
            - [topic]
            - [topic]
            - [topic]
        '''
        # get gpt response
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        response_back = response.choices[0].message.content
        all_res = all_res + '\n' + response_back
    return all_res

def process_with_topics(files, subject, selectedTopics):
    all_res = ""
    for file in files:
        info3 = pdf_to_text(file)
        prompt = f'''
        Give me a summary from {info3} in {subject} class for one of these {selectedTopics} with each point in a 
        separate bullet point with one of {selectedTopics} as the title:
            [Topic]: 
                - information
                - information
        '''

        # get gpt response
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        response_back = response.choices[0].message.content
        all_res = all_res + '\n' + response_back
    return all_res


# generate options for the user on what kind of cheat sheet they want to get
@app.route('/generate_actions', methods=['GET', 'POST'])
def generate_actions():
    subject = rec_data["subject"]
    major = rec_data["major"]

    # json data of selected topics
    selectedTopics= request.get_json()

    # go through each file in uploads and send over prompt
    # prompt and layout
    files = glob.glob(os.path.join(UPLOAD_FOLDER, '*.pdf'))
    all_res = process_with_topics(files, subject, selectedTopics)

    # getting options the student can choose to do with the information from PDF files
    prompt = f'''What kinds of things can a {major} student do with {all_res}. 
                Give me 10 options that is at most five words.
                Format it like this:
                - option
                - option
                - option
                '''
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    response_back = response.choices[0].message.content

    print(response_back)

    # make options into array
    rec_data['options'] = []
    options = response_back.split('\n')
    for o in options:
        if o:
            new_option = o.lstrip('- ')
            rec_data['options'].append(new_option)
    
    print(rec_data['options'])
    return jsonify({"options": rec_data['options']})

# generate cheat sheet
@app.route('/generate_sheet', methods=['GET', 'POST'])
def generate_sheet():
    json_data = request.get_json()
    subject = rec_data["subject"]
    major = rec_data["major"]
    actions = json_data

    # go through files
    all_res = ""
    files = glob.glob(os.path.join(UPLOAD_FOLDER, '*.pdf'))
    for file in files:
        info3 = pdf_to_text(file)

        # call gpt
        prompt = f'''Give me a study guide and content explanation for a {major} student to successfully do {actions} from {info3}.
                Format it like this:
                [headings]
                - [information]
                - [information]
        
        '''
        # summarize the content above
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        responses = response.choices[0].message.content
        all_res = all_res + '\n' + responses

    print(all_res)

    pdf_file_path = "cheat_sheet.pdf"
    c = canvas.Canvas(pdf_file_path, pagesize=letter)
    width, height = letter
    
    left_margin=50
    right_margin=50

    # Set margins and line height
    line_height = 15
    max_width = width - (left_margin + right_margin)  # Maximum width for text
    y_position = height - 50  # Start position from top

    # Split the text into lines
    lines = all_res.split('\n')

    for line in lines:
        # Split the line into words for wrapping
        words = line.split(' ')
        current_line = ''
        
        for word in words:
            # Check if adding this word would exceed the maximum width
            test_line = f"{current_line} {word}".strip()
            text_width = pdfmetrics.stringWidth(test_line, 'Helvetica', 12)

            if text_width <= max_width:
                current_line = test_line  # Add the word to the current line
            else:
                # Draw the current line and reset for the next line
                c.drawString(left_margin, y_position, current_line)
                y_position -= line_height  # Move down for the next line
                current_line = word  # Start new line with the current word
            
            # Check if we need a new page
            if y_position < 50:  # Adjust for the bottom margin
                c.showPage()
                y_position = height - 50  # Reset position for new page
        
        # Draw any remaining text in current_line
        if current_line:
            c.drawString(left_margin, y_position, current_line)
            y_position -= line_height  # Move down for the next response

    c.save()  # Save the PDF file after all lines are added
    print(f"PDF generated and saved at {pdf_file_path}")

    return jsonify({"path_to_file": pdf_file_path})

@app.route('/download', methods=['GET'])
def download():
    return send_file("cheat_sheet.pdf", as_attachment=True)

@app.route('/recommend_authors', methods=['GET', 'POST'])
def recommend_authors():
    json_data = request.get_json()
    print(json_data)
    rec_data["book_title"] = json_data["book_title"]
    rec_data["book_author"] = json_data["book_author"]
    rec_data["book_desc"] = json_data["book_desc"]

    # generate authors from GPT
    prompt = "Please recommend five author names only for readers who enjoyed " + rec_data["book_author"] + "'s " + rec_data["book_title"] + " that is about " + rec_data["book_desc"] + "."
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user", 
                "content": prompt
            }
        ]
    )

    response_back = response.choices[0].message.content

    print(str(response_back))

    parsed_response = []

    try:
        parsed_response = parse_response(response_back)
    except:        
        print("ERROR: gpt keyword response won't parse")
        print(response_back)

    if len(rec_data["author_recs"]) != 0:
        rec_data["author_recs"] *= 0

    print(rec_data["author_recs"])
    rec_data["author_recs"] = parsed_response

    return jsonify(data={"files": parsed_response})

def parse_response(keyword_response):    
    keyword_list = keyword_response.splitlines()
    new_keyword_list = []
    for i, item in enumerate(keyword_list):
        item = item.strip()
        if item != "":
            item = item[item.index(".") + 1:]
            item = item.strip()
            new_keyword_list.append(item)

    print(new_keyword_list)
    return new_keyword_list

@app.route('/recommend_books', methods=['GET', 'POST'])
def recommend_books():
    # generate books from GPT

    author_list = concat_author_list(rec_data["author_recs"])

    prompt = "Please recommend books from " + author_list + " similar to " +  rec_data["book_title"] + " by " + rec_data["book_author"] + " and provide five keywords each in this format: book : xxx, keywords : xxx"
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user", 
                "content": prompt
            }
        ]
    )

    response_back = response.choices[0].message.content

    print(response_back)

    parsed_titles = {}

    try:
        parsed_titles = parse_book_recs(response_back)
        print(parsed_titles)
    except:        
        print("ERROR: gpt keyword response won't parse")
        # print(response_back)

    return jsonify(data={"book_recs": parsed_titles})

def concat_author_list(author_list):
    authors = ""

    for i in range(0, len(author_list)):
        if i != len(author_list) - 1:
            authors += author_list[i] + ", "
        else:
            authors += author_list[i]

    return authors

# MAIN

if __name__ == '__main__':
    app.run(debug=True)