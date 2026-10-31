"""Reusable browser-based voice assistant for the JanSahay prototype."""

from __future__ import annotations

import html
import json

import streamlit as st

from .i18n import LANGUAGE_LOCALES

_REPLIES = {
    "English": {
        "documents": "Check the selected scheme's document list. Demonstration examples may include identity proof, a land record, or a bank passbook.",
        "status": "Open Request Tracking to see each request's current stage and any pending documents.",
        "scheme": "Open Scheme Finder to compare your details with separate sample rules. These are not official eligibility decisions.",
        "general": "You can ask about schemes, required documents, or request status. This assistant uses simple local demonstration rules.",
    },
    "Telugu": {
        "documents": "ఎంచుకున్న పథకానికి అవసరమైన పత్రాల జాబితాను చూడండి. నమూనా పత్రాల్లో గుర్తింపు పత్రం, భూమి రికార్డు లేదా బ్యాంకు పాస్‌బుక్ ఉండవచ్చు.",
        "status": "ప్రతి అభ్యర్థన దశను, ఇంకా సమర్పించాల్సిన పత్రాలను చూడటానికి అభ్యర్థన స్థితి పేజీని తెరవండి.",
        "scheme": "మీ వివరాలను వేర్వేరు నమూనా నియమాలతో పోల్చడానికి పథకాల అన్వేషణను తెరవండి. ఇవి అధికారిక అర్హత నిర్ణయాలు కావు.",
        "general": "పథకాలు, అవసరమైన పత్రాలు లేదా అభ్యర్థన స్థితి గురించి అడగండి. ఈ సహాయకుడు స్థానిక నమూనా నియమాలను ఉపయోగిస్తాడు.",
    },
    "Hindi": {
        "documents": "चुनी हुई योजना की दस्तावेज़ सूची देखें। नमूने में पहचान दस्तावेज़, भूमि रिकॉर्ड या बैंक पासबुक हो सकते हैं।",
        "status": "हर अनुरोध का मौजूदा चरण और बाकी दस्तावेज़ देखने के लिए अनुरोध स्थिति खोलें।",
        "scheme": "अपनी जानकारी को अलग-अलग नमूना नियमों से मिलाने के लिए योजना खोज खोलें। ये आधिकारिक पात्रता निर्णय नहीं हैं।",
        "general": "योजना, आवश्यक दस्तावेज़ या अनुरोध की स्थिति पूछें। यह सहायक स्थानीय नमूना नियमों का उपयोग करता है।",
    },
}

_COPY = {
    "English": {
        "title": "Voice assistant",
        "microphone": "Start speaking",
        "placeholder": "Type your question if speech is unavailable",
        "send": "Ask",
        "stop": "Stop voice",
        "read": "Read answer",
        "ready": "Allow microphone access when your browser asks. You can also type a question.",
        "listening": "Listening. Speak your question now.",
        "unsupported": "Speech recognition is not supported in this browser. Type your question below.",
        "permission": "Microphone permission was denied. Allow it in your browser settings, or type your question.",
        "recognition_error": "Speech recognition stopped. Check microphone permission or type your question.",
        "empty": "Type or speak a question first.",
        "no_speech": "No speech was detected. Try again or type your question.",
        "voice_unavailable": "The answer is shown above. Speech playback is not supported in this browser.",
        "stopped": "Voice playback stopped.",
        "done": "Answer ready.",
        "note": "Browser speech recognition and speech playback are used when supported. Replies are local demonstrations, not live AI.",
    },
    "Telugu": {
        "title": "వాయిస్ సహాయకుడు",
        "microphone": "మాట్లాడటం ప్రారంభించండి",
        "placeholder": "మాట గుర్తింపు లేకపోతే మీ ప్రశ్నను టైప్ చేయండి",
        "send": "అడగండి",
        "stop": "వాయిస్ ఆపండి",
        "read": "సమాధానం చదవండి",
        "ready": "బ్రౌజర్ అడిగినప్పుడు మైక్రోఫోన్ అనుమతి ఇవ్వండి. ప్రశ్నను టైప్ కూడా చేయవచ్చు.",
        "listening": "వింటున్నాం. ఇప్పుడు మీ ప్రశ్న చెప్పండి.",
        "unsupported": "ఈ బ్రౌజర్‌లో మాట గుర్తింపు లేదు. కింద మీ ప్రశ్నను టైప్ చేయండి.",
        "permission": "మైక్రోఫోన్ అనుమతి నిరాకరించబడింది. బ్రౌజర్ సెట్టింగుల్లో అనుమతించండి లేదా ప్రశ్నను టైప్ చేయండి.",
        "recognition_error": "మాట గుర్తింపు ఆగిపోయింది. మైక్రోఫోన్ అనుమతిని తనిఖీ చేయండి లేదా ప్రశ్నను టైప్ చేయండి.",
        "empty": "ముందుగా ప్రశ్నను టైప్ చేయండి లేదా చెప్పండి.",
        "no_speech": "మాట వినిపించలేదు. మళ్లీ ప్రయత్నించండి లేదా ప్రశ్నను టైప్ చేయండి.",
        "voice_unavailable": "సమాధానం పైన ఉంది. ఈ బ్రౌజర్‌లో మాట ద్వారా చదివే సదుపాయం లేదు.",
        "stopped": "వాయిస్ ప్లేబ్యాక్ ఆపబడింది.",
        "done": "సమాధానం సిద్ధంగా ఉంది.",
        "note": "అందుబాటులో ఉన్నప్పుడు బ్రౌజర్ మాట గుర్తింపు, మాట ప్లేబ్యాక్ ఉపయోగిస్తాం. సమాధానాలు స్థానిక నమూనాలు; ప్రత్యక్ష AI కాదు.",
    },
    "Hindi": {
        "title": "वॉइस सहायक",
        "microphone": "बोलना शुरू करें",
        "placeholder": "आवाज़ काम न करे तो अपना सवाल लिखें",
        "send": "पूछें",
        "stop": "आवाज़ रोकें",
        "read": "जवाब पढ़ें",
        "ready": "ब्राउज़र पूछे तो माइक्रोफ़ोन की अनुमति दें। आप सवाल लिख भी सकते हैं।",
        "listening": "सुन रहा है। अब अपना सवाल बोलें।",
        "unsupported": "इस ब्राउज़र में आवाज़ पहचान उपलब्ध नहीं है। नीचे सवाल लिखें।",
        "permission": "माइक्रोफ़ोन की अनुमति नहीं मिली। ब्राउज़र सेटिंग में अनुमति दें या सवाल लिखें।",
        "recognition_error": "आवाज़ पहचान रुक गई। माइक्रोफ़ोन अनुमति जाँचें या सवाल लिखें।",
        "empty": "पहले सवाल लिखें या बोलें।",
        "no_speech": "आवाज़ नहीं मिली। फिर कोशिश करें या सवाल लिखें।",
        "voice_unavailable": "जवाब ऊपर दिख रहा है। इस ब्राउज़र में आवाज़ से पढ़ना उपलब्ध नहीं है।",
        "stopped": "आवाज़ चलना रोक दिया गया।",
        "done": "जवाब तैयार है।",
        "note": "समर्थित होने पर ब्राउज़र की आवाज़ पहचान और पढ़ने की सुविधा उपयोग होती है। जवाब स्थानीय नमूने हैं, लाइव AI नहीं।",
    },
}


