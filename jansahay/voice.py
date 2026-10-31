"""Reusable browser-based page reader for the JanSahay prototype."""

from __future__ import annotations

import html
import json

import streamlit as st

from .i18n import LANGUAGE_LOCALES

_COPY = {
    "English": {
        "title": "Page reader",
        "read": "Read this page",
        "stop": "Stop reading",
        "ready": "Read the visible page content in your selected language.",
        "reading": "Reading this page.",
        "stopped": "Page reading stopped.",
        "done": "Page reading complete.",
        "no_content": "There is no readable page content.",
        "voice_unavailable": "Speech playback is not supported in this browser.",
        "matching_voice_unavailable": "No English voice is available. Page text was not spoken.",
        "note": "Uses browser speech. Voice processing depends on your browser and selected voice.",
    },
    "Telugu": {
        "title": "పేజీ పఠనం",
        "read": "ఈ పేజీని చదవండి",
        "stop": "చదవడం ఆపండి",
        "ready": "మీరు ఎంచుకున్న భాషలో కనిపిస్తున్న పేజీ విషయాన్ని చదవండి.",
        "reading": "ఈ పేజీని చదువుతోంది.",
        "stopped": "పేజీ పఠనం ఆపబడింది.",
        "done": "పేజీ పఠనం పూర్తయింది.",
        "no_content": "చదవగలిగే పేజీ విషయం లేదు.",
        "voice_unavailable": "ఈ బ్రౌజర్‌లో మాట ప్లేబ్యాక్ అందుబాటులో లేదు.",
        "matching_voice_unavailable": "తెలుగు వాయిస్ అందుబాటులో లేదు. పేజీ పాఠ్యాన్ని చదవలేదు.",
        "note": "బ్రౌజర్ మాట సదుపాయం ఉపయోగిస్తాం; వాయిస్ ప్రాసెసింగ్ మీ బ్రౌజర్, ఎంచుకున్న వాయిస్‌పై ఆధారపడి ఉంటుంది.",
    },
    "Hindi": {
        "title": "पृष्ठ पाठक",
        "read": "यह पृष्ठ पढ़ें",
        "stop": "पढ़ना रोकें",
        "ready": "चुनी हुई भाषा में दिखाई दे रही पृष्ठ सामग्री पढ़ें।",
        "reading": "यह पृष्ठ पढ़ा जा रहा है।",
        "stopped": "पृष्ठ पढ़ना रोक दिया गया।",
        "done": "पृष्ठ पढ़ना पूरा हुआ।",
        "no_content": "पढ़ने योग्य पृष्ठ सामग्री नहीं है।",
        "voice_unavailable": "इस ब्राउज़र में आवाज़ चलाना उपलब्ध नहीं है।",
        "matching_voice_unavailable": "हिंदी आवाज़ उपलब्ध नहीं है। पृष्ठ का पाठ नहीं पढ़ा गया।",
        "note": "ब्राउज़र की आवाज़ सुविधा उपयोग होती है; आवाज़ का प्रसंस्करण आपके ब्राउज़र और चुनी गई आवाज़ पर निर्भर करता है।",
    },
}


