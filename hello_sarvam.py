import os
from sarvamai import SarvamAI

# Load .env (simple parser, no extra dependency)
try:
    with open(".env") as f:
        for line in f:
            k, _, v = line.strip().partition("=")
            if k and v:
                os.environ.setdefault(k, v)
except FileNotFoundError:
    pass

client = SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])

response = client.chat.completions(
    model="sarvam-105b-conversations",
    messages=[{"role": "user", "content": "Say hello in Hindi and English."}],
)
print(response.choices[0].message.content)
