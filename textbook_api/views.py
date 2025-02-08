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

    def post(self, request):
        file = request.FILES.get('file')
        if file:
            textbook = Textbook.objects.create(name=request.data.get('name'), file=file)
            return Response({"message": "Textbook uploaded successfully!", "id": textbook.id})
        return Response({"error": "No file uploaded"}, status=400)

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
    
class TestQuestions(APIView):
    
    def post(self, request):
        client = genai.Client(api_key="AIzaSyBBYVqeD6eo1REqbiNYo6ylLvexyXtyvds")
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents="Create 10 mock qusetions from the book Introduction to C programming by Dennis Richie"
        )
        print(response)
        return Response({"questions": response})
        