def render(language: str) -> None:
    if language not in LANGUAGE_LOCALES:
        raise ValueError(f"Unsupported voice language: {language}")
    copy = _COPY[language]
    locale = LANGUAGE_LOCALES[language]
    labels = {key: html.escape(value) for key, value in copy.items()}
    script_values = json.dumps(
        {"locale": locale, "copy": copy},
        ensure_ascii=True,
    ).replace("</", "<\\/")
    st.html(
        f"""
        <section class="jansahay-voice" aria-label="{labels['title']}">
          <div class="jansahay-voice-heading">
            <svg aria-hidden="true" viewBox="0 0 24 24" width="25" height="25">
              <path fill="currentColor" d="M12 3a1 1 0 0 0-1 1v10a1 1 0 0 0 2 0V4a1 1 0 0 0-1-1Zm-5 8a1 1 0 0 0-2 0 7 7 0 0 0 6 6.93V21h2v-3.07A7 7 0 0 0 19 11a1 1 0 0 0-2 0 5 5 0 0 1-10 0Z"/>
            </svg>
            <strong>{labels['title']}</strong>
          </div>
          <div class="jansahay-voice-controls">
            <button type="button" id="js-voice-read">{labels['read']}</button>
            <button type="button" id="js-voice-stop">{labels['stop']}</button>
          </div>
          <div id="js-voice-status" role="status" aria-live="polite">{labels['ready']}</div>
          <small>{labels['note']}</small>
        </section>
        <style>
          .jansahay-voice {{ background: rgba(255,255,255,.94); border: 1px solid #dce8e7;
            border-left: 4px solid #2c8066; border-radius: 12px; color: #17333d;
            padding: .8rem 1rem; margin: .25rem 0 1rem; box-shadow: 0 5px 18px rgba(23,51,61,.06); }}
          .jansahay-voice-heading {{ display:flex; align-items:center; gap:.55rem; margin-bottom:.55rem; color:#104e64; }}
          .jansahay-voice-controls {{ display:flex; gap:.5rem; align-items:center; flex-wrap:wrap; }}
          .jansahay-voice button {{ border:1px solid #176f8a; border-radius:8px; background:#176f8a;
            color:#fff; font:inherit; font-weight:650; min-height:2.5rem; padding:.4rem .8rem; cursor:pointer; }}
          #js-voice-stop {{ background:#fff; color:#104e64; }}
          #js-voice-status {{ margin:.45rem 0; font-size:.9rem; }}
          .jansahay-voice small {{ color:#52686d; display:block; line-height:1.4; margin-top:.4rem; }}
          .jansahay-voice button:focus-visible {{ outline:3px solid #e6a23c; outline-offset:2px; }}
        </style>
        <script>
        (() => {{
          const settings = {script_values};
          const copy = settings.copy;
          const status = document.getElementById("js-voice-status");
          const synthesis = window.speechSynthesis;
          let currentRequest = 0;
          let watchTimer = null;
          let pageObserver = null;
          let utterance = null;

          function excluded(element) {{
            return element.matches(
              'script,style,noscript,nav,aside,header,footer,button,input,textarea,select,' +
              '[hidden],[inert],[aria-hidden="true"],[data-testid="stSidebar"],' +
              '[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],' +
              '[data-testid="stStatusWidget"],.site-header,.site-footer,.jansahay-voice'
            );
          }}

          function visible(element) {{
            for (let node = element; node && node.nodeType === Node.ELEMENT_NODE; node = node.parentElement) {{
              if (excluded(node)) return false;
              const style = window.getComputedStyle(node);
              if (style.display === "none" || style.visibility === "hidden" || style.visibility === "collapse") {{
                return false;
              }}
            }}
            return true;
          }}

          function pageText() {{
            const root = document.querySelector('[data-testid="stMain"]') || document.querySelector("main");
            if (!root) return "";
            const chunks = [];
            const blockTags = new Set(["H1", "H2", "H3", "H4", "H5", "H6", "P", "LI", "DT", "DD", "BLOCKQUOTE", "PRE", "TD", "TH", "CAPTION"]);
            function visibleText(node) {{
              if (node.nodeType === Node.TEXT_NODE) {{
                return visible(node.parentElement) ? node.nodeValue : "";
              }}
              if (node.nodeType !== Node.ELEMENT_NODE || excluded(node) || !visible(node)) return "";
              return Array.from(node.childNodes, visibleText).join("");
            }}
            function visit(node) {{
              if (node.nodeType === Node.TEXT_NODE) {{
                const text = node.nodeValue.replace(/\\s+/g, " ").trim();
                if (text && visible(node.parentElement)) chunks.push(text);
                return;
              }}
              if (node.nodeType !== Node.ELEMENT_NODE || excluded(node) || !visible(node)) return;
              if (blockTags.has(node.tagName)) {{
                const text = visibleText(node).replace(/\\s+/g, " ").trim();
                const context = node.closest("tr,li,[role='listitem']");
                const contextText = context ? context.innerText.replace(/\\s+/g, " ").trim() : "";
                if (text) chunks.push({{
                  text,
                  key: contextText ? `${{contextText.toLocaleLowerCase()}}\\n${{text.toLocaleLowerCase()}}` : text.toLocaleLowerCase(),
                }});
                return;
              }}
              for (const child of node.childNodes) visit(child);
            }}
            visit(root);
            const unique = [];
            const seen = new Set();
            for (const chunk of chunks) {{
              const normalized = (typeof chunk === "string" ? chunk : chunk.text).replace(/\\s+/g, " ").trim();
              const key = typeof chunk === "string" ? normalized.toLocaleLowerCase() : chunk.key;
              if (normalized && !seen.has(key)) {{
                seen.add(key);
                unique.push(normalized);
              }}
            }}
            return unique.join(". ");
          }}

          function pageSignature() {{
            const selectedPage = document.querySelector(
              '[data-testid="stSidebar"] [role="radio"][aria-checked="true"]'
            );
            return (selectedPage ? selectedPage.innerText : "") + "\\n" + pageText();
          }}

          function stopSpeech(message) {{
            currentRequest += 1;
            if (watchTimer !== null) window.clearInterval(watchTimer);
            watchTimer = null;
            if (pageObserver !== null) pageObserver.disconnect();
            pageObserver = null;
            utterance = null;
            if (synthesis) synthesis.cancel();
            if (message) status.textContent = message;
          }}

          function watchPage(request, pageSnapshot) {{
            const cancelIfChanged = () => {{
              if (request === currentRequest && pageSignature() !== pageSnapshot) {{
                stopSpeech(copy.stopped);
              }}
            }};
            watchTimer = window.setInterval(cancelIfChanged, 350);
            const observedRoots = [
              document.querySelector('[data-testid="stMain"]'),
              document.querySelector('[data-testid="stSidebar"]'),
            ].filter(Boolean);
            if (window.MutationObserver && observedRoots.length) {{
              pageObserver = new MutationObserver(cancelIfChanged);
              for (const root of observedRoots) {{
                pageObserver.observe(root, {{
                  attributes: true,
                  attributeFilter: ["aria-checked"],
                  characterData: true,
                  childList: true,
                  subtree: true,
                }});
              }}
            }}
          }}

          function matchingVoice() {{
            return new Promise(resolve => {{
              const language = settings.locale.split("-")[0].toLowerCase();
              const deadline = Date.now() + 2000;
              function find() {{
                const voices = synthesis.getVoices();
                const exact = voices.find(voice => voice.lang.toLowerCase() === settings.locale.toLowerCase());
                if (exact) return resolve(exact);
                const sameLanguage = voices.find(voice => voice.lang.toLowerCase().split("-")[0] === language);
                if (sameLanguage) return resolve(sameLanguage);
                if (Date.now() >= deadline) return resolve(null);
                window.setTimeout(find, 100);
              }}
              find();
            }});
          }}

          async function readPage() {{
            stopSpeech("");
            const request = currentRequest;
            if (!synthesis || !window.SpeechSynthesisUtterance) {{
              status.textContent = copy.voice_unavailable;
              return;
            }}
            const text = pageText();
            if (!text) {{
              status.textContent = copy.no_content;
              return;
            }}
            const pageSnapshot = pageSignature();
            watchPage(request, pageSnapshot);
            const voice = await matchingVoice();
            if (request !== currentRequest) return;
            if (!voice) {{
              stopSpeech(copy.matching_voice_unavailable);
              return;
            }}
            if (pageSignature() !== pageSnapshot) {{
              stopSpeech(copy.stopped);
              return;
            }}
            const speech = new SpeechSynthesisUtterance(text);
            speech.lang = settings.locale;
            speech.voice = voice;
            utterance = speech;
            speech.onend = () => {{
              if (request === currentRequest) {{
                stopSpeech(copy.done);
              }}
            }};
            speech.onerror = () => {{
              if (request === currentRequest) stopSpeech(copy.voice_unavailable);
            }};
            status.textContent = copy.reading;
            synthesis.speak(speech);
          }}

          document.getElementById("js-voice-read").addEventListener("click", readPage);
          document.getElementById("js-voice-stop").addEventListener("click", () => stopSpeech(copy.stopped));
          window.addEventListener("pagehide", () => stopSpeech(""));
        }})();
        </script>
        """,
        unsafe_allow_javascript=True,
    )
