import os
import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from jansahay import db, i18n


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class PortalTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "portal.sqlite3"
        self.environment = unittest.mock.patch.dict(
            os.environ, {"JANSAHAY_DB_PATH": str(self.database_path)}
        )
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary_directory.cleanup()

    def _login_citizen(self, language="English"):
        app = AppTest.from_file(str(APP_PATH), default_timeout=15).run()
        if language != "English":
            app.selectbox[0].set_value(i18n.language_label(language)).run()
        app.form_submit_button[0].click().run()
        self.assertFalse(app.exception)
        return app

    def test_language_selection_translates_all_citizen_pages(self):
        expected_titles = {
            "English": (
                "Welcome, Ravi", "Scheme finder", "JanSahay assistant", "Check a claim",
                "Document helper", "Request tracking", "Telephone assistance",
                "Nearby service directory", "Reminders", "Community insights",
            ),
            "Telugu": (
                "స్వాగతం, Ravi", "పథకాల అన్వేషణ", "జన్‌సహాయ్ సహాయకుడు", "సందేశాన్ని తనిఖీ చేయండి",
                "పత్రాల సహాయకుడు", "అభ్యర్థన స్థితి", "టెలిఫోన్ సహాయం", "సమీప సేవా కేంద్రాలు",
                "గుర్తుచూపులు", "సమాజ సమాచారం",
            ),
            "Hindi": (
                "स्वागत है, Ravi", "योजना खोज", "जनसहाय सहायक", "दावे की जाँच",
                "दस्तावेज़ सहायक", "अनुरोध स्थिति", "फ़ोन सहायता", "नज़दीकी सेवा केंद्र",
                "अनुस्मारक", "समुदाय जानकारी",
            ),
        }
        for language, titles in expected_titles.items():
            with self.subTest(language=language):
                app = self._login_citizen(language)
                self.assertEqual(app.session_state["language"], language)
                expected_voice_title = {
                    "English": "Voice assistant",
                    "Telugu": "వాయిస్ సహాయకుడు",
                    "Hindi": "वॉइस सहायक",
                }[language]
                self.assertEqual(
                    list(app.selectbox[0].options),
                    ["English", "తెలుగు", "हिन्दी"],
                )
                for index, expected_title in enumerate(titles):
                    page_option = app.sidebar.radio[0].options[index]
                    app.sidebar.radio[0].set_value(page_option).run()
                    self.assertFalse(app.exception, f"{language}/{page_option}: {app.exception}")
                    self.assertEqual(app.title[0].value, expected_title)
                    self.assertEqual(app.session_state["language"], language)
                    self.assertTrue(any(
                        expected_voice_title in item.value
                        for item in app.html
                    ))

    def test_citizen_navigation_excludes_volunteer_desk(self):
        app = self._login_citizen()
        self.assertNotIn("Volunteer Desk", app.sidebar.radio[0].options)
        for page in (
            "Overview",
            "Scheme Finder",
            "Assistant",
            "Check a Claim",
            "Documents",
            "Request Tracking",
            "Telephone Help",
            "Service Directory",
            "Reminders",
            "Community Insights",
        ):
            app.sidebar.radio[0].set_value(page).run()
            self.assertFalse(app.exception, f"{page}: {app.exception}")

    def test_scheme_finder_shows_distinct_rules_and_runs_checker(self):
        app = self._login_citizen()
        app.sidebar.radio[0].set_value(app.sidebar.radio[0].options[1]).run()
        expected_schemes = (
            "Small Farmer Input Support",
            "Agricultural Subsidy Assistance",
            "Land Notice Assistance",
            "Farmer Document Assistance",
            "Crop Assistance Support",
        )
        rendered_subheaders = [item.value for item in app.subheader]
        for scheme in expected_schemes:
            self.assertIn(scheme, rendered_subheaders)
        self.assertIn(
            "Demonstration scheme information — not verified against an official source.",
            [item.value for item in app.info],
        )
        next(item for item in app.form_submit_button if item.label == "Check demo eligibility").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Potentially eligible" in item.value for item in app.info))

    def test_claim_check_displays_explanation_reasons_and_action(self):
        app = self._login_citizen()
        app.sidebar.radio[0].set_value(app.sidebar.radio[0].options[3]).run()
        app.text_area[0].set_value("Please send OTP to get guaranteed approval")
        next(item for item in app.form_submit_button if item.label == "Check claim").click().run()
        self.assertFalse(app.exception)
        self.assertIn("SUSPICIOUS", [item.value for item in app.subheader])
        self.assertTrue(any("Recommended action:" in item.value for item in app.markdown))
        self.assertTrue(any("password" in item.value for item in app.warning))

    def test_volunteer_access_is_separate_from_citizen_login(self):
        app = AppTest.from_file(str(APP_PATH), default_timeout=15).run()
        app.selectbox[0].set_value("తెలుగు").run()
        app.text_input[5].set_value("helper123")
        app.form_submit_button[2].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["language"], "Telugu")
        self.assertIn("స్వచ్ఛంద సేవకుల విభాగం", app.sidebar.radio[0].options)
        self.assertTrue(any("వాయిస్ సహాయకుడు" in item.value for item in app.html))

    def test_ivr_records_volunteer_follow_up(self):
        app = self._login_citizen("Telugu")
        telephone_page = app.sidebar.radio[0].options[6]
        app.sidebar.radio[0].set_value(telephone_page).run()
        ivr_select = next(item for item in app.selectbox if item.key == "ivr_option")
        ivr_select.set_value(ivr_select.options[4]).run()
        next(item for item in app.button if item.label == "నమూనా IVR సమాధానాన్ని వినండి").click().run()
        self.assertTrue(any("స్వచ్ఛంద సేవకుల సహాయ అభ్యర్థన" in item.value for item in app.info))
        next(
            item for item in app.form_submit_button
            if item.label == "స్వచ్ఛంద సేవకుల సహాయం కోరండి"
        ).click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("స్థానికంగా నమోదు" in item.value for item in app.success))

    def test_telephone_help_uses_fictional_dialer_link(self):
        app = self._login_citizen("Hindi")
        telephone_page = app.sidebar.radio[0].options[6]
        app.sidebar.radio[0].set_value(telephone_page).run()
        phone_link = next(item for item in app.link_button if item.label == "जनसहाय को कॉल करें")
        self.assertTrue(phone_link.url.startswith("tel:"))
        self.assertTrue(any("काल्पनिक नमूना नंबर" in item.value for item in app.caption))

    def test_voice_assistant_is_rendered_in_selected_language(self):
        for language, expected_title in (
            ("English", "Voice assistant"),
            ("Telugu", "వాయిస్ సహాయకుడు"),
            ("Hindi", "वॉइस सहायक"),
        ):
            with self.subTest(language=language):
                app = self._login_citizen(language)
                self.assertFalse(app.exception)
                self.assertTrue(any(
                    expected_title in str(getattr(item, "value", ""))
                    for item in getattr(app, "html", [])
                ))

    def test_request_tracking_displays_submitted_and_pending_documents(self):
        app = self._login_citizen()
        db.add_document(
            "JS-CASE1002",
            "JS-C10245",
            "land-notice.txt",
            "Hearing notice",
            "Rule-based demo explanation.",
            self.database_path,
        )
        app.sidebar.radio[0].set_value("Request Tracking").run()
        checklist = [
            item.value for item in app.markdown
            if "Submitted ·" in item.value or "Pending ·" in item.value
        ]
        self.assertIn("✓ Submitted · Land notice", checklist)
        self.assertIn("○ Pending · Land record", checklist)

    def test_translated_status_selection_persists_canonical_case_value(self):
        app = self._login_citizen("Hindi")
        app.sidebar.radio[0].set_value(app.sidebar.radio[0].options[5]).run()
        status_select = next(item for item in app.selectbox if item.key == "status_JS-CASE1001")
        self.assertIn("हल हो गया", status_select.options)
        save_button = next(
            item for item in app.form_submit_button
            if item.label == "अनुरोध बदलाव सहेजें"
        )
        status_select.set_value("हल हो गया")
        save_button.click().run()
        case = next(item for item in db.list_cases("JS-C10245") if item["case_id"] == "JS-CASE1001")
        self.assertEqual(case["status"], "Resolved")


if __name__ == "__main__":
    unittest.main()