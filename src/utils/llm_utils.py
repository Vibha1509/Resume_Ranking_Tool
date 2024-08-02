from together import Together
from src.utils.resume_file_utils import extract_text_from_pdf
from src.utils.resume_file_utils import get_resumes
from src.repository.mongodb_repository import get_resume_by_id
import re
import io
import os

def generate_prompt_summary(resume_text, job_description):
    prompt = """
        [ROLE] HR Recruiter
        Objective:
        To streamline the recruitment process by leveraging an LLM to filter and score a candidate based on a job description provided. This application will perform a two-level screening process to ensure the candidate meets the given job requirement and rate the suitability of the candidate to facilitate quick decision-making by HR.

        Instructions:

        First Level Filtering:
        The first level of filtering must be stringent and function similarly to a keyword search, ensuring only candidates who explicitly meet the job requirements pass through.

        Here are a few examples to look out for while performing the first level of filtering. Note that these are just examples of some cases that are common. These may or may not be a part of the job description provided:-
        ---Experience:
        If the job requires a specific number of years of experience (e.g., 3 years), ensure the candidate's resume explicitly states this experience or calculate it from the employment dates mentioned.
        Example: "3 years of experience in software development."
        ---Gender:
        If the job requires a specific gender, identify the gender from the name on the resume. For LGBTQ+ requirements, look for pronouns or other indicators of gender identity.
        Example: "John Doe" for male or "Jane Doe" for female. Pronouns like "they/them" for non-binary.
        ---Location:
        If the job requires the candidate to be in a specific location, check the resume for the candidate's current location and their willingness to relocate if necessary.
        Example: Job in California, resume states candidate is in New York but mentions "open to relocation."

        Reject candidates who do not meet these strict criteria.

        Do not move to the second level of filtering if the candidate does not pass this first level of screening.

        Second Level Ranking:
        ---For candidates who pass the first level of filtering, score the resume out of 10 based on their fit for the job. This ranking should consider the following factors:
        ---Relevance of Skills and Experience:
        Assess how closely the candidate's skills and past experience match the job description.
        Example: If the job is for a software developer with Python expertise, prioritize candidates with extensive Python development experience.
        ---Additional Qualifications:
        Consider any additional qualifications or certifications that enhance the candidate's suitability for the role.
        Example: Certifications like AWS Certified Developer for a cloud development role.
        ---Soft Skills and Cultural Fit:
        Evaluate the candidate's soft skills and their potential cultural fit within the company.
        Example: Leadership experience or teamwork as mentioned in the job description.

        For each shortlisted candidate:

        Extract the name on the resume.
        Assign a score out of 10.
        Provide a concise summary highlighting:
        Strengths- The qualities that make the candidate a good fit for the job.
        Weaknesses- Any skills or qualifications the candidate lacks that are essential or beneficial for the role.

        The output must be in a JSON format.

        ##############################################################################################

        Examples of LLM final output:-

        Job Description:
        Requires 3 years of marketing experience, a female candidate, and the job is based in New York.

        Candidate A's Resume:
        John Doe, 2 years of marketing experience, male, based in New York.

        LLM OUPUT:-
        {
        "Name": "John Doe",
        "Status": "Reject",
        "Score": null,
        "Summary": {"Candidate is a male, but female candidate is required."}
        }

        Candidate B's Resume:
        Jessica James, 4 years of marketing experience, female, based in Boston, mentions willingness to relocate.

        LLM OUTPUT:-
        {
        "Name": "Jessica James",
        "Status": "Accept",
        "Score": 9,
        "Summary": 
        {"Strengths: "Strong marketing background with 4 years of experience, surpassing the required 3 years. Demonstrates excellent campaign management and analytical skills. Willing to relocate to New York, matching the job location requirement.", 
        "Weaknesses": "Lacks experience in digital marketing, which is a key aspect of the job."}
        }

        #############################################################################################

        Please provide the output in the following JSON format:

        For rejected candidates:
        {
        "Name": "<Extract name from resume>",
        "Status": "Reject",
        "Score": 0,
        "Summary": {"Reason": "<reason for rejection in 2-3 lines>"}
        }

        For accepted candidates:
        {
        "Name": "<Extract name from resume>",
        "Status": "Accept",
        "Score": <score  out of 10>,
        "Summary": {"strengths":"<The qualities that make the candidate a good fit for the job", "Weaknesses": "<Any skills or qualifications the candidate lacks that are essential for the role>"}
        }

        Output should not contain any other text.

        ##############################################################################################

        Input data:

        resume: {resume_input}
        job description: {jd_input}

        """.replace("resume_input", resume_text).replace("jd_input", job_description)

    return prompt


