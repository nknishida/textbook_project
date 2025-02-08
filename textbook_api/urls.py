from django.urls import path
from .views import UploadTextbook, GenerateQuestions, TestQuestions

urlpatterns = [
    # Endpoint to upload a textbook
    path('upload-textbook/', UploadTextbook.as_view(), name='upload-textbook'),

    # Endpoint to generate questions from a textbook
    path('generate-questions/', GenerateQuestions.as_view(), name='generate-questions'),
    # Endpoint to generate questions from a textbook
    path('test-questions/', TestQuestions.as_view(), name='test-questions'),
]