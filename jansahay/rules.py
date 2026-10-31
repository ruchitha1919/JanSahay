"""Deterministic, explicitly simulated rules for the JanSahay prototype."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

from . import i18n

MAX_DOCUMENT_BYTES = 5 * 1024 * 1024
MAX_PDF_PAGES = 30


SCHEMES = (
    {
        "name": "Small Farmer Input Support",
        "description": "Demonstration support for essential seeds, fertilizer, and other farm inputs.",
        "who_can_apply": "Small and marginal farmers who cultivate their own or leased land.",
        "criteria": "Applicant must be a farmer, be at least 18, meet the income limit, and cultivate no more than 5 acres.",
        "age_requirement": "18 years or older.",
        "land_requirement": "Own or cultivate owned/leased farmland; maximum 5 acres.",
        "income_requirement": "Annual household income up to Rs 2,50,000.",
        "documents": ["Aadhaar copy", "Land record", "Bank passbook"],
        "procedure": "Review the checklist, prepare copies, and ask a local service desk or volunteer to help submit the relevant form.",
        "assistance": "This demonstration describes possible input-cost support; no benefit or payment is provided by this prototype.",
        "required_fields": ("age", "occupation", "annual_income", "land_acres", "land_access"),
        "eligible_occupations": ("farmer",),
        "min_age": 18,
        "max_income": 250000,
        "max_land": 5,
    },
    {
        "name": "Agricultural Subsidy Assistance",
        "description": "Demonstration guidance for farmers exploring an agricultural equipment or input subsidy.",
        "who_can_apply": "Farmers and agricultural workers who cultivate farmland and need help understanding a subsidy application.",
        "criteria": "Applicant must be at least 18, have an agricultural occupation, meet the income limit, and cultivate no more than 10 acres.",
        "age_requirement": "18 years or older.",
        "land_requirement": "Own or cultivate owned/leased farmland; maximum 10 acres.",
        "income_requirement": "Annual household income up to Rs 4,00,000.",
        "documents": ["Aadhaar copy", "Land record", "Bank passbook", "Income certificate"],
        "procedure": "Confirm the relevant subsidy with an authorized office, gather the checklist, and request help with the application form.",
        "assistance": "This demonstration offers application guidance only; it does not grant a subsidy or confirm an official scheme.",
        "required_fields": ("age", "occupation", "annual_income", "land_acres", "land_access"),
        "eligible_occupations": ("farmer", "farm worker", "cultivator"),
        "min_age": 18,
        "max_income": 400000,
        "max_land": 10,
    },
    {
        "name": "Land Notice Assistance",
        "description": "Demonstration guidance for understanding a land or revenue notice and organizing next steps.",
        "who_can_apply": "A landowner, authorized cultivator, or rural citizen who has received a land-related notice.",
        "criteria": "Applicant must be at least 18, have access to the relevant land, and have a land notice to review.",
        "age_requirement": "18 years or older.",
        "land_requirement": "Own or be authorized to cultivate the land named in the notice; no acreage or income limit.",
        "income_requirement": "No income limit is used in this demonstration rule.",
        "documents": ["Land notice", "Land record", "Identity document"],
        "procedure": "Keep the notice and land record together, note any deadline, and ask an authorized office or qualified helper about next steps.",
        "assistance": "This demonstration can help organize a checklist; it is not legal advice and cannot interpret an official decision.",
        "required_fields": ("age", "land_access", "has_land_notice"),
        "eligible_occupations": (),
        "min_age": 18,
        "max_income": None,
        "max_land": None,
    },
    {
        "name": "Farmer Document Assistance",
        "description": "Demonstration help for farmers who need to understand or organize application documents.",
        "who_can_apply": "Farmers and cultivators who need help preparing or replacing documents for a government-service request.",
        "criteria": "Applicant must be at least 18, identify as a farmer/cultivator, have access to farmland, and need document assistance.",
        "age_requirement": "18 years or older.",
        "land_requirement": "Own, lease, or be authorized to cultivate farmland; no acreage limit.",
        "income_requirement": "No income limit is used in this demonstration rule.",
        "documents": ["Identity document", "Land record", "Bank passbook", "Relevant application form"],
        "procedure": "Choose the request, compare documents with its checklist, and ask a volunteer or service desk for help with missing items.",
        "assistance": "This demonstration provides document guidance only; it does not issue or authenticate documents.",
        "required_fields": ("age", "occupation", "land_access", "needs_document_help"),
        "eligible_occupations": ("farmer", "cultivator", "farm worker"),
        "min_age": 18,
        "max_income": None,
        "max_land": None,
    },
    {
        "name": "Crop Assistance Support",
        "description": "Demonstration guidance for farmers reporting crop loss and seeking help with next steps.",
        "who_can_apply": "Farmers who cultivate an affected field and need assistance organizing crop-loss information.",
        "criteria": "Applicant must be at least 18, be a farmer, cultivate no more than 10 acres, and report crop loss.",
        "age_requirement": "18 years or older.",
        "land_requirement": "Own or cultivate owned/leased farmland affected by crop loss; maximum 10 acres.",
        "income_requirement": "No income limit is used in this demonstration rule.",
        "documents": ["Identity document", "Land record", "Crop loss evidence", "Bank passbook"],
        "procedure": "Record the affected crop and dates, keep supporting documents, and confirm reporting requirements with an authorized local office.",
        "assistance": "This demonstration helps organize information; it does not verify damage or promise compensation.",
        "required_fields": ("age", "occupation", "land_acres", "land_access", "crop_loss"),
        "eligible_occupations": ("farmer",),
        "min_age": 18,
        "max_income": None,
        "max_land": 10,
    },
)

SERVICE_DIRECTORY = (
    {
        "type": "Government office (simulated)",
        "name": "Karimnagar Citizen Service Desk",
        "area": "Karimnagar",
        "services": "Scheme guidance, form support, and document checklist review",
        "hours": "Weekdays, 10:00-17:00 (demo listing)",
    },
    {
        "type": "Authorized service centre (simulated)",
        "name": "District e-Service Help Point",
        "area": "Karimnagar district",
        "services": "Form navigation, document checklist review, and referrals",
        "hours": "By appointment (demo listing)",
    },
    {
        "type": "NGO (simulated)",
        "name": "Rural Community Support Desk",
        "area": "Online demo",
        "services": "Assisted access, request follow-up, and application navigation",
        "hours": "Demo availability only",
    },
)

CLAIM_EXAMPLES = (
    ("JanSahay is not an official government portal", "VERIFIED"),
    ("JanSahay is an official government portal", "FALSE"),
    ("Please send OTP to get guaranteed approval", "SUSPICIOUS"),
    ("A new agricultural benefit starts tomorrow", "UNVERIFIED"),
)


class DocumentError(ValueError):
    """Raised when a demo upload cannot be read or is unsupported."""


def list_demo_schemes() -> list[dict[str, object]]:
    return [dict(scheme) for scheme in SCHEMES]


def get_scheme(scheme_name: str) -> dict[str, object]:
    scheme = next((item for item in SCHEMES if item["name"] == scheme_name), None)
    if scheme is None:
        raise ValueError("Choose a scheme from the demonstration list.")
    return dict(scheme)


def check_eligibility(scheme_name: str, profile: dict[str, object]) -> dict[str, object]:
    scheme = get_scheme(scheme_name)
    missing = [
        field
        for field in scheme["required_fields"]
        if profile.get(field) is None or str(profile.get(field)).strip().casefold() in {"", "not sure"}
    ]
    occupation = str(profile.get("occupation") or "").strip().casefold()
    income = profile.get("annual_income")
    land = profile.get("land_acres")
    age = profile.get("age")

    for label, value in (("annual income", income), ("land holding", land), ("age", age)):
        if value is not None and float(value) < 0:
            raise ValueError(f"{label.title()} must be zero or more.")
    if age is not None and float(age) > 120:
        raise ValueError("Age must be 120 years or less.")

    if missing:
        missing_labels = {
            "age": "age",
            "occupation": "occupation",
            "annual_income": "annual income",
            "land_acres": "land holding",
            "land_access": "land ownership or cultivation",
            "has_land_notice": "whether you have a land notice",
            "needs_document_help": "whether you need document help",
            "crop_loss": "whether crops were lost",
        }
        missing_text = ", ".join(missing_labels.get(field, field) for field in missing)
        return {
            "eligible": None,
            "status": "POTENTIALLY ELIGIBLE",
            "label": "Potentially eligible — more details needed (demonstration)",
            "explanation": f"Add or confirm: {missing_text}.",
            "reasons": [f"Missing information: {missing_text}."],
            "missing_fields": missing,
            "documents": list(scheme["documents"]),
        }

    reasons: list[str] = []
    eligible_occupations = scheme["eligible_occupations"]
    if eligible_occupations and occupation not in eligible_occupations:
        reasons.append("Occupation does not match this demonstration rule.")
    if age is not None and scheme["min_age"] is not None and float(age) < float(scheme["min_age"]):
        reasons.append(f"Applicant must be at least {scheme['min_age']} years old.")
    if income is not None and scheme["max_income"] is not None and float(income) > float(scheme["max_income"]):
        reasons.append(f"Annual income is above the Rs {scheme['max_income']:,} demonstration limit.")
    if land is not None and scheme["max_land"] is not None and float(land) > float(scheme["max_land"]):
        reasons.append(f"Land holding is above the {scheme['max_land']}-acre demonstration limit.")
    land_access = str(profile.get("land_access") or "").strip().casefold()
    if "land_access" in scheme["required_fields"] and land_access not in {
        "owned", "lease", "leased", "cultivated", "authorized",
    } and land_access != "none":
        reasons.append("Land ownership or cultivation details are not recognized.")
    if land_access == "none":
        reasons.append("The rule requires owned or cultivated land.")
    if "land_acres" in scheme["required_fields"] and land is not None and float(land) == 0:
        reasons.append("Land holding must be greater than zero for this demonstration rule.")
    for field, reason in (
        ("has_land_notice", "A land notice is required for this demonstration rule."),
        ("needs_document_help", "This rule applies when document assistance is needed."),
        ("crop_loss", "Reported crop loss is required for this demonstration rule."),
    ):
        if field in scheme["required_fields"] and profile.get(field) is False:
            reasons.append(reason)

    eligible = not reasons
    return {
        "eligible": eligible,
        "status": "ELIGIBLE" if eligible else "NOT ELIGIBLE",
        "label": "Eligible under demonstration rules" if eligible else "Not eligible under demonstration rules",
        "explanation": "The provided details match this scheme's demonstration criteria." if eligible else " ".join(reasons),
        "reasons": reasons or ["The provided details match the stated demonstration rules."],
        "missing_fields": [],
        "documents": list(scheme["documents"]),
    }


def verify_claim(claim: str, language: str = "English") -> dict[str, object]:
    cleaned = " ".join(claim.split())
    if not cleaned:
        raise ValueError("Enter a claim to check.")
    if language not in i18n.LANGUAGES:
        raise ValueError("Choose English, Telugu, or Hindi.")
    normalized = cleaned.casefold()

    positive_official = re.search(
        r"\bjansahay\b[^.!?]{0,35}\b(?:is|acts as|operates as)\b"
        r"(?!\s+(?:not|never)\b|['’]t\b)"
        r"[^.!?]{0,35}\b(?:an?\s+)?(?:official\s+)?(?:live\s+)?government\s+"
        r"(?:portal|website|service)\b",
        normalized,
    )
    negative_official = re.search(
        r"\bjansahay\b[^.!?]{0,35}\b(?:is not|isn't|isnt|never was)\b"
        r"[^.!?]{0,35}\b(?:an?\s+)?(?:official\s+)?(?:live\s+)?government\s+"
        r"(?:portal|website|service)\b",
        normalized,
    )
    negative_reference = re.search(
        r"\b(?:it|this|that)\s+(?:is not|isn't|isnt|never was)\b"
        r"[^.!?]{0,35}\b(?:an?\s+)?(?:official\s+)?(?:live\s+)?government\s+"
        r"(?:portal|website|service)\b",
        normalized,
    )
    if positive_official and (negative_official or negative_reference):
        return _claim_result(
            "UNVERIFIED",
            "The message makes conflicting statements about JanSahay's status.",
            ["Conflicting wording cannot be resolved by this local demonstration."],
            [],
            "Check the service's independently confirmed official address.",
            language,
        )
    if negative_official:
        return _claim_result(
            "VERIFIED",
            "This matches the local prototype's stated independent, demonstration-only status.",
            ["The application identifies itself as an independent local prototype."],
            [],
            "Do not treat this local result as government verification.",
            language,
        )
    if positive_official:
        return _claim_result(
            "FALSE",
            "JanSahay in this project is an independent demonstration prototype, not an official government portal.",
            ["The application identifies itself as an independent local prototype."],
            [],
            "Do not submit sensitive details through a site unless you independently confirm its official address.",
            language,
        )
    supported_local_data = re.search(
        r"\bjansahay prototype uses local demo data\b",
        normalized,
    )
    negated_local_data = re.search(
        r"\b(?:not|never|false)\b[^.!?]{0,40}\bjansahay prototype uses local demo data\b",
        normalized,
    )
    if supported_local_data and not negated_local_data:
        return _claim_result(
            "VERIFIED",
            "This matches how the local JanSahay application is configured.",
            ["This prototype stores its demonstration records in a local SQLite database."],
            [],
            "This confirms only the local demo behavior; it does not verify a government scheme.",
            language,
        )

    suspicious_patterns = (
        (r"\b(?:send|share|tell|provide|forward|reveal|disclose)\s+(?:(?:me|us)\s+)?(?:(?:your|the)\s+)?(?:otp|one[- ]time password|password)\b", "credential"),
        (r"\b(?:ask(?:s|ed)?|request(?:s|ed)?)\s+(?:you\s+)?(?:for\s+)?(?:your\s+)?(?:otp|one[- ]time password|password)\b", "credential"),
        (r"\b(?:pay|transfer|send)\s+(?:an?\s+)?(?:fee|money|payment|amount)\b", "payment"),
        (r"\b(?:pay|transfer|send)\b.{0,30}(?:\b\d+\b|₹|rs\.?|inr|fee|money|payment|amount)", "payment"),
        (r"\bguaranteed?\s+(?:approval|benefit|subsidy|payment)\b", "guarantee"),
        (r"(?:ఫీజు చెల్లించండి|డబ్బు పంపండి|రుసుము చెల్లించండి|शुल्क जमा करें|पैसे भेजें|रुपये भेजें)", "payment"),
        (r"(?:ఓటీపీ|ఒటిపి|పాస్‌వర్డ్)\s*(?:పంపండి|పంచండి|చెప్పండి|ఇవ్వండి|తెలియజేయండి)", "credential"),
        (r"(?:పంపండి|పంచండి|చెప్పండి|ఇవ్వండి).{0,20}(?:ఓటీపీ|ఒటిపి|పాస్‌వర్డ్)", "credential"),
        (r"(?:ओटीपी|पासवर्ड)\s+(?:भेजें|दें|साझा करें|बताएँ)", "credential"),
        (r"(?:भेजें|दें|साझा करें|बताएँ).{0,20}(?:ओटीपी|पासवर्ड)", "credential"),
        (r"\b(?:otp|one[- ]time password|password)\b\s*(?:भेजें|दें|साझा करें|बताइए|बताएं|माँगें|मांगे)", "credential"),
        (r"\b(?:otp|one[- ]time password|password)\b\s*(?:పంపండి|పంచండి|చెప్పండి|ఇవ్వండి|అడగండి)", "credential"),
    )
    matched_kinds = set()
    for pattern, kind in suspicious_patterns:
        if any(
            not _is_negated_request(normalized, match.start())
            for match in re.finditer(pattern, normalized, re.IGNORECASE)
        ):
            matched_kinds.add(kind)
    if matched_kinds:
        reasons = []
        if "credential" in matched_kinds:
            reasons.append("The message asks for a one-time password or other sensitive credential.")
        if "payment" in matched_kinds:
            reasons.append("The message asks for money or an upfront fee.")
        if "guarantee" in matched_kinds:
            reasons.append("The message promises a guaranteed approval or benefit.")
        return _claim_result(
            "SUSPICIOUS",
            "The message contains a common scam indicator. This rule flags wording only; it does not identify the sender.",
            reasons,
            ["Request for a password/OTP, money, or guaranteed benefit."],
            "Do not pay or share OTPs, passwords, or bank details. Confirm the claim through a trusted official channel.",
            language,
        )

    return _claim_result(
        "UNVERIFIED",
        "There is not enough curated evidence in this local demo to confirm or disprove the claim.",
        ["No matching curated demonstration claim or reliable external evidence was found."],
        [],
        "Do not forward the message as fact. Check an official government source or ask a trusted local service desk.",
        language,
    )


def _is_negated_request(text: str, match_start: int) -> bool:
    prefix = text[max(0, match_start - 70):match_start]
    clause = re.split(r"[.!?;,]", prefix)[-1]
    clause = re.split(r"\b(?:but|however|instead|yet)\b", clause)[-1]
    return bool(re.search(r"\b(?:do not|don't|dont|never|not|avoid|no)\b", clause))


def _claim_result(
    status: str,
    explanation: str,
    reasons: list[str],
    scam_indicators: list[str],
    recommended_action: str,
    language: str = "English",
) -> dict[str, object]:
    localize = lambda text: i18n.translate_text(text, language)
    return {
        "status": status,
        "explanation": localize(explanation),
        "reasons": [localize(reason) for reason in reasons],
        "evidence": [localize("Local JanSahay prototype rules only; no external source was checked.")],
        "evidence_links": [],
        "scam_indicators": [localize(indicator) for indicator in scam_indicators],
        "recommended_action": localize(recommended_action),
        "live_verification": False,
    }


def assistant_reply(
    message: str,
    language: str = "English",
    cases: list[dict[str, object]] | None = None,
) -> str:
    if not message.strip():
        raise ValueError("Type a question for the demo assistant.")
    if language not in i18n.LANGUAGES:
        raise ValueError("Choose English, Telugu, or Hindi.")

    normalized = message.casefold()
    if language == "Telugu":
        prefix = "స్థానిక నియమాల ఆధారిత నమూనా సహాయం (ప్రత్యక్ష AI కాదు): "
        unknown = "స్థానిక నమూనా సమాచారంతో ఈ ప్రశ్నకు సమాధానం ఇవ్వలేను. జాబితాలోని పథకం, పత్రాలు, సేవలు లేదా మీ అభ్యర్థన గురించి అడగండి."
        labels = {"criteria": "నమూనా అర్హత", "documents": "అవసరమైన పత్రాలు"}
    elif language == "Hindi":
        prefix = "स्थानीय नियम-आधारित नमूना सहायता (लाइव AI नहीं): "
        unknown = "स्थानीय नमूना जानकारी से इस सवाल का जवाब नहीं दे सकता। सूचीबद्ध योजना, दस्तावेज़, सेवाओं या अपने अनुरोध के बारे में पूछें।"
        labels = {"criteria": "नमूना पात्रता", "documents": "आवश्यक दस्तावेज़"}
    else:
        prefix = "Local rule-based demo guidance (not live AI): "
        unknown = "I cannot answer that from the local demo data. Ask about a listed demonstration scheme, documents, services, or your saved request."
        labels = {"criteria": "Demonstration criteria", "documents": "Required documents"}

    localize = lambda text: i18n.translate_text(text, language)
    selected_scheme = _assistant_scheme(normalized, language)
    if any(term in normalized for term in (
        "document", "paper", "checklist", "పత్ర", "పాస్‌బుక్", "दस्तावेज", "कागज़",
    )):
        if any(term in normalized for term in (
            "request", "case", "my request", "my case", "అభ్యర్థన", "కేసు", "अनुरोध", "केस",
        )):
            if cases:
                summaries = []
                for case in cases:
                    docs = ", ".join(
                        localize(str(item)) for item in case.get("required_documents", [])
                    ) or localize("No documents are listed.")
                    summaries.append(
                        f"{case.get('case_id', '')} · {localize(str(case.get('title', '')))}: {docs}"
                    )
                guidance = localize("Documents listed in your saved requests: ") + " | ".join(summaries)
            else:
                guidance = localize("No saved local requests were found for this account.")
        else:
            scheme = selected_scheme or next(
                item for item in SCHEMES if item["name"] == "Farmer Document Assistance"
            )
            documents = ", ".join(localize(str(item)) for item in scheme["documents"])
            guidance = (
                f"{localize(str(scheme['name']))}: {labels['documents']}: {documents}. "
                + localize("This is a local demonstration checklist, not an official requirement.")
            )
    elif any(term in normalized for term in (
        "status", "request", "case", "tracking", "స్థితి", "అభ్యర్థన", "కేసు",
        "स्थिति", "अनुरोध", "केस", "application", "progress", "stage",
        "దరఖాస్తు", "పురోగతి", "దశ", "आवेदन", "प्रगति", "चरण",
    )):
        if cases:
            summaries = []
            for case in cases:
                status = localize(str(case.get("status", "")))
                title = localize(str(case.get("title", "")))
                stage = localize(str(case.get("stage", "")))
                summaries.append(f"{case.get('case_id', '')} · {title} — {status}; {stage}")
            guidance = localize("Saved local requests: ") + " | ".join(summaries)
        else:
            guidance = localize("No saved local requests were found for this account.")
    elif selected_scheme is not None:
        eligibility_terms = (
            "eligible", "eligibility", "అర్హత", "పాత్ర", "पात्र", "पात्रता",
        )
        eligibility_note = (
            " " + localize(
                "Use Scheme Finder to compare your profile with these demonstration rules."
            )
            if any(term in normalized for term in eligibility_terms)
            else ""
        )
        guidance = (
            f"{localize(str(selected_scheme['name']))}: "
            f"{localize(str(selected_scheme['description']))} "
            f"{labels['criteria']}: {localize(str(selected_scheme['criteria']))} "
            f"{labels['documents']}: "
            f"{', '.join(localize(str(item)) for item in selected_scheme['documents'])}."
            f"{eligibility_note}"
        )
    elif any(term in normalized for term in (
        "eligible", "eligibility", "అర్హత", "పాత్ర", "पात्र", "पात्रता",
    )):
        guidance = localize(
            "I cannot assess personal eligibility without a selected scheme and profile. "
            "Open Scheme Finder to compare your details with local demonstration rules."
        )
    elif any(term in normalized for term in (
        "scheme", "eligible", "eligibility", "farmer", "agriculture", "crop",
        "పథక", "అర్హత", "రైతు", "వ్యవసాయ", "పంట", "योजना", "पात्रता", "किसान", "कृषि", "फसल",
    )):
        guidance = localize("Available local demonstration schemes: ") + "; ".join(
            f"{localize(str(item['name']))} — {localize(str(item['description']))}"
            for item in SCHEMES
        )
    elif any(term in normalized for term in (
        "service", "office", "directory", "సేవ", "కార్యాలయ", "सेवा", "कार्यालय",
    )):
        guidance = localize("Sample local service listings: ") + "; ".join(
            f"{localize(str(item['name']))} ({localize(str(item['area']))}) — "
            f"{localize(str(item['services']))}"
            for item in SERVICE_DIRECTORY
        )
    else:
        guidance = unknown
    return prefix + guidance


def _assistant_scheme(message: str, language: str) -> dict[str, object] | None:
    keywords = {
        "Small Farmer Input Support": (
            "small farmer", "input support", "seeds", "fertilizer", "చిన్న రైతు",
            "छोटे किसान", "बीज", "उर्वरक",
        ),
        "Agricultural Subsidy Assistance": (
            "agricultural subsidy", "equipment subsidy", "farm subsidy", "సబ్సిడీ",
            "వ్యవసాయ సబ్సిడీ", "कृषि सब्सिडी", "सब्सिडी",
        ),
        "Land Notice Assistance": (
            "land notice", "revenue notice", "భూ నోటీసు", "భూమి నోటీసు",
            "भूमि नोटिस", "राजस्व नोटिस",
        ),
        "Farmer Document Assistance": (
            "farmer document", "document help", "document assistance", "పత్రాల సహాయం",
            "రైతు పత్రాలు", "किसान दस्तावेज़", "दस्तावेज़ सहायता",
        ),
        "Crop Assistance Support": (
            "crop loss", "crop assistance", "పంట నష్టం", "పంట సహాయం",
            "फसल नुकसान", "फसल सहायता",
        ),
    }
    for scheme in SCHEMES:
        name = str(scheme["name"])
        if i18n.translate_text(name, language).casefold() in message:
            return scheme
        if any(term in message for term in keywords[name]):
            return scheme
    return None


def extract_document(file_name: str, content: bytes) -> str:
    if not content or not content.strip():
        raise DocumentError("The uploaded file is empty.")
    if len(content) > MAX_DOCUMENT_BYTES:
        raise DocumentError("The file exceeds the 5 MB demonstration limit.")
    extension = Path(file_name).suffix.casefold()
    try:
        if extension in {".txt", ".md"}:
            extracted = content.decode("utf-8-sig")
        elif extension == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(content))
            if len(reader.pages) > MAX_PDF_PAGES:
                raise DocumentError("The PDF exceeds the 30-page demonstration limit.")
            extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif extension == ".docx":
            from docx import Document

            document = Document(BytesIO(content))
            extracted = "\n".join(paragraph.text for paragraph in document.paragraphs)
        else:
            raise DocumentError("Unsupported file type. Upload a TXT, PDF, or DOCX file.")
    except DocumentError:
        raise
    except Exception as error:
        raise DocumentError("The file could not be read. Check that it is a valid TXT, PDF, or DOCX file.") from error

    extracted = re.sub(r"\s+", " ", extracted).strip()
    if not extracted:
        raise DocumentError("No readable text was found in the uploaded file.")
    return extracted


def explain_document(text: str) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        raise DocumentError("There is no extracted text to explain.")
    markers = []
    for label, terms in (
        ("identity details", ("aadhaar", "identity", "name")),
        ("land details", ("land", "survey", "plot")),
        ("bank details", ("bank", "account", "ifsc")),
        ("notice or deadline information", ("notice", "hearing", "deadline", "respond")),
    ):
        if any(term in cleaned.casefold() for term in terms):
            markers.append(label)
    summary = cleaned[:420] + ("..." if len(cleaned) > 420 else "")
    if markers:
        return "Rule-based demo summary. The text appears to mention " + ", ".join(markers) + ". Extract: " + summary
    return "Rule-based demo summary. Review the following extracted text; this does not interpret legal meaning: " + summary


def document_matches_requirement(requirement: str, document: dict[str, object]) -> bool:
    aliases = {
        "aadhaar copy": ("aadhaar", "aadhar", "uidai"),
        "land record": ("land record", "survey record", "pattadar passbook", "revenue record"),
        "bank passbook": ("bank passbook", "passbook", "bank statement"),
        "land notice": ("land notice", "revenue notice", "hearing notice"),
    }.get(requirement.casefold(), (requirement.casefold(),))
    source = " ".join(
        str(document.get(field) or "") for field in ("file_name", "extracted_text")
    )
    normalized = " " + re.sub(r"[^a-z0-9]+", " ", source.casefold()).strip() + " "
    return any(" " + alias + " " in normalized for alias in aliases)


def document_checklist(
    requirements: list[str], documents: list[dict[str, object]]
) -> list[tuple[str, bool]]:
    return [
        (requirement, any(document_matches_requirement(requirement, document) for document in documents))
        for requirement in requirements
    ]