def generate_prompt_email(resume_text, job_description):
    prompt = """
        [TASK] Write a pitch email to a candidate applying for a job. Based on their resume and the job description, clearly explain why the candidate would be an excellent fit for the role. 
        This email will be sent from a recruiter at the company to the candidate.

        Job Description Overview: Start by briefly summarizing the job description.
        Candidate Fit: Detail how the candidate's qualifications, projects, and job experiences align with the job requirements. Use specific examples from their resume.
        Perks and Benefits: Highlight the perks and benefits available to the candidate if they join the company.
        Next Steps: Outline the next steps in the hiring process.
        Meeting Schedule: Request the candidate's preferred meeting schedule or means of communication.
        Include placeholders for the recruiter to fill in personal and company details.

        resume: {resume_input}
        job description: {jd_input}

        """.replace("resume_input", resume_text).replace("jd_input", job_description)
    
    return prompt


def call_llm(prompt):
    clientAPI = Together(api_key=os.environ.get("TOGETHER_API_KEY"))

    response = clientAPI.chat.completions.create(
        model="meta-llama/Llama-3-8b-chat-hf",
        messages=[{"role": "user", "content": prompt}],
    )
    # print(response.choices[0].message.content)
    return response.choices[0].message.content



import ast, traceback
def extract_valid_json(raw_output):
    response_text = raw_output.replace("```", "").replace("、", ",").replace("json", "").replace("</s>", "").replace(
        "<s>", "").replace('null', 'None').strip()
    try:
        response_dict = ast.literal_eval(response_text)
        return response_dict
    except Exception as e:
        malformed_json = response_text
        cleaned_json = re.search(r"\{.*\}", malformed_json, re.DOTALL)
        if cleaned_json:
            cleaned_json = cleaned_json.group(0)
            try:
                cleaned_json = ast.literal_eval(cleaned_json)
                return cleaned_json
            except Exception as e:
                traceback.print_exc()
                print("Error parsing response:", cleaned_json)
                return {}
        else:
            print("Error parsing response:", response_text)

    return{}



def get_summaries_from_llm(job_description, resume_ids):
    # Step 1: get all resumes dicts (id, filepointer)
    resume_files = get_resumes(resume_ids)

    # Step 2: get summary for each resume
    summaries = []
    for doc in resume_files:
        # READ PDF
        resume_text = extract_text_from_pdf(doc['resume_file_pointer'])

        # GENERATE PROMPT
        prompt = generate_prompt_summary(resume_text, job_description)

        # GET SUMMARY
        summary = call_llm(prompt)

        summary_json = extract_valid_json(summary)

        summaries.append({
            'resume_id': doc['resume_id'],
            'summary': summary_json,
        })

    return summaries



def generate_pitch_email_from_llm(resume_id, job_description):
    # Step 1: get resume by ID from mongodb
    resume_file = get_resume_by_id(resume_id)
    print(resume_id, job_description)
    print("-------------------------------------")

    # READ PDF
    resume_text = extract_text_from_pdf(io.BytesIO(resume_file.read()))

    # GENERATE PROMPT
    prompt = generate_prompt_email(resume_text, job_description)

    # GET EMAIL
    pitch_email = call_llm(prompt)

    return pitch_email



# def sort_resumes_by_score(resume_summaries):
#     sorted_resume_summaries = sorted(resume_summaries, key=lambda x: x['summary']['Score'], reverse=True)

#     return sorted_resume_summaries

def sort_resumes_by_score(resume_summaries):
    sorted_resume_summaries = sorted(resume_summaries, key=lambda x: x['summary'].get('Score', 0), reverse=True)

    return sorted_resume_summaries




def chat_with_resume(resume_id, job_description, user_input):
    # Step 1: get resume by ID from mongodb
    resume_file = get_resume_by_id(resume_id)
    resume_text = extract_text_from_pdf(io.BytesIO(resume_file.read()))

    # Initialize conversation history
    conversation_history = []

    # Add the PDF content and JD to initial context if the conversation is starting
    if not conversation_history:
        conversation_history.append(f"Resume Content: {resume_text}")
        conversation_history.append(f"Job Description: {job_description}")

    # Add user input to the conversation history
    conversation_history.append(f"User: {user_input}")
    
    # Create the prompt for the model
    prompt = "\n".join(conversation_history)
    
    response = call_llm(prompt)
    conversation_history.append(f"AI: {response}")
    
    return response
