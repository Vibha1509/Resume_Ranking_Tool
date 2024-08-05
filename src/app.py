from io import BytesIO

from flask import Flask, request, jsonify, render_template, send_file
from src.services.service import process_resumes_and_jd
from src.repository.mongodb_repository import get_resume_by_id
from src.utils.llm_utils import generate_pitch_email_from_llm, chat_with_resume

import os


app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return render_template("index.html")

@app.route('/tool', methods=['GET'])
def tool():
    return render_template("tool.html")

@app.route('/result-resumes')
def result_resumes():
    return render_template('result-resumes.html')

@app.route('/pitch-email')
def pitch_emails():
    return render_template('pitch-email.html')


#Homepage API
@app.route('/api/fetch_resumes', methods=['POST'])
def fetch_resumes():
    resumes = request.files.getlist('resumes')
    job_description = request.form.get('jobDescription')

    response = process_resumes_and_jd(resumes, job_description)

    return jsonify(response), 200




#View Resume Button
@app.route('/api/download-pdf/<resume_id>', methods=['GET'])
def download_pdf(resume_id):
    resume_file = get_resume_by_id(resume_id)

    if not resume_file:
        return "File not found", 404

    # Read the file content
    pdf_bytes = resume_file.read()
    pdf_stream = BytesIO(pdf_bytes)

    #filename = resume_id + '.pdf'
    # Send the file as a response without forcing download
    return send_file(pdf_stream, mimetype='application/pdf')



#Generate Pitch Email
@app.route('/api/generate-email/<resume_id>', methods=['POST'])
def generate_email(resume_id):
    resume_file = get_resume_by_id(resume_id)
    if not resume_file:
        return jsonify({"error": "File not found"}), 404

    job_description = request.json.get('jobDescription')
    if job_description is None:
        return jsonify({"error": "Job description not provided"}), 400

    try:
        response = generate_pitch_email_from_llm(resume_id, job_description)
        return jsonify({"pitch_email": response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/api/chat-icon/<resume_id>', methods=['POST'])
def chat_icon_conversation(resume_id):
    resume_file = get_resume_by_id(resume_id)
    if not resume_file:
        return jsonify({"error": "File not found"}), 404

    job_description = request.json.get('jobDescription')
    user_input = request.json.get('userInput')
    if job_description is None:
        return jsonify({"error": "Job description not provided"}), 400
    if user_input is None:
        return jsonify({"error": "User input not provided"}), 400

    try:
        response = chat_with_resume(resume_id, job_description, user_input)
        return jsonify({"response": response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    # app.run(debug=True)
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

