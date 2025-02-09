from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from .models import Textbook
import requests
import PyPDF2
import openai
from ebooklib import epub
from bs4 import BeautifulSoup
from django.conf import settings
from google import genai
from PyPDF2 import PdfReader  


# Function to search for a textbook online using Google Books API
def search_textbook_online(name):
    url = f"https://www.googleapis.com/books/v1/volumes?q={name}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()  # Return search results
    return None

# Function to extract text from a PDF file
def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

# Function to extract text from an EPUB file
def extract_text_from_epub(file_path):
    book = epub.read_epub(file_path)
    text = ""
    for item in book.get_items():
        if item.get_type() == epub.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text += soup.get_text()
    return text

# Function to extract text from a file (PDF or EPUB)
def extract_text_from_file(file_path):
    if file_path.endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith('.epub'):
        return extract_text_from_epub(file_path)
    else:
        raise ValueError("Unsupported file format")

# Function to generate questions using OpenAI GPT
# def generate_questions(text):
#     openai.api_key = "sk-...gvgA"  # Replace with your OpenAI API key
#     # response = openai.Completion.create(
#     #     engine="text-davinci-003",
#     #     prompt=f"Generate 5 questions from the following text:\n\n{text}",
#     #     max_tokens=500
#     # )
#     response = openai.ChatCompletion.create(
#     model="gpt-3.5-turbo",  # Use the latest available model
#     messages=[{"role": "system", "content": "You are an AI that generates questions from text."},
#               {"role": "user", "content": f"Generate 5 questions from the following text:\n\n{text}"}]
# )
#     return response.choices[0].text.strip()

def generate_questions(text):
    # client = openai.Client(api_key=settings.OPENAI_API_KEY)  # Use the new API format
    openai.api_key = settings.OPENAI_API_KEY

    
    # response = client.chat.completions.create(
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an AI that generates questions from text."},
            {"role": "user", "content": f"Generate 5 questions from the following text:\n\n{text}"}
        ],
        max_tokens=500
    )
    
    return response.choices[0].message.content.strip()

