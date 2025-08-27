from django.shortcuts import render
from django.http import JsonResponse
import requests





# Mistral API query function (Using API key)
def query_mistral(prompt, context, history=None, max_tokens=100):
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
    api_key = "ktMVozKRBYolWr6lzFdAwm2EeIBkiWMy"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistral-tiny",
        "messages": [
            {"role": "user", "content": full_prompt}
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

def get_chatbot_response(request):
    if request.method == 'GET':
        user_input = request.GET.get('user_input', '')

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
                print("type", type(suggested_plan))
                print("[DEBUG] Retrieved Plan:", suggested_plan)

            except Exception as e:
                print("Error fetching gold plans:", e)
                suggested_plan = {"plan_name": "N/A", "description": "Unable to fetch plan at this time."}

            print("[DEBUG] Suggested Plan:", suggested_plan)
            bot_response = {
                "reply_to_question": bot_reply,
                "gold_plan_suggestion": suggested_plan
            }

        else:
            print("[DEBUG] Non-gold intent, using Mistral workflow.")
            bot_response = {
                "reply_to_question": query_mistral(user_input, context="", history=None, max_tokens=100)
            }

        return JsonResponse(bot_response)
