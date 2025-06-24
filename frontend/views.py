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
        "https://4c39-34-147-116-224.ngrok-free.app/generate",
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
