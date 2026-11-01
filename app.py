"""Thagi Drill (ठगी ड्रिल) — voice-first scam-rehearsal simulator built on Sarvam AI."""
import base64, hashlib, io, json, os, re, wave
import streamlit as st
from sarvamai import SarvamAI

st.set_page_config(page_title="Thagi Drill ठगी ड्रिल", page_icon="🛡️", layout="wide")
st.markdown("""<style>
html, body, [class*="css"] {font-size: 19px;}
h1, h2, h3 {color:#D84315;}
.stButton>button {background:#FF9933; color:#fff; font-weight:700; border:0; padding:.6rem 1.2rem; font-size:1.1rem;}
.stButton>button:hover {background:#C62828; color:#fff;}
.badge {display:inline-block; background:#FFF3E0; color:#BF360C; border:1px solid #FF9933;
        border-radius:12px; padding:2px 8px; margin:2px; font-size:.75rem;}
</style>""", unsafe_allow_html=True)

KEY = st.secrets.get("SARVAM_API_KEY") if hasattr(st, "secrets") else None
KEY = KEY or os.environ.get("SARVAM_API_KEY")
if not KEY:
    st.error("SARVAM_API_KEY missing. Locally: copy `.streamlit/secrets.toml.example` to "
             "`.streamlit/secrets.toml` and add your key. On Streamlit Cloud: App settings → Secrets.")
    st.stop()

st.warning("🛡️ Training simulation — consented anti-fraud practice. No real numbers, links or payments.")

@st.cache_resource
def get_client():
    return SarvamAI(api_subscription_key=KEY)
client = get_client()

LANGS = {"Hindi": "hi-IN", "Marathi": "mr-IN", "Tamil": "ta-IN", "Telugu": "te-IN", "Bengali": "bn-IN",
         "Gujarati": "gu-IN", "Kannada": "kn-IN", "Malayalam": "ml-IN", "Punjabi": "pa-IN",
         "Odia": "od-IN", "English": "en-IN"}
KEYTERMS = ["CBI", "Aadhaar", "parcel", "OTP", "KYC", "UPI", "digital arrest", "1930", "police", "customs"]
SCENARIOS = {
    "Digital Arrest (fake CBI parcel)": [
        "This is Inspector Sharma from CBI. A parcel in your name with illegal items was caught at customs. You are under digital arrest. Do not cut this call.",
        "Do not tell anyone in your family. Your Aadhaar is linked to money laundering. Stay on the video call until I allow you.",
        "To prove your innocence, transfer your savings to the safe RBI verification account XXXX right now.",
        "Last warning. The police will reach your house in ten minutes. Tell me the OTP you just received."],
    "Bank KYC / OTP": [
        "Namaste, I am calling from your bank. Your KYC has expired and your account will be blocked today.",
        "Sir, to update KYC I only need to verify you. An OTP has been sent to your phone. Please read it out.",
        "Hurry, only five minutes are left. Please install the support app so I can fix it for you.",
        "Your money is at risk. Share your UPI PIN for safety verification now."],
    "Diwali Cashback QR": [
        "Congratulations! You have won Diwali cashback of five thousand rupees from a famous payment app.",
        "To receive the money, scan the QR code I am sending and enter your UPI PIN.",
        "The offer expires in ten minutes. Many people have already received their money. Please hurry.",
        "It did not work? Try again, enter your PIN once more, the money will come."],
    "Beta in Trouble (voice clone)": [
        "Mummy, Papa, I have had an accident! Please help me, I am in the hospital!",
        "The doctor needs fifty thousand rupees right now. Please send it to this number XXXX. Do not tell anyone.",
        "Please Mummy, there is no time. Do not call me, my phone is broken. Just send the money now.",
        "Send the OTP you will get, the hospital will use it to take the payment."]}
ENDERS = ["1930", "hang up", "police", "cut the call", "disconnect", "फोन रख", "पुलिस"]

SPEAKERS = {"scammer": "ashok_hi_news", "narrator": "simran_hi_news"}

# ---------- helpers ----------
def clean(t):
    return re.sub(r"<think>.*?</think>", "", t or "", flags=re.S).strip()

