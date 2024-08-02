from src.repository.mongodb_repository import save_resume_to_mongo
from src.utils.llm_utils import get_summaries_from_llm, sort_resumes_by_score

def process_resumes_and_jd(resumes, job_description):
    
    # Step1: Save all the resumes in Mongo and get back resume_ids
    resume_ids = []
    for resume in resumes:
        resume_id = save_resume_to_mongo(resume)
        resume_ids.append(resume_id)

    # Step2: get Summary and rating for each of the resume
    resume_summaries = get_summaries_from_llm(job_description, resume_ids)
    sorted_resumes = sort_resumes_by_score(resume_summaries)

    return sorted_resumes

