import os
import requests

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = "llama3-13b"  # استخدم موديل مدعوم حاليًا

def analyze(product, offers):
    """
    تحليل الذكاء الاصطناعي للعروض الأفضل باستخدام Groq API
    """
    prompt = f"Product: {product}\nOffers: {offers}\nPlease summarize and recommend the best option clearly."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": GROQ_MODEL,
        "prompt": prompt,
        "max_output_tokens": 400,
        "temperature": 0.2
    }

    response = requests.post("https://api.groq.com/v1/completions", json=data, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Groq API Error: {response.status_code} - {response.text}")
    
    result = response.json()
    return result['completion']  # حسب شكل الاستجابة الجديد من Groq
