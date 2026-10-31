import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from jansahay import db
from jansahay import rules


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "test.sqlite3"
        db.initialize_database(self.database_path)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_seeded_citizen_and_cases_are_available(self):
        citizen = db.authenticate("Ravi Kumar", "ravi123", self.database_path)
        self.assertEqual(citizen["citizen_id"], "JS-C10245")
        self.assertEqual(citizen["district"], "Karimnagar")
        self.assertIsNone(db.authenticate("Ravi Kumar", "wrong", self.database_path))
        cases = db.list_cases("JS-C10245", self.database_path)
        self.assertEqual({case["case_id"] for case in cases}, {"JS-CASE1001", "JS-CASE1002"})

    def test_generated_citizen_and_case_ids_are_unique(self):
        first_citizen = db.create_citizen("Asha", "pw", "Warangal", "Farmer", path=self.database_path)
        second_citizen = db.create_citizen("Kiran", "pw", "Nizamabad", "Rural citizen", path=self.database_path)
        self.assertNotEqual(first_citizen, second_citizen)
        first_case = db.create_case(first_citizen, "Demo case", path=self.database_path)
        second_case = db.create_case(first_citizen, "Another demo case", path=self.database_path)
        self.assertNotEqual(first_case, second_case)

    def test_case_document_notification_and_interaction_changes_persist(self):
        updated = db.update_case("JS-CASE1001", status="Waiting for Documents", path=self.database_path)
        self.assertEqual(updated["status"], "Waiting for Documents")

        document_id = db.add_document(
            "JS-CASE1001", "JS-C10245", "land-record.txt", "Survey record", "A land record.", self.database_path
        )
        self.assertEqual(db.get_document(document_id, self.database_path)["status"], "Submitted")

        notification_id = db.create_notification(
            "JS-C10245", "A demo reminder", "JS-CASE1001", self.database_path
        )
        self.assertTrue(db.mark_notification_read(notification_id, self.database_path))
        self.assertEqual(db.list_notifications("JS-C10245", self.database_path)[0]["is_read"], 1)

        interaction_id = db.log_interaction("JS-C10245", "assistant", "hello", "demo reply", self.database_path)
        self.assertEqual(db.list_interactions("JS-C10245", path=self.database_path)[0]["interaction_id"], interaction_id)

    def test_citizen_can_clear_all_local_document_attachments(self):
        db.add_document(
            "JS-CASE1001", "JS-C10245", "land-record.txt", "Survey record", "Demo", self.database_path
        )
        deleted = db.delete_citizen_documents("JS-C10245", self.database_path)
        self.assertEqual(deleted, 1)
        self.assertEqual(db.list_documents("JS-CASE1001", self.database_path), [])

    def test_invalid_case_update_does_not_change_stored_case(self):
        with self.assertRaises(ValueError):
            db.update_case("JS-CASE1001", status="Not a status", path=self.database_path)
        self.assertEqual(db.get_case("JS-CASE1001", self.database_path)["status"], "In Progress")
        with self.assertRaises(ValueError):
            db.update_case("missing-case", status="Resolved", path=self.database_path)

    def test_scheme_configuration_has_five_distinct_farmer_focused_rules(self):
        schemes = rules.list_demo_schemes()
        self.assertEqual(len(schemes), 5)
        self.assertEqual(
            [scheme["name"] for scheme in schemes],
            [
                "Small Farmer Input Support",
                "Agricultural Subsidy Assistance",
                "Land Notice Assistance",
                "Farmer Document Assistance",
                "Crop Assistance Support",
            ],
        )
        self.assertEqual(len({scheme["criteria"] for scheme in schemes}), 5)
        for scheme in schemes:
            for field in ("description", "who_can_apply", "criteria", "age_requirement",
                          "land_requirement", "income_requirement", "documents", "procedure", "assistance"):
                self.assertTrue(scheme[field], f"{scheme['name']} is missing {field}")

    def test_scheme_check_uses_scheme_specific_eligibility_and_missing_details(self):
        small_farmer = {
            "occupation": "farmer",
            "age": 42,
            "annual_income": 180000,
            "land_acres": 3.5,
            "land_access": "owned",
        }
        small_result = rules.check_eligibility("Small Farmer Input Support", small_farmer)
        self.assertTrue(small_result["eligible"])
        self.assertEqual(small_result["status"], "ELIGIBLE")

        subsidy_result = rules.check_eligibility(
            "Agricultural Subsidy Assistance",
            {**small_farmer, "annual_income": 300000, "land_acres": 8},
        )
        self.assertTrue(subsidy_result["eligible"])
        small_limit_result = rules.check_eligibility(
            "Small Farmer Input Support",
            {**small_farmer, "annual_income": 300000},
        )
        self.assertFalse(small_limit_result["eligible"])

        land_notice = rules.check_eligibility(
            "Land Notice Assistance",
            {"age": 35, "land_access": "owned", "has_land_notice": True},
        )
        self.assertTrue(land_notice["eligible"])
        no_notice = rules.check_eligibility(
            "Land Notice Assistance",
            {"age": 35, "land_access": "owned", "has_land_notice": False},
        )
        self.assertFalse(no_notice["eligible"])

        document_help = rules.check_eligibility(
            "Farmer Document Assistance",
            {
                "age": 38,
                "occupation": "cultivator",
                "land_access": "leased",
                "needs_document_help": True,
            },
        )
        self.assertTrue(document_help["eligible"])
        crop_help = rules.check_eligibility(
            "Crop Assistance Support",
            {
                "age": 38,
                "occupation": "farmer",
                "land_access": "owned",
                "land_acres": 4,
                "crop_loss": True,
            },
        )
        self.assertTrue(crop_help["eligible"])
        excess_land = rules.check_eligibility(
            "Crop Assistance Support",
            {
                "age": 38,
                "occupation": "farmer",
                "land_access": "owned",
                "land_acres": 12,
                "crop_loss": True,
            },
        )
        self.assertFalse(excess_land["eligible"])

        missing = rules.check_eligibility(
            "Small Farmer Input Support",
            {"occupation": "farmer", "annual_income": None, "land_acres": 2, "land_access": None, "age": None},
        )
        self.assertIsNone(missing["eligible"])
        self.assertEqual(missing["status"], "POTENTIALLY ELIGIBLE")
        self.assertIn("annual_income", missing["missing_fields"])
        with self.assertRaises(ValueError):
            rules.check_eligibility(
                "Small Farmer Input Support",
                {**small_farmer, "annual_income": -1},
            )
        with self.assertRaises(ValueError):
            rules.check_eligibility("Unknown scheme", small_farmer)

    def test_checklist_matching_requires_specific_document_terms(self):
        land_notice = {"file_name": "land-notice.txt", "extracted_text": "Hearing notice"}
        land_record = {"file_name": "survey-record.txt", "extracted_text": "Survey record"}
        checklist = rules.document_checklist(
            ["Land notice", "Land record"], [land_notice]
        )
        self.assertEqual(checklist, [("Land notice", True), ("Land record", False)])
        self.assertEqual(
            rules.document_checklist(["Land record"], [land_record]), [("Land record", True)]
        )

    def test_claim_verification_handles_negated_official_status(self):
        result = rules.verify_claim("JanSahay is not an official government portal")
        self.assertEqual(result["status"], "VERIFIED")
        self.assertFalse(result["live_verification"])

    def test_volunteer_requests_can_be_listed_without_citizen_filter(self):
        request_id = db.log_interaction(
            "JS-C10245", "volunteer_request", "JS-CASE1001", "Pending volunteer follow-up", self.database_path
        )
        results = db.list_interactions(None, "volunteer_request", self.database_path)
        self.assertEqual(results[0]["interaction_id"], request_id)

    def test_claim_check_has_all_four_demo_outcomes_and_rejects_empty_text(self):
        examples = (
            ("JanSahay is an official government portal", "FALSE"),
            ("JanSahay prototype uses local demo data", "VERIFIED"),
            ("Please send OTP to get guaranteed approval", "SUSPICIOUS"),
            ("Pay Rs 500 to activate the farmer benefit", "SUSPICIOUS"),
            ("What is the current application deadline?", "UNVERIFIED"),
        )
        for claim, expected in examples:
            with self.subTest(claim=claim):
                result = rules.verify_claim(claim)
                self.assertEqual(result["status"], expected)
                self.assertTrue(result["explanation"])
                self.assertTrue(result["reasons"])
                self.assertIn("recommended_action", result)
                self.assertFalse(result["live_verification"])
                self.assertEqual(result["evidence_links"], [])
        with self.assertRaises(ValueError):
            rules.verify_claim("  ")

    def test_document_extraction_and_errors(self):
        text = rules.extract_document("notice.txt", b"Hearing notice for land survey 12.")
        self.assertIn("Hearing notice", text)
        explanation = rules.explain_document(text)
        self.assertIn("notice or deadline information", explanation)

        pdf_content = b"BT /F1 12 Tf 72 720 Td (Land notice demo) Tj ET\n"
        pdf_objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            f"<< /Length {len(pdf_content)} >>\nstream\n".encode() + pdf_content + b"endstream",
        ]
        pdf_bytes = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for object_number, content in enumerate(pdf_objects, start=1):
            offsets.append(len(pdf_bytes))
            pdf_bytes.extend(f"{object_number} 0 obj\n".encode() + content + b"\nendobj\n")
        xref_offset = len(pdf_bytes)
        pdf_bytes.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
        pdf_bytes.extend(b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]))
        pdf_bytes.extend(
            f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode()
        )
        self.assertIn("Land notice demo", rules.extract_document("notice.pdf", bytes(pdf_bytes)))

        from docx import Document

        document = Document()
        document.add_paragraph("Land record for demo survey 12.")
        output = BytesIO()
        document.save(output)
        self.assertIn("demo survey", rules.extract_document("record.docx", output.getvalue()))

        for file_name, content in (("empty.txt", b"  "), ("photo.png", b"image"), ("broken.pdf", b"not a pdf")):
            with self.subTest(file_name=file_name):
                with self.assertRaises(rules.DocumentError):
                    rules.extract_document(file_name, content)

    def test_assistant_has_english_and_telugu_demo_responses(self):
        english = rules.assistant_reply("What documents should I bring?", "English")
        telugu = rules.assistant_reply("documents", "Telugu")
        self.assertIn("bank passbook", english)
        self.assertIn("ప్రత్యక్ష ప్రభుత్వ సేవ కాదు", telugu)
        with self.assertRaises(ValueError):
            rules.assistant_reply("  ", "English")


if __name__ == "__main__":
    unittest.main()