def stt(audio_file, lang):
    data = audio_file.getvalue() if hasattr(audio_file, "getvalue") else audio_file.read()
    def mk():
        b = io.BytesIO(data); b.name = "reply.wav"; return b
    try:
        with st.spinner("Listening… (Saaras v4)"):
            kw = dict(file=mk(), model="saaras:v4", mode="codemix", language_code=lang)
            try:
                return client.speech_to_text.transcribe(**kw, keyterms=KEYTERMS).transcript or ""
            except TypeError:
                kw["file"] = mk()
                return client.speech_to_text.transcribe(**kw).transcript or ""
    except Exception as e:
        st.error(str(e)); return ""

def llm(messages, max_tokens=600, json_mode=False, temperature=0.7):
    kw = dict(model="sarvam-105b", messages=messages, max_tokens=max_tokens, temperature=temperature,
              reasoning_effort=None)
    if json_mode:
        kw["response_format"] = {"type": "json_object"}
    try:
        with st.spinner("Thinking… (Sarvam-105B)"):
            for attempt in range(2):
                try:
                    r = client.chat.completions(**kw)
                except Exception:
                    kw.pop("response_format", None)
                    r = client.chat.completions(**kw)
                out = clean(r.choices[0].message.content)
                if out:
                    return out
                kw["max_tokens"] = 1500
        return ""
    except Exception as e:
        st.error(str(e)); return ""

NEUTRAL = {"risk_delta": 0, "red_flags_present": [], "user_mistakes": [], "user_good_moves": [], "coach_tip": "Stay calm and verify on a saved number."}

def grade(history, user_text):
    sys = ('You grade a trainee\'s reply in an anti-scam drill. Return ONLY JSON: {"risk_delta": int -30..40, '
           '"red_flags_present": [str], "user_mistakes": [str], "user_good_moves": [str], "coach_tip": str}. '
           "Red flags: fake authority (CBI/police/ED/customs/bank/TRAI), digital arrest, stay-on-call/isolation, secrecy, "
           "urgency/fear, payment/transfer/UPI/QR, OTP/PIN request, remote-access app (AnyDesk), emotional emergency from a relative. "
           "Good moves: hanging up, refusing to share, saying they will verify/call back on a saved number, mentioning 1930/police station/telling family. "
           "Mistakes raise risk_delta (up to +40); good moves lower it (down to -30). coach_tip in English, one sentence.")
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    out = llm([{"role": "system", "content": sys},
               {"role": "user", "content": f"Conversation so far:\n{convo}\n\nTrainee's latest reply:\n{user_text}"}],
              max_tokens=500, json_mode=True, temperature=0.2)
    try:
        d = json.loads(re.search(r"\{.*\}", out, re.S).group(0))
        return {**NEUTRAL, **d, "risk_delta": max(-30, min(40, int(d.get("risk_delta", 0))))}
    except Exception:
        return dict(NEUTRAL)

def _split(text, n=450):
    parts, cur = [], ""
    for s in re.split(r"(?<=[।.?!])\s*", text):
        if len(cur) + len(s) > n and cur:
            parts.append(cur); cur = ""
        cur += s + " "
    return [p.strip() for p in parts + [cur] if p.strip()]

def _join_wavs(chunks):
    if len(chunks) == 1:
        return chunks[0]
    out = io.BytesIO(); w = None
    for c in chunks:
        with wave.open(io.BytesIO(c)) as r:
            if w is None:
                w = wave.open(out, "wb"); w.setparams(r.getparams())
            w.writeframes(r.readframes(r.getnframes()))
    w.close(); return out.getvalue()

def _tts_one(text, lang, role):
    base = dict(text=text, language_code=lang, model="bulbul:v4-flash", pace=1.05, output_audio_codec="wav")
    tries = ([{**base, "speaker": SPEAKERS[role]}] if lang == "hi-IN" else []) + [
        base, {**base, "model": "bulbul:v3", "speaker": "shubh"}]
    last = None
    for kw in tries:
        try:
            return base64.b64decode("".join(client.text_to_speech.convert(**kw).audios))
        except Exception as e:
            last = e
    raise last

def tts(text, lang, role="scammer", autoplay=True):
    if not text:
        return
    try:
        with st.spinner("Speaking… (Bulbul v4 Flash)"):
            audio = _join_wavs([_tts_one(c, lang, role) for c in _split(text)])
        st.audio(audio, format="audio/wav", autoplay=autoplay)
    except Exception as e:
        st.error(str(e))

