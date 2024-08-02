from io import BytesIO
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from src.repository.mongodb_repository import get_resume_by_id

def extract_text_from_pdf(resume_file):
    resume_file.seek(0)
    pdf_file = BytesIO(resume_file.read())

    text = ""
    for page_layout in extract_pages(pdf_file):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                text += element.get_text() + "\n"

    return text

# get Resumes from a list of IDs
def get_resumes(resume_ids):
    # will return a list of dicts
    # each dict looks like:
    # {
    #     'resume_id': <<resume_id>>,
    #     'resume_file': <<resume_file_pointer>>
    # }
    resume_files = []
    
    for id in resume_ids:
        temp_dict = {}
        temp_dict['resume_id'] = str(id)
        temp_dict['resume_file_pointer'] = get_resume_by_id(id)
        resume_files.append(temp_dict)
    
    return resume_files