def _reply(question: str, language: str) -> str:
    normalized = question.casefold()
    topic = "general"
    if any(term in normalized for term in (
        "document", "paper", "checklist", "పత్ర", "పాస్‌బుక్", "दस्तावेज", "कागज़",
    )):
        topic = "documents"
    elif any(term in normalized for term in (
        "status", "request", "case", "స్థితి", "అభ్యర్థన", "स्थिति", "अनुरोध",
    )):
        topic = "status"
    elif any(term in normalized for term in (
        "scheme", "eligible", "eligibility", "పథక", "అర్హత", "योजना", "पात्रता",
    )):
        topic = "scheme"
    return _REPLIES[language][topic]


def render(language: str) -> None:
    if language not in LANGUAGE_LOCALES:
        raise ValueError(f"Unsupported voice language: {language}")
    copy = _COPY[language]
    locale = LANGUAGE_LOCALES[language]
    replies = _REPLIES[language]
    labels = {key: html.escape(value) for key, value in copy.items()}
    script_values = json.dumps(
        {"locale": locale, "copy": copy, "replies": replies},
        ensure_ascii=True,
    ).replace("</", "<\\/")
    st.html(
        f"""
        <section class="jansahay-voice" aria-label="{labels['title']}">
          <div class="jansahay-voice-heading">
            <svg aria-hidden="true" viewBox="0 0 24 24" width="25" height="25">
              <path fill="currentColor" d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3Zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.93V21h2v-3.07A7 7 0 0 0 19 11h-2Z"/>
            </svg>
            <strong>{labels['title']}</strong>
          </div>
          <div class="jansahay-voice-controls">
            <button type="button" id="js-voice-mic" aria-label="{labels['microphone']}">🎙️</button>
            <input id="js-voice-input" type="text" aria-label="{labels['placeholder']}" placeholder="{labels['placeholder']}">
            <button type="button" id="js-voice-send">{labels['send']}</button>
            <button type="button" id="js-voice-stop">{labels['stop']}</button>
          </div>
          <div id="js-voice-status" role="status" aria-live="polite">{labels['ready']}</div>
          <div id="js-voice-answer" hidden></div>
          <button type="button" id="js-voice-read" hidden>{labels['read']}</button>
          <small>{labels['note']}</small>
        </section>
        <style>
          .jansahay-voice {{ background: rgba(255,255,255,.94); border: 1px solid #dce8e7;
            border-left: 4px solid #2c8066; border-radius: 12px; color: #17333d;
            padding: .8rem 1rem; margin: .25rem 0 1rem; box-shadow: 0 5px 18px rgba(23,51,61,.06); }}
          .jansahay-voice-heading {{ display:flex; align-items:center; gap:.55rem; margin-bottom:.55rem; color:#104e64; }}
          .jansahay-voice-controls {{ display:flex; gap:.5rem; align-items:center; flex-wrap:wrap; }}
          .jansahay-voice-controls input {{ flex:1 1 260px; min-height:2.5rem; border:1px solid #9aafac;
            border-radius:8px; padding:.45rem .7rem; font:inherit; }}
          .jansahay-voice button {{ border:1px solid #176f8a; border-radius:8px; background:#176f8a;
            color:#fff; font:inherit; font-weight:650; min-height:2.5rem; padding:.4rem .8rem; cursor:pointer; }}
          #js-voice-mic {{ background:#2c8066; border-color:#2c8066; min-width:3rem; font-size:1.2rem; }}
          #js-voice-stop {{ background:#fff; color:#104e64; }}
          #js-voice-status {{ margin:.45rem 0; font-size:.9rem; }}
          #js-voice-answer {{ background:#f3f8f6; border-radius:8px; padding:.6rem .75rem; margin:.45rem 0; line-height:1.5; }}
          .jansahay-voice small {{ color:#52686d; display:block; line-height:1.4; margin-top:.4rem; }}
          .jansahay-voice button:focus-visible, .jansahay-voice input:focus-visible {{ outline:3px solid #e6a23c; outline-offset:2px; }}
        </style>
        <script>
        (() => {{
          const settings = {script_values};
          const input = document.getElementById("js-voice-input");
          const status = document.getElementById("js-voice-status");
          const answer = document.getElementById("js-voice-answer");
          const readButton = document.getElementById("js-voice-read");
          const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
          let recognition = null;
          const copy = settings.copy;

          function speak(text) {{
            if (!("speechSynthesis" in window) || !("SpeechSynthesisUtterance" in window)) {{
              status.textContent = copy.voice_unavailable;
              return;
            }}
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = settings.locale;
            const voices = window.speechSynthesis.getVoices();
            const voice = voices.find(item => item.lang.toLowerCase() === settings.locale.toLowerCase())
              || voices.find(item => item.lang.toLowerCase().startsWith(settings.locale.slice(0, 2)));
            if (voice) utterance.voice = voice;
            window.speechSynthesis.speak(utterance);
          }}

          function respond(question) {{
            const normalized = question.toLocaleLowerCase(settings.locale);
            const has = terms => terms.some(term => normalized.includes(term));
            let reply = settings.replies.general;
            if (has(["document", "paper", "checklist", "పత్ర", "పాస్‌బుక్", "दस्तावेज", "कागज़"])) {{
              reply = settings.replies.documents;
            }} else if (has(["status", "request", "case", "స్థితి", "అభ్యర్థన", "स्थिति", "अनुरोध"])) {{
              reply = settings.replies.status;
            }} else if (has(["scheme", "eligible", "eligibility", "పథక", "అర్హత", "योजना", "पात्रता"])) {{
              reply = settings.replies.scheme;
            }}
            answer.textContent = reply;
            answer.hidden = false;
            readButton.hidden = false;
            status.textContent = copy.done;
            speak(reply);
          }}

          document.getElementById("js-voice-send").addEventListener("click", () => {{
            if (!input.value.trim()) {{
              status.textContent = copy.empty;
              input.focus();
              return;
            }}
            respond(input.value.trim());
          }});
          input.addEventListener("keydown", event => {{
            if (event.key === "Enter") document.getElementById("js-voice-send").click();
          }});
          readButton.addEventListener("click", () => {{
            if (!answer.hidden) speak(answer.textContent);
          }});
          document.getElementById("js-voice-stop").addEventListener("click", () => {{
            if ("speechSynthesis" in window) window.speechSynthesis.cancel();
            if (recognition) recognition.abort();
            status.textContent = copy.stopped;
          }});
          document.getElementById("js-voice-mic").addEventListener("click", () => {{
            if (!SpeechRecognition) {{
              status.textContent = copy.unsupported;
              input.focus();
              return;
            }}
            recognition = new SpeechRecognition();
            recognition.lang = settings.locale;
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;
            recognition.onresult = event => {{
              input.value = event.results[0][0].transcript;
              respond(input.value);
            }};
            recognition.onerror = event => {{
              status.textContent = event.error === "not-allowed" || event.error === "service-not-allowed"
                ? copy.permission : event.error === "no-speech" ? copy.no_speech : copy.recognition_error;
            }};
            recognition.onend = () => {{
              if (!answer.hidden && status.textContent === copy.listening) status.textContent = copy.done;
            }};
            try {{
              recognition.start();
              status.textContent = copy.listening;
            }} catch (_error) {{
              status.textContent = copy.recognition_error;
            }}
          }});
        }})();
        </script>
        """,
        unsafe_allow_javascript=True,
    )