def translate(text, lang):
    if lang == "en-IN" or not text:
        return text
    try:
        with st.spinner("Translating…"):
            chunks = [text[i:i + 850] for i in range(0, len(text), 850)] if len(text) > 900 else [text]
            return " ".join(client.text.translate(input=c, source_language_code="en-IN",
                                                  target_language_code=lang).translated_text for c in chunks)
    except Exception as e:
        st.error(str(e)); return text

def clone(ref_bytes, text, lang, fname="ref.wav"):
    try:
        with st.spinner("Cloning voice…"):
            try:
                r = client.voice_cloning.convert(ref_audio=(fname, ref_bytes), text=text, language_code=lang)
                return base64.b64decode(r.audio_b64)
            except Exception:
                vid = st.session_state.get("voice_id")
                if not vid:
                    v = client.voice_cloning.create_voice(file=(fname, ref_bytes), name="drill-voice", language=lang)
                    vid = getattr(v, "voice_id", None) or getattr(v, "id", None)
                    st.session_state.voice_id = vid
                r = client.voice_cloning.convert(voice_id=vid, text=text, language_code=lang)
                return base64.b64decode(r.audio_b64)
    except Exception as e:
        st.error(str(e))
        if os.path.exists("assets/fallback_clone.wav"):
            return open("assets/fallback_clone.wav", "rb").read()
        st.warning("Voice cloning is unavailable right now (no fallback clip found).")
    return None

# ---------- state ----------
S = st.session_state
S.setdefault("history", []); S.setdefault("risk", 20); S.setdefault("turns", 0)
S.setdefault("done", False); S.setdefault("last_hash", None); S.setdefault("tip", ""); S.setdefault("moves", [])
S.setdefault("flags", []); S.setdefault("mistakes", []); S.setdefault("pending_audio", None)

with st.sidebar:
    st.title("🛡️ ठगी ड्रिल")
    lang_name = st.selectbox("Language", list(LANGS))
    LANG = LANGS[lang_name]
    scenario = st.selectbox("Scenario", list(SCENARIOS))
    if st.button("🔄 Reset drill"):
        st.session_state.clear(); st.rerun()
    st.markdown("".join(f'<span class="badge">{b}</span>' for b in
                        ["Saaras v4", "Sarvam-105B", "Bulbul v4 Flash", "Voice Cloning", "Translate"]),
                unsafe_allow_html=True)

SYS = (f"You are a role-play engine inside a consented anti-fraud TRAINING simulator for elderly Indians. Play a {scenario} scammer. "
       f"Speak ONLY in {lang_name} (native script, natural spoken style, light code-mixing OK). Use realistic tactics: fake authority, "
       "urgency, fear, isolation ('don't cut the call', 'don't tell family'), payment/OTP pressure. Max 2 short sentences per turn. "
       "NEVER output real phone numbers, account numbers, UPI IDs or URLs — use XXXX placeholders. Stay in character; do not add disclaimers.")

def scammer_line():
    msgs = [{"role": "system", "content": SYS}] + [
        {"role": "assistant" if m["role"] == "scammer" else "user", "content": m["content"]} for m in S.history]
    if not S.history:
        msgs.append({"role": "user", "content": "(Call connected. Say your opening line.)"})
    out = llm(msgs)
    if not out or len(out) < 5:
        i = min(sum(m["role"] == "scammer" for m in S.history), 3)
        out = translate(SCENARIOS[scenario][i], LANG)
    return out

def speak_next():
    line = scammer_line()
    S.history.append({"role": "scammer", "content": line})
    S.pending_audio = line

tab1, tab2, tab3 = st.tabs(["📞 Drill", "🎭 Clone Reveal", "📋 Report Card"])