# API View to upload a textbook
class UploadTextbook(APIView):
    parser_classes = [MultiPartParser]
    API_KEY = "AIzaSyBBYVqeD6eo1REqbiNYo6ylLvexyXtyvds"

    def post(self, request):
        file = request.FILES.get('file')
        if file:
            textbook = Textbook.objects.create(name=request.data.get('name'), file=file)

            # Read the content from the uploaded file
            file_path = textbook.file.path  # Get the saved file path
            extracted_text = self.extract_text(file_path, file.name)
            
            if not extracted_text.strip():
                return Response({"error": "Could not extract text from file"}, status=400)
            # Generate questions using Gemini API
            questions = self.generate_from_pdf(extracted_text)

            return Response({
                "message": "Textbook uploaded and processed successfully!",
                "id": textbook.id,
                "questions": questions
            })

            # return Response({"message": "Textbook uploaded successfully!", "id": textbook.id})
        return Response({"error": "No file uploaded"}, status=400)
    
    def extract_text(self, file_path, filename):
        """
        Extract text from the uploaded file (supports .txt and .pdf)
        """
        text = ""
        try:
            if filename.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            elif filename.endswith('.pdf'):
                with open(file_path, 'rb') as f:
                    pdf_reader = PdfReader(f)
                    text = " ".join([page.extract_text() or "" for page in pdf_reader.pages])
        except Exception as e:
            print(f"Error extracting text: {e}")
        
        return text

    def generate_from_pdf(self, content):
        """
        Send extracted text to Gemini API for question generation.
        """
        try:
            API_KEY = "AIzaSyBBYVqeD6eo1REqbiNYo6ylLvexyXtyvds"

            # Print raw request data for debugging
            # print("Raw request data:", request.data)
            # print("Request content type:", request.content_type)
            
            # Handle both form-data and JSON input
            # if isinstance(request.data, dict):
            #     data = request.data
            # else:
            #     try:
            #         data = json.loads(request.data)
            #     except:
            #         data = request.data
                    
            # print("Processed request data:", data)
            
            # Extract parameters
            # num_questions = data.get('num_questions')
            # if isinstance(num_questions, str):
            #     num_questions = int(num_questions)

            # Generate questions using class API key
            client = genai.Client(api_key=self.API_KEY)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"Generate 10 mock interview questions along with answers based on the following text:\n\n{content[:5000]} "
            )

            print("Gemini API response text:", response.text)

            #  # Parse response to JSON
            # if response and hasattr(response, 'text'):
            #     try:
            #         return json.loads(response.text)  # Convert API text response to JSON
            #     except json.JSONDecodeError:
            #         return [{"question": "Failed to parse response", "rationale": "Check API output format"}]
            # else:
            #     return [{"question": "No questions generated", "rationale": "API returned an empty response"}]

            # Parse response to JSON
            # if response.status_code == 200:
            #     try:
            #         return json.loads(response.text)  # Attempt to parse the API response
            #     except json.JSONDecodeError:
            #         print("Error parsing response:", response.text)  # Log the error response
            #         return [{"question": "Failed to parse response", "rationale": "Check API output format"}]
            # else:
            #     return [{"question": "Error with API request", "rationale": f"Status code: {response.status_code}"}]

            # try:
            #     return json.loads(response.text)  # Attempt to parse the API response as JSON
            # except json.JSONDecodeError:
            #     print("Error parsing response:", response.text)
            #     return [{"question": "Failed to parse response", "rationale": "Check API output format"}]

            # questions = self.extract_questions_from_text(response.text)

            # import json

            # try:
            #     response_json = json.loads(response.text)
            #     print("Parsed Response:", response_json)
            # except json.JSONDecodeError as e:
            #     print("JSON Parsing Error:", e)

            # if not questions:
            #     print("Error parsing response:", response.text)
            #     return [{"question": "Failed to parse response", "rationale": "Check API output format"}]
            
            # return questions


            # genai.configure(api_key=API_KEY)

            # model = genai.GenerativeModel("gemini-1.5-flash")
            
            # # Send the content to Gemini for question generation
            # prompt = f"Generate 5 mock interview questions based on the following text:\n\n{content[:5000]}"
            # # Limiting text length to 5000 characters to avoid token limits

            # response = model.generate_content(prompt)
            return response.text if response and response.text else "No questions generated."
        
        except Exception as e:
            print(f"Error in question generation: {e}")
            return "Error generating questions"
        
    # def extract_questions_from_text(self, response_text):
    #     """
    #     Extract questions and rationale from the plain text response.
    #     """
    #     questions = []
    #     question_pattern = re.compile(r"\*\*Question (\d+): (.*?)\*\*.*?\n(.*?)\n\n\*+\s+\*\*Why this question is effective:\*\* (.*?)\n", re.DOTALL)
    #     matches = question_pattern.findall(response_text)
        
    #     for match in matches:
    #         question = match[1].strip()
    #         rationale = match[3].strip()
    #         questions.append({
    #             "question": question,
    #             "rationale": rationale
    #         })
        
    #     return questions
    # import re

    # def extract_questions_from_text(self,response_text):
    #     """
    #     Extracts questions and rationale from the text response.
    #     """
    #     questions = []
        
    #     # Pattern to capture questions and rationales
    #     question_pattern = re.compile(
    #         r"\*\*Question \d+: \((.*?)\)\*\*\n\n"
    #         r"\"(.*?)\"\n\n"
    #         r"\*\*Why this question is good:\*\*\n\n"
    #         r"(.*?)(?=\n\n\*\*Question \d+:|\Z)", re.DOTALL
    #     )

    #     matches = question_pattern.findall(response_text)
        
    #     for match in matches:
    #         category = match[0].strip()
    #         question = match[1].strip()
    #         rationale = match[2].strip()
            
    #         questions.append({
    #             "question": question,
    #             "rationale": rationale
    #         })

    #     return questions


# API View to generate questions from a textbook
class GenerateQuestions(APIView):
    def post(self, request):
        textbook_name = request.data.get('name')
        search_result = search_textbook_online(textbook_name)

        if search_result:
            # Use online textbook content (placeholder for now)
            text = "Extract text from search result or download link"
        else:
            # Use uploaded textbook
            try:
                textbook = Textbook.objects.get(name=textbook_name)
                text = extract_text_from_file(textbook.file.path)
            except Textbook.DoesNotExist:
                return Response({"error": "Textbook not found"}, status=404)

        questions = generate_questions(text)
        return Response({"questions": questions})
    
# class TestQuestions(APIView):
    
#     def post(self, request):
#         client = genai.Client(api_key="AIzaSyBBYVqeD6eo1REqbiNYo6ylLvexyXtyvds")
#         response = client.models.generate_content(
#             model="gemini-2.0-flash", contents="Create 10 mock qusetions from the book Introduction to C programming by Dennis Richie"
#         )
#         print(response)
#         return Response({"questions": response})
        

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

