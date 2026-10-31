import json
import shutil
import subprocess
import unittest
from unittest.mock import patch

from jansahay import voice


class PageReaderTests(unittest.TestCase):
    _NODE_READER_HARNESS = r"""
const vm = require("node:vm");
const source = process.argv[1];
const scenario = process.argv[2];
const selectedLocale = process.argv[3];
const stoppedMessage = {
  "en-IN": "Page reading stopped.",
  "te-IN": "పేజీ పఠనం ఆపబడింది.",
  "hi-IN": "पृष्ठ पढ़ना रोक दिया गया।",
}[selectedLocale];
const calls = { spoken: [], cancelled: 0, observers: [], handlers: {} };

function element(tagName, children = [], options = {}) {
  const node = {
    nodeType: 1,
    tagName: tagName.toUpperCase(),
    childNodes: children,
    parentElement: null,
    hidden: Boolean(options.hidden),
    excluded: Boolean(options.excluded),
    style: options.style || {},
    attrs: options.attrs || {},
    matches(selector) {
      if (this.excluded && selector.includes(this.tagName.toLowerCase())) return true;
      if (this.hidden && selector.includes("[hidden]")) return true;
      if (this.attrs.inert && selector.includes("[inert]")) return true;
      if (this.attrs["aria-hidden"] === "true" && selector.includes('[aria-hidden="true"]')) return true;
      return false;
    },
    closest(selector) {
      for (let node = this; node; node = node.parentElement) {
        if (selector.includes("tr") && node.tagName === "TR") return node;
        if (selector.includes("li") && node.tagName === "LI") return node;
        if (selector.includes('[role="listitem"]') && node.attrs.role === "listitem") return node;
      }
      return null;
    },
    get innerText() {
      return this.childNodes.map(child => child.nodeType === 3 ? child.nodeValue : child.innerText).join(" ");
    },
  };
  for (const child of children) child.parentElement = node;
  return node;
}

function text(value) {
  return { nodeType: 3, nodeValue: value, parentElement: null };
}

const main = element("main", [
  element("h1", [text("Citizen dashboard")]),
  element("p", [
    text("Visible page guidance"),
    element("span", [text("Hidden accessible text")], { attrs: { "aria-hidden": "true" } }),
  ]),
  element("p", [text("Visible page guidance")]),
  element("table", [
    element("tr", [element("td", [text("Case 1")]), element("td", [text("Open")])]),
    element("tr", [element("td", [text("Case 2")]), element("td", [text("Open")])]),
  ]),
  element("p", [text("Hidden announcement")], { hidden: true }),
  element("button", [text("Interactive control")], { excluded: true }),
  element("nav", [text("Navigation link")], { excluded: true }),
]);
const selectedPage = { innerText: "Citizen dashboard" };
const status = { textContent: "", addEventListener() {} };
const readButton = { addEventListener(_name, callback) { calls.handlers.read = callback; } };
const stopButton = { addEventListener(_name, callback) { calls.handlers.stop = callback; } };
const document = {
  querySelector(selector) {
    if (selector === '[data-testid="stMain"]') return main;
    if (selector === '[data-testid="stSidebar"]') return {};
    if (selector.includes('[role="radio"]')) return selectedPage;
    return null;
  },
  getElementById(id) {
    return {
      "js-voice-status": status,
      "js-voice-read": readButton,
      "js-voice-stop": stopButton,
    }[id] || null;
  },
};

const availableVoices = scenario === "async"
  ? []
  : scenario === "unavailable"
    ? [{ lang: "en-US" }]
    : [{ lang: selectedLocale }];
let voiceLoadPolls = 0;
const synthesis = {
  getVoices() { return availableVoices; },
  cancel() { calls.cancelled += 1; },
  speak(utterance) { calls.spoken.push(utterance); },
};
class SpeechSynthesisUtterance {
  constructor(value) { this.text = value; }
}
class MutationObserver {
  constructor(callback) { this.callback = callback; calls.observers.push(this); }
  observe() {}
  disconnect() {}
}
let clock = 0;
const context = {
  document,
  Node: { ELEMENT_NODE: 1, TEXT_NODE: 3 },
  MutationObserver,
  SpeechSynthesisUtterance,
  Date: { now() { clock += 500; return clock; } },
  window: {
    speechSynthesis: synthesis,
    SpeechSynthesisUtterance,
    MutationObserver,
    getComputedStyle(node) {
      return { display: node.style.display || "block", visibility: node.style.visibility || "visible" };
    },
    setInterval() { return 1; },
    clearInterval() {},
    setTimeout(callback) {
      voiceLoadPolls += 1;
      if (scenario === "async" && voiceLoadPolls === 3) availableVoices.push({ lang: selectedLocale });
      callback();
    },
    addEventListener() {},
  },
};
vm.runInNewContext(source, context);

(async () => {
  await calls.handlers.read();
  if (scenario === "read" || scenario === "async") {
    if (calls.spoken.length !== 1) throw new Error("expected one utterance");
    const utterance = calls.spoken[0];
    if (!utterance.text.includes("Citizen dashboard") || !utterance.text.includes("Visible page guidance")) {
      throw new Error("visible main-page content was not read");
    }
    if (utterance.text.includes("Hidden announcement") || utterance.text.includes("Hidden accessible text") ||
        utterance.text.includes("Navigation link") ||
        utterance.text.includes("Interactive control") || (utterance.text.match(/Visible page guidance/g) || []).length !== 1) {
      throw new Error("hidden, navigation, control, or duplicate text was included");
    }
    if ((utterance.text.match(/Open/g) || []).length !== 2) {
      throw new Error("meaningful repeated values from separate table rows were dropped");
    }
    if (utterance.lang !== selectedLocale || utterance.voice.lang !== selectedLocale) {
      throw new Error("speech did not use the matching selected-language voice");
    }
    await calls.handlers.read();
    if (calls.spoken.length !== 2 || calls.cancelled < 2) throw new Error("repeated start did not cancel prior speech");
    calls.handlers.stop();
    if (calls.cancelled < 3 || status.textContent !== stoppedMessage) {
      throw new Error("stop did not cancel speech and report its state");
    }
  } else if (scenario === "navigation") {
    main.childNodes[0] = element("h1", [text("Different page")]);
    main.childNodes[0].parentElement = main;
    calls.observers[0].callback();
    if (calls.cancelled < 2 || status.textContent !== stoppedMessage) {
      throw new Error("page change did not cancel speech");
    }
  } else if (scenario === "unavailable") {
    if (calls.spoken.length !== 0 ||
        status.textContent !== "No English voice is available. Page text was not spoken.") {
      throw new Error("missing exact-locale voice did not prevent speech and report the limitation");
    }
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
"""

    def _rendered_html(self, language):
        with patch.object(voice.st, "html") as render_html:
            voice.render(language)
        return render_html.call_args.args[0]

    def _run_reader_scenario(self, language, scenario):
        rendered = self._rendered_html(language)
        script = rendered.split("<script>", 1)[1].split("</script>", 1)[0]
        locale = {"English": "en-IN", "Telugu": "te-IN", "Hindi": "hi-IN"}[language]
        result = subprocess.run(
            ["node", "-e", self._NODE_READER_HARNESS, script, scenario, locale],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_reader_controls_and_unavailable_voice_messages_are_localized(self):
        expected = {
            "English": ("Page reader", "Read this page", "No English voice is available. Page text was not spoken.", "en-IN"),
            "Telugu": ("పేజీ పఠనం", "ఈ పేజీని చదవండి", "తెలుగు వాయిస్ అందుబాటులో లేదు. పేజీ పాఠ్యాన్ని చదవలేదు.", "te-IN"),
            "Hindi": ("पृष्ठ पाठक", "यह पृष्ठ पढ़ें", "हिंदी आवाज़ उपलब्ध नहीं है। पृष्ठ का पाठ नहीं पढ़ा गया।", "hi-IN"),
        }
        for language, labels in expected.items():
            with self.subTest(language=language):
                rendered = self._rendered_html(language)
                for label in labels[:2]:
                    self.assertIn(label, rendered)
                script_settings = json.loads(
                    rendered.split("const settings = ", 1)[1]
                    .split(";\n          const copy", 1)[0]
                )
                self.assertEqual(script_settings["copy"]["matching_voice_unavailable"], labels[2])
                self.assertEqual(script_settings["locale"], labels[3])
                self.assertIn('id="js-voice-read"', rendered)
                self.assertIn('id="js-voice-stop"', rendered)
                self.assertNotIn("js-voice-mic", rendered)
                self.assertNotIn("js-voice-input", rendered)

    def test_reader_extracts_main_visible_content_without_repeating_navigation_or_hidden_text(self):
        rendered = self._rendered_html("English")
        for evidence in (
            '[data-testid="stMain"]',
            'nav,aside,header,footer,button,input,textarea,select',
            '[hidden],[inert],[aria-hidden="true"]',
            "visibleText(node)",
            "const seen = new Set()",
            "unique.join",
        ):
            with self.subTest(evidence=evidence):
                self.assertIn(evidence, rendered)

    def test_reader_requires_a_matching_language_voice_and_cancels_on_stop_or_navigation(self):
        rendered = self._rendered_html("Telugu")
        for evidence in (
            "voice.lang.toLowerCase() === settings.locale.toLowerCase()",
            "speech.lang = settings.locale",
            "speech.voice = voice",
            "copy.matching_voice_unavailable",
            "synthesis.cancel()",
            "new MutationObserver",
            "pageSignature() !== pageSnapshot",
            "window.addEventListener(\"pagehide\"",
        ):
            with self.subTest(evidence=evidence):
                self.assertIn(evidence, rendered)
        self.assertNotIn("sameLanguage", rendered)
        self.assertNotIn("|| voices[0]", rendered)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required to exercise embedded reader behavior")
    def test_reader_runtime_uses_exact_locale_for_each_supported_language(self):
        for language in ("English", "Telugu", "Hindi"):
            with self.subTest(language=language):
                self._run_reader_scenario(language, "read")

    @unittest.skipUnless(shutil.which("node"), "Node.js is required to exercise embedded reader behavior")
    def test_reader_runtime_waits_for_asynchronously_loaded_matching_voice(self):
        self._run_reader_scenario("Telugu", "async")

    @unittest.skipUnless(shutil.which("node"), "Node.js is required to exercise embedded reader behavior")
    def test_reader_runtime_cancels_when_page_content_changes(self):
        self._run_reader_scenario("Telugu", "navigation")

    @unittest.skipUnless(shutil.which("node"), "Node.js is required to exercise embedded reader behavior")
    def test_reader_runtime_reports_missing_matching_language_voice(self):
        self._run_reader_scenario("English", "unavailable")

    def test_invalid_reader_language_is_rejected(self):
        with self.assertRaises(ValueError):
            voice.render("French")


if __name__ == "__main__":
    unittest.main()
