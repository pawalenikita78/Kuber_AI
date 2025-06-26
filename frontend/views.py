from django.shortcuts import render
from django.http import JsonResponse
import PyPDF2
from langchain.text_splitter import CharacterTextSplitter
import requests
import os



# 1. Extract PDF Text
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text()
    return text

# Load and prepare PDF text once
pdf_text = extract_text_from_pdf(r"C:\Desktop\Safety_Chatbot\general_safety_rules.pdf")

# Split the text into chunks
splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_text(pdf_text)

# Mistral API query function (Using API key)
def query_mistral(prompt, context, history=None):
    # Build conversation history string
    history_str = ""
    if history:
        for h in history:
            history_str += f"User: {h['user']}\nAssistant: {h['bot']}\n"
    # Add the current prompt as the latest user message
    history_str += f"User: {prompt}\n"

    full_prompt = (
        "You are a polite, helpful assistant. "
        "You can answer general questions like greetings, goodbyes, casual conversations, or polite phrases in a friendly way using your general knowledge. "
        "For all other questions, only use the information provided in the context below. "
        "If the next question is based on a previous question, answer using the given document and previous answers. "
        "If you do not know the answer, reply exactly: 'Sorry, the answer is not available.'\n\n"
        f"Here is the document context:\n{context}\n\n"
        f"Conversation history:\n{history_str}"
    )

    api_url = "https://api.mistral.ai/v1/chat/completions"
    api_key = "p3TWNjZ8YQ0gGJRU4DWcf7o8avLqfuZ9"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistral-tiny",
        "messages": [
            {"role": "user", "content": full_prompt}
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"].strip()
        return answer
    except Exception as e:
        print("Error communicating with Mistral API:", e)
        return "Sorry, I could not get a response from the chatbot server."

# 2. View to Render the Chatbot UI
def chatbot_home(request):
    return render(request, 'chatbot.html')

# 3. View to Handle Chatbot Input
def get_chatbot_response(request):
    if request.method == 'GET':
        user_input = request.GET.get('user_input', '')

        # Find the most relevant chunks using keyword matching
        relevant_chunks = []
        user_words = set(user_input.lower().split())
        for chunk in chunks:
            chunk_words = set(chunk.lower().split())
            if user_words & chunk_words:
                relevant_chunks.append(chunk)

        # Use up to 2 most relevant chunks, or fallback to the first chunk
        if relevant_chunks:
            context = " ".join(relevant_chunks[:2])
        elif len(chunks) > 0:
            context = chunks[0]
        else:
            context = ""

        # Get conversation history from session
        history = request.session.get('chat_history', [])
        # Only keep the last 5 exchanges for brevity
        history = history[-5:]

        # Query Mistral with history
        bot_response = query_mistral(user_input, context, history)

        # Update conversation history in session
        history.append({'user': user_input, 'bot': bot_response})
        request.session['chat_history'] = history

        return JsonResponse({'response': bot_response})



'''
from django.shortcuts import render
from django.http import JsonResponse
import PyPDF2
from langchain.text_splitter import CharacterTextSplitter
import requests

# 1. Extract PDF Text
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text()
    return text

# Load and prepare PDF text once
pdf_text = extract_text_from_pdf("C:\Desktop\Safety_Chatbot\general_safety_rules.pdf")

# Split the text into chunks
splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_text(pdf_text)

# LLaMA query function
def query_llama(prompt, context):
    full_prompt = (
        "You are a helpful assistant. Answer the question ONLY using the information in the context below. "
        "If the answer is not present in the context, reply exactly: "
        "'Sorry, the answer is not available in the provided document.'\n\n"
        f"Context:\n{context}\n\nQuestion: {prompt}"
    )
    response = requests.post(
        "p3TWNjZ8YQ0gGJRU4DWcf7o8avLqfuZ9",
        json={"message": full_prompt}
    )
    try:
        answer = response.json()["response"]
        return answer
    except Exception as e:
        print("Error parsing JSON:", e)
        print("Raw response:", response.text)
        return "Sorry, I could not get a response from the chatbot server."

# 2. View to Render the Chatbot UI
def chatbot_home(request):
    return render(request, 'chatbot.html')

# 3. View to Handle Chatbot Input
def get_chatbot_response(request):
    if request.method == 'GET':
        user_input = request.GET.get('user_input', '')

        # Find the most relevant chunks using keyword matching
        relevant_chunks = []
        user_words = set(user_input.lower().split())
        for chunk in chunks:
            chunk_words = set(chunk.lower().split())
            if user_words & chunk_words:
                relevant_chunks.append(chunk)

        # Use up to 2 most relevant chunks, or fallback to the first chunk
        if relevant_chunks:
            context = " ".join(relevant_chunks[:2])
        elif len(chunks) > 0:
            context = chunks[0]
        else:
            context = ""

        bot_response = query_llama(user_input, context)
        return JsonResponse({'response': bot_response})


'''
# from django.shortcuts import render
# from django.http import JsonResponse
# import requests

# # 1. View to Render the Chatbot UI
# def chatbot_home(request):
#     return render(request, 'chatbot.html')

# # 2. View to Handle Chatbot Input and Directly Query the LLaMA Model
# def get_chatbot_response(request):
#     if request.method == 'GET':
#         user_input = request.GET.get('user_input', '')

#         # Send user input directly to LLaMA model API
#         try:
#             response = requests.post(
#                 "https://36dc-34-34-94-240.ngrok-free.app/generate",  # Replace with your actual Colab API endpoint
#                 json={"message": user_input}
#             )
#             bot_response = response.json().get("response", "Sorry, I could not understand your question.")
#         except Exception as e:
#             print("Error:", e)
#             bot_response = "Sorry, I could not get a response from the chatbot server."

#         return JsonResponse({'response': bot_response})