# class TestQuestions(APIView):
    
#     def post(self, request):
#         api_key="AIzaSyBBYVqeD6eo1REqbiNYo6ylLvexyXtyvds"
        
#         try:
#             print("Request Data:", request.data)

#             # Get the number of questions from the request data, defaulting to 10 if not provided
#             num_questions = request.data.get('num_questions', 10)

#             if not isinstance(num_questions, int) or num_questions <= 0:
#                 raise ValidationError("num_questions should be a positive integer.")
            
#             # Ensure that the textbook name is provided
#             textbook_name = request.data.get('textbook_name')
#             if not textbook_name:
#                 raise ValidationError("Textbook name is required.")
            
#              # Print the individual fields
#             print(f"Number of Questions: {num_questions}")
#             print(f"Textbook Name: {textbook_name}")
            
#             client = genai.Client(api_key="AIzaSyBBYVqeD6eo1REqbiNYo6ylLvexyXtyvds")
#             response = client.models.generate_content(
#                 model="gemini-2.0-flash",
#                 contents=f"Create {num_questions} mock questions from the book {textbook_name}"
#             )
#             print(response)
#             return Response({"questions": response}, status=status.HTTP_200_OK)

#         except ValidationError as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({"error": "An error occurred while generating questions."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# def parse_questions(raw_text):
#     """
#     Parse the raw question text into a structured format.
#     Returns a list of dictionaries containing question number, content, and section.
#     """
#     try:
#         # Handle different input types
#         if isinstance(raw_text, dict):
#             raw_text = raw_text.get('questions', '')
#         elif not isinstance(raw_text, str):
#             print(f"Unexpected raw_text type: {type(raw_text)}")
#             raw_text = str(raw_text)

#         questions = []
#         current_section = None
        
#         # Split the text into lines
#         lines = raw_text.split('\n')
        
#         # Find the first section header
#         for i, line in enumerate(lines):
#             if line.strip().startswith('**') and ':' in line:
#                 current_section = line.strip('*: ')
#                 current_line = i
#                 break
#         else:
#             current_line = 0
        
#         # Process each line
#         while current_line < len(lines):
#             line = lines[current_line].strip()
            
#             if not line:
#                 current_line += 1
#                 continue
                
#             if line.startswith('**') and line.endswith(':**'):
#                 current_section = line.strip('*: ')
#                 current_line += 1
#                 continue
                
#             if line[0].isdigit() and '.' in line:
#                 try:
#                     number = line.split('.')[0].strip()
                    
#                     if '**Question:**' in line:
#                         content = line.split('**Question:**')[1].strip()
#                     else:
#                         content = line.split('.', 1)[1].strip()
#                         if content.startswith('**'):
#                             content = content.strip('*')
                    
#                     question = {
#                         'number': int(number),
#                         'section': current_section,
#                         'content': content
#                     }
                    
#                     questions.append(question)
#                 except Exception as e:
#                     print(f"Error parsing question: {line}, Error: {str(e)}")
            
#             current_line += 1
        
#         return questions
        
#     except Exception as e:
#         print(f"Error in parse_questions: {str(e)}")
#         return []
import re

# def parse_questions(raw_text):
#     """
#     Parses the raw question text into a structured format.
#     Returns a list of dictionaries containing question number, content, and section.
#     """
#     try:
#         # Ensure raw_text is a string
#         if isinstance(raw_text, dict):
#             raw_text = raw_text.get('questions', '')
#         elif not isinstance(raw_text, str):
#             print(f"Unexpected raw_text type: {type(raw_text)}")
#             raw_text = str(raw_text)

#         questions = []
#         current_section = "Question"  # Default section
        
#         # Regex pattern to extract questions in markdown-like format
#         question_pattern = r"\*\*\s*(\d+)\.\s*(.*?)\*\*\s*\n\n\*\*\s*Question:\s*\*\*\s*(.*?)\n\n"
#         matches = re.findall(question_pattern, raw_text, re.DOTALL)
        
#         if not matches:
#             print("No questions found in response. Check the input format.")
        
#         # Process extracted questions
#         for match in matches:
#             number, title, content = match
#             question = {
#                 "number": int(number.strip()),
#                 "section": current_section,
#                 "content": content.strip()
#             }
#             questions.append(question)
        
#         return questions

#     except Exception as e:
#         print(f"Error in parse_questions: {str(e)}")
#         return []

import re

