import PyPDF2
from PyPDF2 import PdfReader
import os
from together import Together
from io import BytesIO
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

# Extract text from PDF
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        text = ""
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
    return text

# def extract_text_from_pdf(resume_file):
#     resume_file.seek(0)
#     pdf_file = BytesIO(resume_file.read())

#     text = ""
#     for page_layout in extract_pages(pdf_file):
#         for element in page_layout:
#             if isinstance(element, LTTextContainer):
#                 text += element.get_text() + "\n"
#     return text

# Function to call LLaMA 3 model via Together.ai
def call_llm(prompt):
    clientAPI = Together(api_key="1ff96bc452a77fbdfea388ee12e6491ac5a53043dc66de6f2946f5b4ddefe800")
    response = clientAPI.chat.completions.create(
        model="meta-llama/Llama-3-8b-chat-hf",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

# Initialize conversation history
conversation_history = []

# Chat with PDF function
def chat_with_pdf(pdf_text, user_input):
    # Add the PDF content to the initial context if the conversation is starting
    if not conversation_history:
        conversation_history.append(f"Content from PDF: {pdf_text}")
    
    # Add user input to the conversation history
    conversation_history.append(f"User: {user_input}")
    
    # Create the prompt for the model
    prompt = "\n".join(conversation_history)
    
    response = call_llm(prompt)
    conversation_history.append(f"AI: {response}")
    
    return response

# Main function
def main():
    # Path to the PDF file
    pdf_path = r"C:\Users\vanda\OneDrive\Documents\Job Search\Resume_Old.pdf"
    
    # Extract text from the PDF
    pdf_text = extract_text_from_pdf(pdf_path)
    
    print("You can now start chatting with the PDF content!")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Chat ended.")
            break
        
        response = chat_with_pdf(pdf_text, user_input)
        print(f"AI: {response}")

if __name__ == "__main__":
    main()
