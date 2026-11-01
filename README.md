# Thagi Drill (ठगी ड्रिल)
Make the first scam call your parents ever hear a fake one — a voice-first scam-rehearsal simulator in 11 Indian languages.

## Features
- Live scam-call drill (digital arrest, bank KYC/OTP, Diwali cashback QR, "beta in trouble") with a danger meter and coach tips
- Speak your reply; the app transcribes, grades and escalates the scammer
- Clone Reveal: consented voice-clone demo showing how little audio a fake needs
- Report card + downloadable family safe-word card, translated and read aloud

## Sarvam APIs used
Saaras v4 (speech-to-text) · Sarvam-105B (chat) · Bulbul v4 Flash (text-to-speech) · Voice Cloning · Translate

## Run locally
```
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # add your key
streamlit run app.py
```

## Deploy on Streamlit Cloud
1. Push this repo to GitHub.
2. share.streamlit.io → New app → pick repo and `app.py`.
3. Advanced settings → Secrets: `SARVAM_API_KEY = "..."` → Deploy.

## Impact
- 1,23,672 digital-arrest cases and ₹1,918 crore lost in 2024 (MHA/I4C)
- 1,03,488 senior-citizen cyber-fraud complaints in 2025, ₹4,005.12 crore (MHA, Rajya Sabha, 5 Aug 2026)
- 47% of Indian adults faced or know someone hit by an AI voice scam (McAfee)
