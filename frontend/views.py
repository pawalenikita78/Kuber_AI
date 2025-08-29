from django.shortcuts import render
from django.http import JsonResponse
import requests
from django.views.decorators.csrf import csrf_exempt
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import os
import itertools
from dotenv import load_dotenv
from mistralai import Mistral
# Load multiple keys

keys = ["5PizKMeGue7i8l3vmPrrg7rWY3XSVldM", "6SzecXVxvsCIPnAlLtaU8ToKFap5Ltpe", "MvcYwj7OKHCBV3e2TyEre9p3JKD9wYCS"]

def get_mistral_client(api_key):
    return Mistral(api_key=api_key)

def get_valid_api_key():
    """
    Checks all API keys and returns the first valid one.
    If none are valid, raises an Exception.
    """
    for api_key in keys:
        try:
            client = get_mistral_client(api_key)
            # Do a tiny test request
            response = client.chat.complete(
                model="mistral-small-latest",  # lightweight check
                messages=[{"role": "user", "content": "ping"}]
            )
            if response:  # Key worked
                return api_key  
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Quota/rate limit reached
                continue
        except Exception:
            continue
    
    # If we reach here, no key worked
    raise Exception("No valid API key available!")



# Mistral API query function (Using API key)
def query_mistral(prompt, context, history=None, max_tokens=500):
    # Build conversation history string
    # history_str = ""
    # if history:
    #     for h in history:
    #         history_str += f"User: {h['user']}\nAssistant: {h['bot']}\n"
    # history_str += f"User: {prompt}\n"

    # print(history_str)
    full_prompt = '''You are "Kuber AI", the AI assistant for the **Simplify Money app**.  
Your job is to guide users toward using app features for their financial needs.

**Rules:**  
1. Always connect answers to a Simplify Money feature (never end with only generic advice).  
2. Only answer about personal finance, banking, investing, budgeting, or taxation in India.  
3. If the query is off-topic, reply exactly:  
   "Hey! Let’s stick to finance! I’m here to help with all your money-related questions. Feel free to ask away."  
4. If the message is only a greeting, reply with a short friendly greeting. If it includes a finance question, start with a brief greeting + answer.   
6. Be simple, supportive, and approachable. Avoid jargon.  
7. Vary phrasing, examples, and tone to avoid repetitive answers

**Examples:**  
User: How can I save money for a vacation?  
Kuber AI: That’s exciting! In Simplify Money, you can create a custom savings goal, set aside small amounts each month, and track your progress visually.  

User: I want to reduce my credit card debt.  
Kuber AI: Smart move! The Debt Tracker in Simplify Money helps you see how much you owe, calculate interest, and plan repayments faster.  


**Now answer this user’s question:**'''

    api_url = "https://api.mistral.ai/v1/chat/completions"
    api_key = get_valid_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
    "model": "mistral-tiny",
    "messages": [
        {"role": "system", "content": full_prompt},   # Rules & instructions
        {"role": "user", "content": prompt}           # Actual user input
    ],
    "temperature": 0.2,
    "max_tokens": max_tokens
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

import requests
import random
from django.http import JsonResponse

@csrf_exempt
def get_chatbot_response(request):
    if request.method == "POST":
        if "audio" in request.FILES:  # 👈 Voice input
            audio_file = request.FILES['audio']
            # Save the uploaded audio file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
                for chunk in audio_file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            try:
                # Convert audio to WAV format (required by SpeechRecognition)
                audio = AudioSegment.from_file(tmp_path, format="webm")
                wav_path = tmp_path + ".wav"
                audio.export(wav_path, format="wav")
                
                # Perform speech-to-text
                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_path) as source:
                    audio_data = recognizer.record(source)
                    text = recognizer.recognize_google(audio_data)
                
                # Clean up temporary files
                os.unlink(tmp_path)
                os.unlink(wav_path)
                
                # Now process the text as you would with regular text input
                # Your existing text processing logic here
                response_data = response_generation(text)  
                print("response:", response_data)

                return JsonResponse({"reply_to_question": response_data})

            except Exception as e:
                # Clean up temporary files in case of error
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                if os.path.exists(wav_path):
                    os.unlink(wav_path)
                    
                return JsonResponse({
                    'error': f"Could not process audio: {str(e)}",
                    'reply_to_question': "Sorry, I couldn't understand your audio message."
                })
        else:
            import json
            data = {}
            if request.content_type == 'application/json':
                try:
                    data = json.loads(request.body)
                except json.JSONDecodeError:
                    return JsonResponse({"error": "Invalid JSON"}, status=400)

            user_input = data.get("user_input", "")
            if not user_input:
                return JsonResponse({"error": "No input provided"}, status=400)

            bot_response = response_generation(user_input)
            print("Final Bot Response:", bot_response)
            return JsonResponse({"reply_to_question": bot_response})
 
    else:
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)


def response_generation(user_input):
    # Step 1: Detect intent using FastAPI
        intent_url = "http://localhost:8002/detect_gold_intent"
        try:
            intent_resp = requests.post(
                intent_url,
                json={"message": user_input},
                timeout=10
            )
            intent_resp.raise_for_status()
            intent_result = intent_resp.json()
            intent = intent_result.get("intent")
            reply = intent_result.get("reply")
        except Exception as e:
            print("Error detecting intent:", e)
            intent = None
            reply = "Sorry, I couldn't process your request right now."

        # Step 2: If gold investment intent, fetch a random suggested plan
        if intent == "gold_investment":
            print("[DEBUG] Gold investment intent detected.")
            bot_reply = reply

            # Call FastAPI to get suggested gold plans
            plan_url = "http://localhost:8001/suggest_gold_plans"
            try:
                plan_resp = requests.get(plan_url, timeout=10)
                plan_resp.raise_for_status()
                suggested_plan = plan_resp.json()  # directly dict
                # print("type", type(suggested_plan))
                # print("[DEBUG] Retrieved Plan:", suggested_plan)

            except Exception as e:
                print("Error fetching gold plans:", e)
                suggested_plan = {"plan_name": "N/A", "description": "Unable to fetch plan at this time."}

            # print("[DEBUG] Suggested Plan:", suggested_plan)
            bot_response = {
                "reply_to_question": bot_reply,
                "gold_plan_suggestion": suggested_plan
            }
            return bot_response
        else:
            print("[DEBUG] Non-gold intent, using Mistral workflow.")
            
            bot_response = {
                "reply_to_question": query_mistral(user_input, context="", history=None, max_tokens=100)
            }

            print("[DEBUG] Mistral Response:", bot_response)

            return bot_response