# def parse_questions(raw_text):
#     """
#     Parse the raw question text into a structured format.
#     Returns a list of dictionaries containing question number, content, and section.
#     """
#     try:
#         # Ensure raw_text is a string
#         if isinstance(raw_text, dict):
#             raw_text = raw_text.get('questions', '')
#         elif not isinstance(raw_text, str):
#             print(f"Unexpected raw_text type: {type(raw_text)}")
#             raw_text = str(raw_text)

#         questions = []
#         current_section = "Question"  # Default section if none found
        
#         # Regex pattern to extract questions and their content
#         question_pattern = re.compile(r"(\*\*Question \d+:\s*.*?)\n\*\*Problem\*\*:.*?\n\n", re.DOTALL)
#         matches = question_pattern.findall(raw_text)
        
#         if not matches:
#             print("No questions found in response. Check the input format.")
        
#         # Process extracted questions
#         for match in matches:
#             # Extract question number and content
#             number_search = re.search(r"\d+", match)
#             if number_search:
#                 number = int(number_search.group())
#                 content = match.strip()
#                 question = {
#                     'number': number,
#                     'section': current_section,
#                     'content': content
#                 }
#                 questions.append(question)
        
#         return questions

#     except Exception as e:
#         print(f"Error in parse_questions: {str(e)}")
#         return []

# def parse_questions(raw_text):
#     """
#     Parse the raw question text into a structured format.
#     Returns a list of dictionaries containing question number, content, and section.
#     """
#     try:
#         # Handle different input types
#         if isinstance(raw_text, dict):
#             raw_text = raw_text.get('questions', '')
#         elif not isinstance(raw_text, str):
#             print(f"Unexpected raw_text type: {type(raw_text)}")
#             raw_text = str(raw_text)

#         questions = []
#         current_section = None
        
#         # Split the text into lines
#         lines = raw_text.split('\n')
        
#         # Find the first section header
#         for i, line in enumerate(lines):
#             if line.strip().startswith('**') and ':' in line:
#                 current_section = line.strip('*: ')
#                 current_line = i
#                 break
#         else:
#             current_line = 0
        
#         # Process each line
#         while current_line < len(lines):
#             line = lines[current_line].strip()
            
#             if not line:
#                 current_line += 1
#                 continue
                
#             if line.startswith('**') and line.endswith(':**'):
#                 current_section = line.strip('*: ')
#                 current_line += 1
#                 continue
                
#             if line[0].isdigit() and '.' in line:
#                 try:
#                     number = line.split('.')[0].strip()
                    
#                     if '**Question:**' in line:
#                         content = line.split('**Question:**')[1].strip()
#                     else:
#                         content = line.split('.', 1)[1].strip()
#                         if content.startswith('**'):
#                             content = content.strip('*')
                    
#                     question = {
#                         'number': int(number),
#                         'section': current_section,
#                         'content': content
#                     }
                    
#                     questions.append(question)
#                 except Exception as e:
#                     print(f"Error parsing question: {line}, Error: {str(e)}")
            
#             current_line += 1
        
#         return questions
        
#     except Exception as e:
#         print(f"Error in parse_questions: {str(e)}")
#         return []

import re

def parse_questions(raw_text):
    """
    Parse the raw question text into a structured format.
    Returns a list of dictionaries containing question number, content, and section.
    """
    try:
        # Handle different input types
        if isinstance(raw_text, dict):
            raw_text = raw_text.get('questions', '')
        elif not isinstance(raw_text, str):
            print(f"Unexpected raw_text type: {type(raw_text)}")
            raw_text = str(raw_text)

        questions = []
        current_section = None
        
        # Split the text into lines
        lines = raw_text.split('\n')
        
        # Find the first section header
        for i, line in enumerate(lines):
            if line.strip().startswith('**') and ':' in line:
                current_section = line.strip('*: ')
                current_line = i
                break
        else:
            current_line = 0
        
        # Process each line
        while current_line < len(lines):
            line = lines[current_line].strip()
            
            if not line:
                current_line += 1
                continue
                
            if line.startswith('**') and line.endswith(':**'):
                current_section = line.strip('*: ')
                current_line += 1
                continue
                
            if line[0].isdigit() and '.' in line:
                try:
                    number = line.split('.')[0].strip()
                    
                    if '**Question:**' in line:
                        content = line.split('**Question:**')[1].strip()
                    else:
                        content = line.split('.', 1)[1].strip()
                        if content.startswith('**'):
                            content = content.strip('*')
                    
                    question = {
                        'number': int(number),
                        'section': current_section,
                        'content': content
                    }
                    
                    questions.append(question)
                except Exception as e:
                    print(f"Error parsing question: {line}, Error: {str(e)}")
            
            current_line += 1
        
        return questions
        
    except Exception as e:
        print(f"Error in parse_questions: {str(e)}")
        return []





