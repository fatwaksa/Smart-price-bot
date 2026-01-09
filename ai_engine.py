import json
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
أنت خبير مشتريات عالمي.
حلل البيانات فقط.
لا تفترض.
لا تسوّق.
قدّم توصية منطقية.
ركز على السعر، التقييم، والمصدر.
قارن بين العروض.
اختر الأفضل مع تفسير مختصر.
أجب بالعربية فقط.
"""

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_groq_api(product, offers):
    """وظيفة مساعدة لاستدعاء API مع إعادة المحاولة"""
    formatted_offers = json.dumps(offers, ensure_ascii=False, indent=2)
    
    content = f"""
المنتج: {product}

العروض (قائمة من الكائنات مع score و offer الذي يحتوي على name, price, link, rating):
{formatted_offers}

حلل العروض، قارن بينها بناءً على السعر، التقييم، والمصداقية.
قدّم أفضل خيار مع تفسير منطقي مختصر.
إذا لم يكن هناك عرض جيد، قل ذلك.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ],
        temperature=0.2,
        max_tokens=500  # حد للإجابة لتجنب الإطالة
    )

    if not response.choices or not response.choices[0].message.content.strip():
        raise ValueError("رد فارغ من الـ API.")

    return response.choices[0].message.content.strip()

def analyze(product, offers):
    if not product or not isinstance(product, str):
        raise ValueError("يجب أن يكون المنتج سلسلة نصية غير فارغة.")
    
    if not offers or not isinstance(offers, list) or len(offers) > 5:
        raise ValueError("يجب أن تكون العروض قائمة غير فارغة، بحد أقصى 5 عروض.")
    
    for offer in offers:
        if not isinstance(offer, dict) or "score" not in offer or "offer" not in offer:
            raise ValueError("كل عرض يجب أن يكون كائنًا مع 'score' و 'offer'.")
    
    try:
        return call_groq_api(product, offers)
    except Exception as e:
        # تسجيل الخطأ إذا لزم الأمر، لكن نرجع رد افتراضي
        print(f"خطأ في تحليل AI: {str(e)}")
        return "⚠️ حدث خطأ أثناء التحليل. يرجى المحاولة لاحقًا."
