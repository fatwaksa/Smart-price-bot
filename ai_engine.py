from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
أنت خبير مشتريات عالمي.
حلل البيانات فقط.
لا تفترض.
لا تسوّق.
قدّم توصية منطقية.
"""

def analyze(product, offers):
    content = f"""
المنتج: {product}

العروض:
{offers}

حلل وقدّم أفضل خيار.
"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content