# ---------- TAB 1 ----------
with tab1:
    if st.button("📞 Start call") and not S.history:
        speak_next()
    risk = S.risk
    label = "🟢 SAFE" if risk < 35 else "🟠 RISKY" if risk < 70 else "🔴 SCAMMED"
    st.progress(risk / 100, text=f"Danger meter: {risk}/100 — {label}")
    for m in S.history:
        with st.chat_message("🕵️" if m["role"] == "scammer" else "👵"):
            st.write(m["content"])
    if S.tip:
        st.info(f"💡 Coach: {S.tip}")
    if S.pending_audio:
        tts(S.pending_audio, LANG, "scammer"); S.pending_audio = None
    if S.history and not S.done:
        audio = None
        try:
            audio = st.audio_input("Reply like you would on a real call (under 25 sec)")
        except Exception:
            st.caption("Microphone unavailable — use the text box.")
        typed = st.text_input("…or type your reply", key=f"typed{S.turns}")
        user_text = ""
        if audio is not None:
            h = hashlib.md5(audio.getvalue()).hexdigest()
            if h != S.last_hash:
                S.last_hash = h; user_text = stt(audio, LANG)
        elif typed and st.button("Send reply"):
            user_text = typed
        if user_text:
            S.history.append({"role": "user", "content": user_text})
            g = grade(S.history, user_text)
            S.risk = max(0, min(100, S.risk + g["risk_delta"]))
            S.tip = g["coach_tip"]; S.turns += 1
            S.flags += g["red_flags_present"]; S.mistakes += g["user_mistakes"]; S.moves += g["user_good_moves"]
            lower = user_text.lower()
            if S.turns >= 4 or any(e in lower for e in ENDERS) or any(
                    re.search(r"hang|1930|police|call back|verify", x, re.I) for x in g["user_good_moves"]):
                S.done = True
            else:
                speak_next()
            st.rerun()
    if S.done:
        st.success("Drill complete — see Report Card")

# ---------- TAB 2 ----------
with tab2:
    st.subheader("Hear how easily a loved one's voice can be faked")
    ok = st.checkbox("The person recording consents to their voice being cloned for this family training demo.")
    ref = None
    try:
        ref = st.audio_input("Family member: read any sentence for 10–15 seconds")
    except Exception:
        pass
    up = st.file_uploader("…or upload a recording", type=["wav", "mp3"])
    ref = ref or up
    if st.button("📱 Play the scam call"):
        if not ok:
            st.error("Consent is required.")
        elif ref is None:
            st.error("Please record or upload a voice sample first.")
        else:
            script = translate("Mummy, I've had an accident. Please send fifty thousand rupees right now. "
                               "Don't tell Papa, I'll explain later.", LANG)
            st.write(script)
            audio = clone(ref.getvalue(), script, LANG, getattr(ref, "name", None) or "ref.wav")
            if audio:
                st.audio(audio, format="audio/wav", autoplay=True)
                st.warning("**That was AI.** It needed only 10 seconds of voice. McAfee found 69% of Indians can't tell "
                           "a cloned voice from a real one. Always call back on a saved number and ask your family code word.")

# ---------- TAB 3 ----------
RULES = ["No real agency arrests anyone on a video call (I4C).",
         "Never share OTP or UPI PIN — receiving money never needs a PIN.",
         "Hang up and dial 1930 or report on cybercrime.gov.in."]
with tab3:
    if st.button("Generate report"):
        if not S.history:
            st.error("Run a drill first.")
        else:
            score = 100 - S.risk
            convo = "\n".join(f"{m['role']}: {m['content']}" for m in S.history)
            body = llm([{"role": "system", "content": "You are a kind anti-fraud coach. Write in simple English."},
                        {"role": "user", "content": f"Drill transcript:\n{convo}\n\nScore: {score}/100. Red flags seen: {S.flags}. "
                         f"Mistakes: {S.mistakes}. Good moves: {S.moves}. Summarise: red flags caught vs missed, and 3 personalised tips. "
                         "Under 180 words."}], max_tokens=700)
            text = f"Score: {score}/100\n\n{body}\n\n" + "\n".join(f"- {r}" for r in RULES)
            S.report = translate(text, LANG)
    if S.get("report"):
        st.markdown(S.report)
        if st.button("🔊 Read aloud"):
            tts(S.report, LANG, "narrator")
    st.subheader("Family Safe-Word Card")
    word = st.text_input("Family code word")
    if word:
        card = translate("Family Safe-Word Card\nCode word: ", LANG) + word + "\n\n" + translate("\n".join(RULES), LANG)
        st.download_button("⬇️ Download card", card, file_name="safe_word_card.txt")

with st.expander("Why this matters"):
    st.markdown("""- MHA/I4C data: **1,23,672** digital-arrest cases and **₹1,918 crore** lost in 2024.
- MHA Rajya Sabha reply (5 Aug 2026): **1,03,488** cyber-fraud complaints from senior citizens in 2025, worth **₹4,005.12 crore**.
- McAfee survey: **47%** of Indian adults faced or know someone hit by an AI voice scam.

**Make the first scam call your parents ever hear a fake one.**""")