import json
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework import status
# import genai

# class TestQuestions(APIView):
#     # Class variable for API key
#     API_KEY = "AIzaSyBBYVqeD6eo1REqbiNYo6ylLvexyXtyvds"
    
#     def post(self, request):
#         try:
#             # Print raw request data for debugging
#             print("Raw request data:", request.data)
#             print("Request content type:", request.content_type)
            
#             # Handle both form-data and JSON input
#             if isinstance(request.data, dict):
#                 data = request.data
#             else:
#                 try:
#                     data = json.loads(request.data)
#                 except:
#                     data = request.data
                    
#             print("Processed request data:", data)
            
#             # Extract parameters
#             num_questions = data.get('num_questions')
#             if isinstance(num_questions, str):
#                 num_questions = int(num_questions)
                
#             textbook_name = data.get('textbook_name')
            
#             # Validate inputs
#             if not isinstance(num_questions, int) or num_questions <= 0:
#                 raise ValidationError("num_questions should be a positive integer.")
            
#             if not textbook_name:
#                 raise ValidationError("Textbook name is required.")
            
#             # Generate questions using class API key
#             client = genai.Client(api_key=self.API_KEY)
#             response = client.models.generate_content(
#                 model="gemini-2.0-flash",
#                 contents=f"Create {num_questions} mock questions from the book {textbook_name}"
#             )
            
#             # Extract and parse questions
#             questions_text = ""
#             for candidate in response.candidates:
#                 for part in candidate.content.parts:
#                     if hasattr(part, 'text'):
#                         questions_text += part.text
            
#             structured_questions = parse_questions(questions_text)
#             sections = sorted(list(set(q['section'] for q in structured_questions if q.get('section'))))

#             print("questions:",questions_text)
            
#             # return Response({
#             #     "questions": structured_questions,
#             #     "total_questions": len(structured_questions),
#             #     "sections": sections
#             # }, status=status.HTTP_200_OK)
#             return Response({
#                     "questions": questions_text
#                     # ,
#                     # "total_questions": len(structured_questions),
#                     # "sections": sections
#                 }, status=status.HTTP_200_OK)
            
#         except ValidationError as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except json.JSONDecodeError as e:
#             return Response({"error": "Invalid JSON format", "details": str(e)}, 
#                           status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             print(f"Error in TestQuestions.post: {str(e)}")
#             return Response(
#                 {"error": "An error occurred while generating questions.",
#                  "details": str(e)}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class TestQuestions(APIView):
    # Class variable for API key
    API_KEY = "AIzaSyBBYVqeD6eo1REqbiNYo6ylLvexyXtyvds"
    
    def post(self, request):
        try:
            # Print raw request data for debugging
            print("Raw request data:", request.data)
            print("Request content type:", request.content_type)
            
            # Handle both form-data and JSON input
            if isinstance(request.data, dict):
                data = request.data
            else:
                try:
                    data = json.loads(request.data)
                except:
                    data = request.data
                    
            print("Processed request data:", data)
            
            # Extract parameters
            num_questions = data.get('num_questions')
            if isinstance(num_questions, str):
                num_questions = int(num_questions)
                
            textbook_name = data.get('textbook_name')
            
            # Validate inputs
            if not isinstance(num_questions, int) or num_questions <= 0:
                raise ValidationError("num_questions should be a positive integer.")
            
            if not textbook_name:
                raise ValidationError("Textbook name is required.")
            
            # Generate questions using class API key
            client = genai.Client(api_key=self.API_KEY)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"Create {num_questions} mock questions from the book {textbook_name}"
            )
            
            # Extract and parse questions
            questions_text = ""
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, 'text'):
                        questions_text += part.text
            
            structured_questions = parse_questions(questions_text)
            print(questions_text)

            print("Parsed questions:", structured_questions)

            # Convert to JSON array of objects format
            json_response = {
                # "questions": structured_questions,
                "questions": questions_text,
                "total_questions": len(structured_questions),
                "sections": sorted(list(set(q['section'] for q in structured_questions if q.get('section'))))
            }
            
            return Response(json_response, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except json.JSONDecodeError as e:
            return Response({"error": "Invalid JSON format", "details": str(e)}, 
                          status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error in TestQuestions.post: {str(e)}")
            return Response(
                {"error": "An error occurred while generating questions.",
                 "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
