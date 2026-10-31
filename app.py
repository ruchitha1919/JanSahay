"""Streamlit entry point for the local JanSahay citizen-assistance prototype."""

from __future__ import annotations

from datetime import date
import hashlib
import html
import os
import re

import streamlit as st

from jansahay import db, rules
from jansahay import i18n
from jansahay import voice


db.initialize_database()
st.set_page_config(page_title="JanSahay | Citizen assistance", page_icon="JS", layout="wide")
if "language" not in st.session_state:
    st.session_state["language"] = "English"
if "language_choice" not in st.session_state:
    st.session_state["language_choice"] = str(st.session_state["language"])
st = i18n.LocalizedStreamlit(st, lambda: st.session_state.get("language", "English"))

st.markdown(
    """
    <style>
    :root {
      --ink: #17333d;
      --muted: #647a80;
      --line: #dce8e7;
      --paper: #ffffff;
      --wash: #f3f8f6;
      --blue: #176f8a;
      --blue-deep: #104e64;
      --green: #2c8066;
      --green-soft: #e8f4ee;
      --amber: #a76a1b;
    }
    .stApp {
      background-color: #edf2e4;
      background-image:
        linear-gradient(180deg, rgba(250,250,242,.48), rgba(245,248,237,.38)),
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1600 1000'%3E%3Cdefs%3E%3ClinearGradient id='sky' x1='0' y1='0' x2='0' y2='1'%3E%3Cstop stop-color='%23f7f1dc'/%3E%3Cstop offset='1' stop-color='%23e4edcf'/%3E%3C/linearGradient%3E%3ClinearGradient id='field' x1='0' y1='0' x2='0' y2='1'%3E%3Cstop stop-color='%239dbb78'/%3E%3Cstop offset='1' stop-color='%235f8751'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='1600' height='1000' fill='url(%23sky)'/%3E%3Ccircle cx='1290' cy='170' r='82' fill='%23e9c976' opacity='.45'/%3E%3Cpath d='M0 470 Q210 355 430 445 T850 415 T1260 420 T1600 370 V690 H0Z' fill='%23a9bd8e' opacity='.48'/%3E%3Cpath d='M0 555 Q240 425 500 510 T1020 490 T1600 455 V760 H0Z' fill='%237e9b69' opacity='.58'/%3E%3Cpath d='M0 625 Q250 520 520 590 T1060 560 T1600 530 V1000 H0Z' fill='url(%23field)'/%3E%3Cg fill='none' stroke='%23d8dfaa' stroke-width='5' opacity='.36'%3E%3Cpath d='M-80 1020 Q400 710 760 635'/%3E%3Cpath d='M80 1040 Q500 730 860 635'/%3E%3Cpath d='M260 1050 Q620 750 960 630'/%3E%3Cpath d='M480 1050 Q760 750 1080 620'/%3E%3Cpath d='M720 1050 Q920 760 1200 610'/%3E%3Cpath d='M980 1050 Q1100 770 1320 600'/%3E%3Cpath d='M1240 1050 Q1300 790 1450 590'/%3E%3C/g%3E%3Cg fill='none' stroke='%234f7449' stroke-width='7' stroke-linecap='round' opacity='.44'%3E%3Cpath d='M80 690 q-16 -42 0 -75 m0 75 q18 -36 38 -47 m-38 47 q-23 -30 -42 -37'/%3E%3Cpath d='M210 660 q-16 -42 0 -75 m0 75 q18 -36 38 -47 m-38 47 q-23 -30 -42 -37'/%3E%3Cpath d='M1480 650 q-16 -42 0 -75 m0 75 q18 -36 38 -47 m-38 47 q-23 -30 -42 -37'/%3E%3C/g%3E%3Cg fill='%234b6040' opacity='.52'%3E%3Cpath d='M1168 603 q20 -36 52 -31 l24 12 -13 10 -36 -3 -12 23 25 31 -12 8 -35 -26 -20 38 -12 -6 15 -47 -20 -6 5 -11 23 8 10 -21Z'/%3E%3Ccircle cx='1207' cy='554' r='13'/%3E%3Cpath d='M1188 548 q19 -22 40 0 l-4 5 h-39Z'/%3E%3Cpath d='M1190 624 l-17 42 10 5 27 -40 m19 -4 20 38 11 -5 -12 -43Z'/%3E%3C/g%3E%3C/svg%3E");
      background-position: center top;
      background-size: cover;
      background-attachment: fixed;
      color: var(--ink);
    }
    [data-testid="stHeader"] { background: rgba(243,248,246,.92); }
    [data-testid="stSidebar"] { background: #e8f1ef; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: var(--ink); }
    .block-container { max-width: 1240px; padding-top: 2rem; padding-bottom: 3rem; }
    h1, h2, h3 { color: var(--ink); letter-spacing: 0; }
    h1 { font-family: Georgia, 'Times New Roman', serif; font-size: 2.15rem; }
    h2 { font-family: Georgia, 'Times New Roman', serif; font-size: 1.55rem; }
    .brand-mark { color: var(--blue-deep); font-family: Georgia, 'Times New Roman', serif;
      font-weight: 700; font-size: 1.25rem; padding: .2rem 0 .65rem; }
    .eyebrow { color: var(--green); font-size: .73rem; font-weight: 800;
      text-transform: uppercase; letter-spacing: .12em; }
    .lede { color: var(--muted); font-size: 1rem; line-height: 1.55; }
    .notice { border-left: 4px solid var(--amber); background: #fff8e9; padding: .8rem 1rem;
      color: #62451c; border-radius: 0 5px 5px 0; }
    .metric { background: var(--paper); border: 1px solid var(--line); border-top: 3px solid var(--green);
      padding: 1rem 1.1rem; min-height: 100px; }
    .metric-label { color: var(--muted); font-size: .78rem; text-transform: uppercase; font-weight: 700; }
    .metric-value { color: var(--blue-deep); font-size: 1.8rem; font-weight: 750; margin-top: .2rem; }
    .case-row { background: var(--paper); border: 1px solid var(--line); padding: 1rem 1.15rem;
      margin: .55rem 0; border-radius: 5px; }
    .case-title { font-weight: 700; color: var(--ink); font-size: 1.02rem; }
    .case-meta { color: var(--muted); font-size: .84rem; margin-top: .25rem; }
    .pill { display: inline-block; padding: .25rem .55rem; border-radius: 3px;
      background: var(--green-soft); color: #21694f; font-size: .76rem; font-weight: 700; }
    .rule-note { color: var(--muted); font-size: .82rem; padding-top: .25rem; }
    .site-header { display:flex; align-items:center; justify-content:space-between; gap:1rem;
      border-bottom:1px solid var(--line); padding:.25rem 0 .7rem; margin-bottom:1rem; }
    .site-header .brand-mark { padding:0; }
    .site-tagline { color:var(--muted); font-size:.88rem; text-align:right; }
    .site-footer { color:var(--muted); border-top:1px solid var(--line); margin-top:2rem;
      padding-top:.8rem; font-size:.82rem; text-align:center; }
    [data-testid="stVerticalBlockBorderWrapper"] { background:rgba(255,255,255,.92); }
    div.stButton > button[kind="primary"] { background: var(--blue); border-color: var(--blue); }
    div.stButton > button { border-radius: 4px; }
    @media (max-width: 700px) {
      .block-container { padding: 1.1rem .85rem 2rem; }
      h1 { font-size: 1.8rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _safe(value: object) -> str:
    return html.escape(str(value))


def _site_header() -> None:
    st.markdown(
        '<header class="site-header"><div class="brand-mark">JanSahay</div>'
        '<div class="site-tagline">Farmer and rural citizen assistance</div></header>',
        unsafe_allow_html=True,
    )


def _site_footer() -> None:
    st.markdown(
        '<footer class="site-footer">JanSahay · Local demonstration prototype · Not an official government service.</footer>',
        unsafe_allow_html=True,
    )


def _language_selector(label: str, sidebar: bool = False) -> str:
    selectbox = st.sidebar.selectbox if sidebar else st.selectbox
    labels = tuple(i18n.LANGUAGE_LABELS.values())
    current_language = str(st.session_state["language"])
    selected_label = str(
        selectbox(
            label,
            labels,
            index=i18n.LANGUAGES.index(current_language),
            key="language_choice",
        )
    )
    language = i18n.language_from_label(selected_label)
    st.session_state["language"] = language
    return language


def _case_checklist(case: dict[str, object]) -> list[tuple[str, bool]]:
    uploaded = db.list_documents(str(case["case_id"]))
    return rules.document_checklist(case["required_documents"], uploaded)


def _status_progress(status: str) -> float:
    return {
        "New": 0.15,
        "In Progress": 0.5,
        "Waiting for Documents": 0.68,
        "Resolved": 1.0,
    }.get(status, 0.1)


def _case_summary(case: dict[str, object]) -> None:
    language = str(st.session_state["language"])
    st.markdown(
        f"""<div class="case-row">
        <div class="case-title">{_safe(i18n.translate_text(str(case['title']), language))}</div>
        <div class="case-meta">{_safe(case['case_id'])} &middot; {_safe(i18n.translate_text(str(case['stage']), language))}</div>
        <div style="margin-top:.6rem"><span class="pill">{_safe(i18n.translate_text(str(case['status']), language))}</span></div>
        </div>""",
        unsafe_allow_html=True,
    )


def _login_screen() -> None:
    st.title("A clearer path to public services")
    st.markdown('<p class="lede">Explore scheme guidance, understand documents, and keep track of help requests in one place.</p>', unsafe_allow_html=True)
    st.markdown('<div class="notice"><strong>Simulation:</strong> JanSahay is an independent local prototype. Scheme checks, verification, office listings, assistant replies, and telephone behavior are demonstrations only.</div>', unsafe_allow_html=True)
    st.write("")
    sign_in, register, volunteer_access = st.tabs(["Sign in", "Create an account", "Volunteer access"])

    with sign_in:
        st.caption("Demo account: JS-C10245 / ravi123")
        with st.form("login_form"):
            identifier = st.text_input("Citizen ID or name", value="JS-C10245")
            password = st.text_input("Password", type="password", value="ravi123")
            submitted = st.form_submit_button("Sign in", type="primary")
        if submitted:
            citizen = db.authenticate(identifier, password)
            if citizen is None:
                st.error("We could not find a matching demo account. Check the ID/name and password, then try again.")
            else:
                st.session_state.pop("document_preview", None)
                st.session_state["portal_role"] = "citizen"
                st.session_state["citizen_id"] = citizen["citizen_id"]
                st.rerun()

    with register:
        st.caption("Prototype only: use synthetic demonstration information, not real citizen or financial records.")
        with st.form("registration_form"):
            name = st.text_input("Full name")
            new_password = st.text_input("Create a password", type="password")
            district = st.text_input("District")
            occupation_options = ["Farmer", "Farm worker", "Rural citizen", "Worker", "Small business", "Other"]
            selected_occupation = st.selectbox(
                "Occupation",
                i18n.translate_options(occupation_options, str(st.session_state["language"])),
            )
            occupation = i18n.original_option(
                selected_occupation,
                occupation_options,
                str(st.session_state["language"]),
            )
            age = st.number_input("Age", min_value=0, max_value=120, value=0, step=1)
            income = st.number_input("Approximate annual income (Rs)", min_value=0.0, value=0.0, step=10000.0)
            land = st.number_input("Land holding (acres)", min_value=0.0, value=0.0, step=0.5)
            synthetic_data = st.checkbox("I am using synthetic demonstration information only")
            submitted = st.form_submit_button("Create local demo account", type="primary")
        if submitted:
            if not synthetic_data:
                st.error("Confirm that you are using synthetic demonstration information only.")
            elif not name.strip() or not new_password:
                st.error("Enter a name and password to create an account.")
            else:
                try:
                    citizen_id = db.create_citizen(
                        name,
                        new_password,
                        district,
                        occupation,
                        str(st.session_state["language"]),
                        age or None,
                        income or None,
                        land or None,
                    )
                    db.create_notification(citizen_id, "Your local demo account is ready.")
                    st.session_state.pop("document_preview", None)
                    st.session_state["portal_role"] = "citizen"
                    st.session_state["citizen_id"] = citizen_id
                    st.success(f"Account created. Your demo Citizen ID is {citizen_id}.")
                    st.rerun()
                except Exception as error:
                    st.error(f"The account could not be created: {error}")

    with volunteer_access:
        st.caption("Demo volunteer access code: helper123. This is not a production access control.")
        with st.form("volunteer_login_form"):
            access_code = st.text_input("Volunteer demo access code", type="password")
            submitted = st.form_submit_button("Open volunteer desk", type="primary")
        if submitted:
            if access_code != "helper123":
                st.error("That demo volunteer access code is not valid.")
            else:
                st.session_state.pop("citizen_id", None)
                st.session_state.pop("document_preview", None)
                st.session_state["portal_role"] = "volunteer"
                st.rerun()


def _dashboard(citizen: dict[str, object]) -> None:
    cases = db.list_cases(str(citizen["citizen_id"]))
    notifications = db.list_notifications(str(citizen["citizen_id"]))
    unread_count = sum(not item["is_read"] for item in notifications)
    st.markdown('<div class="eyebrow">Your local service desk</div>', unsafe_allow_html=True)
    st.title(f"Welcome, {citizen['name'].split()[0]}")
    st.markdown(
        f'<p class="lede">Citizen ID <strong>{_safe(citizen["citizen_id"])}</strong> &middot; '
        f"{_safe(citizen['district'] or 'District not set')} &middot; {_safe(citizen['occupation'] or 'Profile incomplete')}</p>",
        unsafe_allow_html=True,
    )
    metrics = st.columns(3)
    for column, label, value in zip(
        metrics,
        ("Open requests", "Resolved", "Unread reminders"),
        (sum(case["status"] != "Resolved" for case in cases), sum(case["status"] == "Resolved" for case in cases), unread_count),
    ):
        column.markdown(
            f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>',
            unsafe_allow_html=True,
        )
    st.write("")
    left, right = st.columns([1.5, 1])
    with left:
        st.subheader("Your requests")
        if cases:
            for case in cases:
                _case_summary(case)
        else:
            st.info("You do not have a request yet. Open Scheme Finder to explore a demo service.")
    with right:
        st.subheader("Next steps")
        st.write("Check a scheme rule, review your document checklist, or ask for volunteer follow-up.")
        st.markdown('<div class="rule-note">All data stays in a local SQLite database on this machine.</div>', unsafe_allow_html=True)
        if notifications:
            st.caption("Latest reminder")
            st.write(notifications[0]["message"])
    st.markdown('<div class="notice">All assistance and status information on this page is simulated for demonstration.</div>', unsafe_allow_html=True)


def _scheme_finder(citizen: dict[str, object]) -> None:
    st.title("Scheme finder")
    st.markdown('<p class="lede">Browse sample programs and compare your profile with simple demonstration rules.</p>', unsafe_allow_html=True)
    st.info("Demonstration scheme information — not verified against an official source.")
    schemes = rules.list_demo_schemes()
    for scheme in schemes:
        with st.container(border=True):
            st.subheader(str(scheme["name"]))
            st.write(str(scheme["description"]))
            st.markdown(f"**Who can apply:** {scheme['who_can_apply']}")
            st.markdown(f"**Eligibility criteria:** {scheme['criteria']}")
            st.markdown(f"**Age requirement:** {scheme['age_requirement']}")
            st.markdown(f"**Land requirement:** {scheme['land_requirement']}")
            st.markdown(f"**Income requirement:** {scheme['income_requirement']}")
            st.markdown("**Required documents:** " + ", ".join(scheme["documents"]))
            st.markdown(f"**Application procedure:** {scheme['procedure']}")
            st.markdown(f"**Assistance information:** {scheme['assistance']}")
            if st.button("Start an assistance request", key=f"apply_{scheme['name']}"):
                case_id = db.create_case(str(citizen["citizen_id"]), str(scheme["name"]), list(scheme["documents"]))
                db.create_notification(
                    str(citizen["citizen_id"]),
                    f"Request {case_id} was created for {scheme['name']}.",
                    case_id,
                )
                st.success(f"Demo request created: {case_id}")

    st.subheader("Check your details for this scheme")
    language = str(st.session_state["language"])
    scheme_names = [str(item["name"]) for item in schemes]
    selected_label = st.selectbox(
        "Choose a demo scheme",
        i18n.translate_options(scheme_names, language),
    )
    selected = i18n.original_option(selected_label, scheme_names, language)
    selected_scheme = rules.get_scheme(selected)
    required_fields = set(selected_scheme["required_fields"])
    with st.form("eligibility_form"):
        age_known = st.checkbox("Age is known", value=citizen.get("age") is not None)
        age = st.number_input(
            "Age",
            min_value=0,
            max_value=120,
            value=int(citizen.get("age") or 0),
            step=1,
            disabled=not age_known,
        )
        profile: dict[str, object] = {"age": age if age_known else None}
        if "occupation" in required_fields:
            occupation_options = ["Farmer", "Farm worker", "Cultivator", "Other"]
            occupation_labels = i18n.translate_options(occupation_options, language)
            default_occupation = str(citizen.get("occupation") or "Farmer")
            default_index = next(
                (index for index, option in enumerate(occupation_options) if option.casefold() == default_occupation.casefold()),
                0,
            )
            selected_occupation = st.selectbox(
                "Occupation",
                occupation_labels,
                index=default_index,
            )
            profile["occupation"] = i18n.original_option(selected_occupation, occupation_options, language).casefold()
        if "annual_income" in required_fields:
            income_known = st.checkbox(
                "Annual income is known",
                value=citizen.get("annual_income") is not None,
            )
            income = st.number_input(
                "Annual income (Rs)",
                min_value=0.0,
                value=float(citizen.get("annual_income") or 0),
                step=10000.0,
                disabled=not income_known,
            )
            profile["annual_income"] = income if income_known else None
        if "land_acres" in required_fields:
            land_known = st.checkbox("Land area is known", value=citizen.get("land_acres") is not None)
            land = st.number_input(
                "Land holding (acres)",
                min_value=0.0,
                value=float(citizen.get("land_acres") or 0),
                step=0.5,
                disabled=not land_known,
            )
            profile["land_acres"] = land if land_known else None
        if "land_access" in required_fields:
            land_options = [
                "Not sure",
                "Own",
                "Lease or cultivate with permission",
                "No land access",
            ]
            selected_land = st.selectbox(
                "Land ownership or cultivation",
                i18n.translate_options(land_options, language),
            )
            land_choice = i18n.original_option(selected_land, land_options, language)
            profile["land_access"] = {
                "Not sure": None,
                "Own": "owned",
                "Lease or cultivate with permission": "leased",
                "No land access": "none",
            }[land_choice]
        for field, question in (
            ("has_land_notice", "Do you have a land notice?"),
            ("needs_document_help", "Do you need help with farmer documents?"),
            ("crop_loss", "Was your crop affected or lost?"),
        ):
            if field in required_fields:
                answers = ["Not sure", "Yes", "No"]
                selected_answer = st.selectbox(question, i18n.translate_options(answers, language))
                answer = i18n.original_option(selected_answer, answers, language)
                profile[field] = {"Not sure": None, "Yes": True, "No": False}[answer]
        submitted = st.form_submit_button("Check demo eligibility", type="primary")
    if submitted:
        result = rules.check_eligibility(selected, profile)
        if result["eligible"] is True:
            st.success(result["label"])
        elif result["eligible"] is False:
            st.warning(result["label"])
        else:
            st.info(result["label"])
        st.write(result["explanation"])
        st.markdown("**Reasons:**")
        for reason in result["reasons"]:
            st.write("• " + str(reason))
        st.markdown("**Required documents:** " + ", ".join(result["documents"]))
        st.caption("These are demonstration rules and not an official eligibility decision.")


def _assistant(citizen: dict[str, object], language: str) -> None:
    st.title("JanSahay assistant")
    st.markdown('<p class="lede">A local rule-based assistant using demonstration scheme and case data. No live AI or government systems are connected.</p>', unsafe_allow_html=True)
    history = db.list_interactions(str(citizen["citizen_id"]), "assistant")
    for item in history:
        with st.chat_message("user"):
            st.write(item["user_input"])
        with st.chat_message("assistant"):
            st.write(item["response"])
    prompt = st.chat_input("Ask about schemes, documents, or a request")
    if prompt:
        try:
            response = rules.assistant_reply(
                prompt,
                language,
                db.list_cases(str(citizen["citizen_id"])),
            )
            db.log_interaction(str(citizen["citizen_id"]), "assistant", prompt, response)
            st.rerun()
        except ValueError as error:
            st.error(str(error))


def _claim_check(citizen: dict[str, object]) -> None:
    st.title("Check a claim")
    st.markdown('<p class="lede">Compare a message with local demo rules. Nothing here contacts an official source.</p>', unsafe_allow_html=True)
    with st.form("claim_form"):
        claim = st.text_area(
            "Paste a suspicious message, WhatsApp forward, scheme claim, or payment request",
            placeholder="For example: JanSahay is an official government portal",
        )
        uploaded_claim = st.file_uploader(
            "Upload a notice or text document (TXT, MD, PDF, DOCX)",
            type=["txt", "md", "pdf", "docx"],
            key="claim_upload",
        )
        submitted = st.form_submit_button("Check claim", type="primary")
    if submitted:
        try:
            submitted_text = claim.strip()
            if uploaded_claim is not None:
                document_text = rules.extract_document(
                    uploaded_claim.name,
                    uploaded_claim.getvalue(),
                )
                submitted_text = "\n".join(part for part in (submitted_text, document_text) if part)
            result = rules.verify_claim(
                submitted_text,
                str(st.session_state["language"]),
            )
            status = str(result["status"])
            db.log_interaction(
                str(citizen["citizen_id"]),
                "verification",
                submitted_text,
                f"{status}: {result['explanation']}",
            )
            st.subheader(status)
            st.markdown("**Verification status:** " + status)
            st.markdown("**Explanation:** " + str(result["explanation"]))
            st.markdown("**Reasons for this result:**")
            for reason in result["reasons"]:
                st.write("• " + str(reason))
            st.markdown("**Supporting evidence:**")
            for evidence in result["evidence"]:
                st.write("• " + str(evidence))
            evidence_links = result["evidence_links"]
            if evidence_links:
                for link in evidence_links:
                    st.markdown(f"[{link}]({link})")
            else:
                st.caption("No external references are available for this demonstration result.")
            st.markdown("**Scam indicators:**")
            indicators = result["scam_indicators"]
            if indicators:
                for indicator in indicators:
                    st.warning(str(indicator))
            else:
                st.write("No common scam indicators were found in this text.")
            st.markdown("**Recommended action:** " + str(result["recommended_action"]))
            st.caption("This is a rule-based demonstration, not live fact-checking or official government verification.")
        except ValueError as error:
            st.error(str(error))
    with st.expander("Curated demonstration examples"):
        for example_claim, example_status in rules.CLAIM_EXAMPLES:
            st.write(f"{example_status}: {example_claim}")


def _documents(citizen: dict[str, object]) -> None:
    st.title("Document helper")
    st.markdown('<p class="lede">Extract text from TXT, PDF, or DOCX files and get a basic rule-based explanation.</p>', unsafe_allow_html=True)
    st.caption("Avoid uploading sensitive originals. This local prototype is not a secure document vault or legal review service.")
    uploaded = st.file_uploader("Choose a document", type=["txt", "md", "pdf", "docx"], key="document_upload")
    if uploaded is not None and st.button("Extract text and explain", type="primary"):
        try:
            contents = uploaded.getvalue()
            text = rules.extract_document(uploaded.name, contents)
            st.session_state["document_preview"] = {
                "file_name": uploaded.name,
                "fingerprint": hashlib.sha256(contents).hexdigest(),
                "text": text,
                "explanation": rules.explain_document(text),
            }
        except rules.DocumentError as error:
            st.error(str(error))

    preview = st.session_state.get("document_preview")
    if uploaded is not None and preview:
        fingerprint = hashlib.sha256(uploaded.getvalue()).hexdigest()
        if fingerprint != preview["fingerprint"]:
            st.session_state.pop("document_preview", None)
            preview = None
    if preview:
        st.subheader("Extracted text")
        st.text_area("Text preview", value=preview["text"], height=150, disabled=True)
        st.subheader("Simple explanation")
        st.write(preview["explanation"])
        st.caption("Rule-based demo explanation only; it does not interpret legal meaning or verify authenticity.")
        cases = db.list_cases(str(citizen["citizen_id"]))
        if not cases:
            st.info("Create a request before attaching a document.")
        else:
            case_by_label = {f"{case['case_id']} · {case['title']}": case for case in cases}
            selected_label = st.selectbox("Attach this document to a request", list(case_by_label))
            if st.button("Submit document to request", type="primary"):
                selected_case = case_by_label[selected_label]
                document_id = db.add_document(
                    str(selected_case["case_id"]),
                    str(citizen["citizen_id"]),
                    str(preview["file_name"]),
                    str(preview["text"]),
                    str(preview["explanation"]),
                )
                db.create_notification(
                    str(citizen["citizen_id"]),
                    f"{preview['file_name']} was attached to request {selected_case['case_id']}.",
                    str(selected_case["case_id"]),
                )
                st.session_state.pop("document_preview", None)
                st.success(f"Document submitted locally (reference {document_id}).")
                st.rerun()

    attached = [
        document
        for case in db.list_cases(str(citizen["citizen_id"]))
        for document in db.list_documents(str(case["case_id"]))
    ]
    if attached:
        st.subheader("Local upload retention")
        with st.form("clear_local_documents_form"):
            confirmed = st.checkbox("Permanently delete all documents attached to my demo requests")
            clear_requested = st.form_submit_button("Clear all my attachments")
        if clear_requested:
            if not confirmed:
                st.error("Confirm deletion before clearing your attachments.")
            else:
                deleted_count = db.delete_citizen_documents(str(citizen["citizen_id"]))
                st.session_state.pop("document_preview", None)
                st.success(f"Deleted {deleted_count} local attachment(s).")
                st.rerun()


def _cases(citizen: dict[str, object]) -> None:
    st.title("Request tracking")
    st.markdown('<p class="lede">View progress, update a demo request, and keep document requirements together.</p>', unsafe_allow_html=True)
    cases = db.list_cases(str(citizen["citizen_id"]))
    if not cases:
        st.info("No requests yet. Use Scheme Finder to create one.")
        return
    for case in cases:
        with st.container(border=True):
            st.subheader(str(case["title"]))
            st.caption(f"{case['case_id']} · Updated {case['updated_at'][:10]}")
            st.write(f"Status: **{case['status']}** · Current stage: **{case['stage']}**")
            st.progress(_status_progress(str(case["status"])))
            st.markdown("**Document checklist**")
            checklist = _case_checklist(case)
            if checklist:
                for requirement, submitted in checklist:
                    st.write(("✓ Submitted" if submitted else "○ Pending") + f" · {requirement}")
            else:
                st.caption("No documents are required for this request yet.")
            attached = db.list_documents(str(case["case_id"]))
            if attached:
                st.caption("Submitted files (inferred from file names and text; not official validation):")
                for document in attached:
                    left, right = st.columns([1, 0.25])
                    left.write(str(document["file_name"]))
                    if right.button("Delete", key=f"delete_document_{document['document_id']}"):
                        db.delete_document(int(document["document_id"]))
                        st.success("Local attachment deleted.")
                        st.rerun()
            with st.form(f"case_update_{case['case_id']}"):
                status_options = list(db.CASE_STATUSES)
                selected_status = st.selectbox(
                    "Update demo status",
                    i18n.translate_options(status_options, str(st.session_state["language"])),
                    index=status_options.index(str(case["status"])),
                    key=f"status_{case['case_id']}",
                )
                next_status = i18n.original_option(
                    selected_status,
                    status_options,
                    str(st.session_state["language"]),
                )
                current_stage = str(case["stage"])
                displayed_stage = i18n.translate_text(current_stage, str(st.session_state["language"]))
                entered_stage = st.text_input(
                    "Progress stage",
                    value=displayed_stage,
                    key=f"stage_{case['case_id']}",
                )
                next_stage = current_stage if entered_stage == displayed_stage else entered_stage
                submitted = st.form_submit_button("Save request update")
            if submitted:
                try:
                    if not next_stage.strip():
                        raise ValueError("Enter a progress stage.")
                    db.update_case(str(case["case_id"]), status=next_status, stage=next_stage.strip())
                    db.create_notification(
                        str(citizen["citizen_id"]),
                        f"Request {case['case_id']} was updated to {next_status}.",
                        str(case["case_id"]),
                    )
                    st.success("Request update saved locally.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))


def _telephone(citizen: dict[str, object], language: str) -> None:
    st.title("Telephone assistance")
    st.markdown('<p class="lede">Try the local call and IVR simulation. No telephone connection is made.</p>', unsafe_allow_html=True)
    st.markdown('<div class="notice">Simulation only: the demo link does not reach a JanSahay office or government helpline.</div>', unsafe_allow_html=True)
    icon_column, contact_column = st.columns([0.12, 1])
    with icon_column:
        st.markdown(
            '<div style="font-size:2.4rem;color:#176f8a;line-height:1" aria-hidden="true">☎</div>',
            unsafe_allow_html=True,
        )
    with contact_column:
        st.subheader("JanSahay IVR")
        phone_number = os.environ.get("JANSAHAY_DEMO_PHONE_NUMBER", "+91 00000 00000").strip()
        phone_digits = re.sub(r"[^\d+]", "", phone_number)
        if not re.fullmatch(r"\+?\d{6,15}", phone_digits):
            st.error("The configured demonstration telephone number is invalid.")
        else:
            st.write(f"Demonstration telephone number: **{phone_number}**")
            st.link_button(
                "Call JanSahay",
                f"tel:{phone_digits}",
                help="Opens the phone dialer with a fictional demonstration number.",
                type="primary",
            )
        st.caption("Fictional demonstration number. Actual telephone connectivity is not configured.")
        st.write("Call for help understanding a scheme, checking a request, or preparing documents. The number does not connect to a real service.")

    st.subheader("Try the simulated IVR")
    st.caption("Choose a language, then play an example response. No call is placed.")
    ivr_language = st.selectbox(
        "Choose IVR language",
        tuple(i18n.LANGUAGE_LABELS.values()),
        index=i18n.LANGUAGES.index(language),
        key="ivr_language_choice",
    )
    ivr_language = i18n.language_from_label(ivr_language)
    ivr_options = [
        "1 · Language and voice interaction",
        "2 · Citizen ID assistance",
        "3 · Case status assistance",
        "4 · Document guidance",
        "5 · Speak to a volunteer",
    ]
    selected_ivr_option = st.selectbox(
        "Choose an IVR option",
        i18n.translate_options(ivr_options, ivr_language),
        key="ivr_option",
    )
    option = i18n.original_option(selected_ivr_option, ivr_options, ivr_language)
    submitted = st.button("Play simulated IVR response", type="primary")
    response_text = {
        "English": {
            ivr_options[0]: "Choose a language above. For a voice interaction, ask about scheme eligibility, documents, or request status.",
            ivr_options[1]: f"Your local demonstration Citizen ID is {citizen['citizen_id']}. Keep it private outside this prototype.",
            ivr_options[2]: "Your request statuses are shown below. This is local demonstration data.",
            ivr_options[3]: "Check the selected scheme's document list. Demonstration examples include an identity document, land record, and bank passbook.",
            ivr_options[4]: "Choose a request below to record a local volunteer follow-up request.",
        },
        "Telugu": {
            ivr_options[0]: "పైన భాషను ఎంచుకోండి. వాయిస్ సహాయం కోసం పథక అర్హత, పత్రాలు లేదా అభ్యర్థన స్థితి గురించి అడగండి.",
            ivr_options[1]: f"మీ స్థానిక నమూనా పౌర ID {citizen['citizen_id']}. ఈ నమూనా వెలుపల దాన్ని గోప్యంగా ఉంచండి.",
            ivr_options[2]: "మీ అభ్యర్థనల స్థితి కింద చూపబడింది. ఇది స్థానిక నమూనా సమాచారం.",
            ivr_options[3]: "ఎంచుకున్న పథకానికి అవసరమైన పత్రాల జాబితాను చూడండి. నమూనా పత్రాల్లో గుర్తింపు పత్రం, భూమి రికార్డు, బ్యాంకు పాస్‌బుక్ ఉండవచ్చు.",
            ivr_options[4]: "స్థానిక స్వచ్ఛంద సేవకుల సహాయ అభ్యర్థన నమోదు చేయడానికి కింద అభ్యర్థనను ఎంచుకోండి.",
        },
        "Hindi": {
            ivr_options[0]: "ऊपर भाषा चुनें। आवाज़ से योजना पात्रता, दस्तावेज़ या अनुरोध स्थिति के बारे में पूछें।",
            ivr_options[1]: f"आपका स्थानीय नमूना नागरिक ID {citizen['citizen_id']} है। इस नमूने के बाहर इसे गोपनीय रखें।",
            ivr_options[2]: "आपके अनुरोधों की स्थिति नीचे दी गई है। यह स्थानीय नमूना जानकारी है।",
            ivr_options[3]: "चुनी हुई योजना की दस्तावेज़ सूची देखें। नमूने में पहचान दस्तावेज़, भूमि रिकॉर्ड और बैंक पासबुक हो सकते हैं।",
            ivr_options[4]: "स्थानीय स्वयंसेवक सहायता का अनुरोध दर्ज करने के लिए नीचे अनुरोध चुनें।",
        },
    }
    if submitted:
        response = response_text[ivr_language][option]
        db.log_interaction(str(citizen["citizen_id"]), "ivr", option, response)
        st.info(response)
        st.caption("This is a local simulation; no call or audio was placed.")
    cases = db.list_cases(str(citizen["citizen_id"]))
    if option == "3 · Case status assistance":
        if cases:
            for case in cases:
                st.write(f"{case['title']} · {case['status']} · {case['stage']}")
        else:
            st.info("No requests yet. Use Scheme Finder to create one.")
    if option == "5 · Speak to a volunteer":
        if not cases:
            st.info("Create a request before asking for volunteer follow-up.")
        else:
            choices = {
                f"{case['case_id']} · {case['title']}": case
                for case in cases
            }
            choice_labels = list(choices)
            translated_choices = i18n.translate_options(choice_labels, ivr_language)
            with st.form("volunteer_follow_up_form"):
                selected_label = st.selectbox("Request follow-up for", translated_choices)
                requested = st.form_submit_button("Request volunteer follow-up", type="primary")
            if requested:
                selected = i18n.original_option(selected_label, choice_labels, ivr_language)
                case = choices[selected]
                db.log_interaction(
                    str(citizen["citizen_id"]),
                    "volunteer_request",
                    str(case["case_id"]),
                    "Pending volunteer follow-up",
                )
                db.create_notification(
                    str(citizen["citizen_id"]),
                    f"Volunteer follow-up requested for {case['case_id']}.",
                    str(case["case_id"]),
                )
                st.success("Follow-up request recorded locally for the volunteer desk.")


def _directory() -> None:
    st.title("Nearby service directory")
    st.markdown('<p class="lede">Sample listings for the prototype. Confirm details independently before visiting.</p>', unsafe_allow_html=True)
    for service in rules.SERVICE_DIRECTORY:
        with st.container(border=True):
            st.subheader(str(service["name"]))
            st.caption(str(service["type"]))
            st.write(f"**Area:** {service['area']}  \n**Services:** {service['services']}  \n**Hours:** {service['hours']}")
            st.caption("Simulated office information. Not official or real-time data.")


def _notifications(citizen: dict[str, object]) -> None:
    st.title("Reminders")
    st.markdown('<p class="lede">Set a local reminder or review request updates.</p>', unsafe_allow_html=True)
    with st.form("reminder_form"):
        reminder_date = st.date_input("Reminder date", value=date.today())
        reminder_text = st.text_input("Reminder note", placeholder="Bring your land record")
        submitted = st.form_submit_button("Save reminder", type="primary")
    if submitted:
        if not reminder_text.strip():
            st.error("Enter a reminder note.")
        else:
            db.create_notification(
                str(citizen["citizen_id"]),
                f"Reminder for {reminder_date.isoformat()}: {reminder_text.strip()}",
            )
            st.success("Reminder saved in the local database.")
            st.rerun()

    notifications = db.list_notifications(str(citizen["citizen_id"]))
    st.subheader("Your reminders and updates")
    if not notifications:
        st.info("No reminders or updates yet.")
    for item in notifications:
        with st.container(border=True):
            st.write(item["message"])
            st.caption(f"{'Read' if item['is_read'] else 'Unread'} · {item['created_at'][:16].replace('T', ' ')}")
            if not item["is_read"] and st.button("Mark as read", key=f"read_{item['notification_id']}"):
                db.mark_notification_read(int(item["notification_id"]))
                st.rerun()


def _volunteer() -> None:
    st.title("Volunteer desk")
    st.markdown('<p class="lede">Review demo requests and save a follow-up action. Citizen records shown here are synthetic prototype data.</p>', unsafe_allow_html=True)
    cases = db.list_cases()
    pending_requests = [
        item for item in db.list_interactions(None, "volunteer_request")
        if item["response"] == "Pending volunteer follow-up"
    ]
    if pending_requests:
        st.subheader("Citizen follow-up requests")
        for request in pending_requests:
            citizen = db.get_citizen(str(request["citizen_id"]))
            case = db.get_case(str(request["user_input"]))
            label = f"{citizen['name']} · {case['case_id']} · {case['title']}" if citizen and case else str(request["user_input"])
            with st.form(f"acknowledge_follow_up_{request['interaction_id']}"):
                st.write(label)
                submitted = st.form_submit_button("Acknowledge request")
            if submitted:
                db.update_interaction_response(int(request["interaction_id"]), "Volunteer follow-up acknowledged")
                if citizen and case:
                    db.create_notification(
                        str(citizen["citizen_id"]),
                        f"A volunteer acknowledged your request for {case['case_id']}.",
                        str(case["case_id"]),
                    )
                st.rerun()
    if not cases:
        st.info("There are no requests to review.")
        return
    for case in cases:
        with st.container(border=True):
            st.subheader(str(case["title"]))
            st.caption(f"{case['case_id']} · {_safe(case['status'])} · {_safe(case['stage'])}")
            with st.form(f"volunteer_{case['case_id']}"):
                status_options = list(db.CASE_STATUSES)
                selected_status = st.selectbox(
                    "Set request status",
                    i18n.translate_options(status_options, str(st.session_state["language"])),
                    index=status_options.index(str(case["status"])),
                    key=f"vol_status_{case['case_id']}",
                )
                status = i18n.original_option(
                    selected_status,
                    status_options,
                    str(st.session_state["language"]),
                )
                current_stage = str(case["stage"])
                displayed_stage = i18n.translate_text(current_stage, str(st.session_state["language"]))
                entered_stage = st.text_input(
                    "Follow-up stage",
                    value=displayed_stage,
                    key=f"vol_stage_{case['case_id']}",
                )
                stage = current_stage if entered_stage == displayed_stage else entered_stage
                note = st.text_input("Citizen update note", value="A volunteer reviewed your request.", key=f"vol_note_{case['case_id']}")
                submitted = st.form_submit_button("Save follow-up")
            if submitted:
                try:
                    if not stage.strip():
                        raise ValueError("Enter a follow-up stage.")
                    updated = db.update_case(
                        str(case["case_id"]),
                        status=status,
                        stage=stage.strip(),
                        assigned_volunteer="Demo volunteer",
                    )
                    db.create_notification(
                        str(updated["citizen_id"]),
                        note.strip() or f"Request {case['case_id']} has a volunteer update.",
                        str(case["case_id"]),
                    )
                    st.success("Follow-up saved and notification created.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))


def _insights() -> None:
    st.title("Community insights")
    st.markdown('<p class="lede">Aggregate counts from the local demo. No citizen names or IDs are shown.</p>', unsafe_allow_html=True)
    cases = db.list_cases()
    documents = [document for case in cases for document in db.list_documents(str(case["case_id"]))]
    language = str(st.session_state["language"])
    statuses = {
        i18n.translate_text(status, language): sum(case["status"] == status for case in cases)
        for status in db.CASE_STATUSES
    }
    metrics = st.columns(3)
    for column, label, value in zip(metrics, ("Total demo requests", "Documents attached", "Volunteer assigned"), (len(cases), len(documents), sum(bool(case["assigned_volunteer"]) for case in cases))):
        column.markdown(
            f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>',
            unsafe_allow_html=True,
        )
    st.subheader("Requests by status")
    st.bar_chart(statuses, horizontal=True)
    st.caption("Counts are calculated locally from synthetic prototype records and are not official statistics.")


def _portal(citizen: dict[str, object]) -> None:
    pages = {
        "Overview": _dashboard,
        "Scheme Finder": _scheme_finder,
        "Assistant": _assistant,
        "Check a Claim": _claim_check,
        "Documents": _documents,
        "Request Tracking": _cases,
        "Telephone Help": _telephone,
        "Service Directory": _directory,
        "Reminders": _notifications,
        "Community Insights": _insights,
    }
    st.sidebar.markdown('<div class="brand-mark">JanSahay</div>', unsafe_allow_html=True)
    st.sidebar.caption("CITIZEN ASSISTANCE · DEMO")
    st.sidebar.markdown(f"**{_safe(citizen['name'])}**  \n`{_safe(citizen['citizen_id'])}`")
    language = _language_selector("Application language", sidebar=True)
    voice.render(language)
    page_options = list(pages)
    selected_page = st.sidebar.radio(
        "Navigate",
        i18n.translate_options(page_options, language),
    )
    page_name = i18n.original_option(selected_page, page_options, language)
    st.sidebar.markdown("---")
    st.sidebar.caption("Assistant, verification, listings, and telephone actions are simulated.")
    if st.sidebar.button("Sign out"):
        st.session_state.pop("citizen_id", None)
        st.session_state.pop("portal_role", None)
        st.session_state.pop("document_preview", None)
        st.rerun()
    if page_name == "Assistant":
        _assistant(citizen, language)
    elif page_name == "Telephone Help":
        _telephone(citizen, language)
    else:
        pages[page_name](citizen) if page_name in {"Overview", "Scheme Finder", "Check a Claim", "Documents", "Request Tracking", "Reminders"} else pages[page_name]()


def _volunteer_portal() -> None:
    st.sidebar.markdown('<div class="brand-mark">JanSahay</div>', unsafe_allow_html=True)
    st.sidebar.caption("VOLUNTEER ASSISTED-ACCESS · DEMO")
    language = _language_selector("Application language", sidebar=True)
    voice.render(language)
    page_options = ["Volunteer Desk", "Community Insights", "Service Directory"]
    language = str(st.session_state["language"])
    selected_page = st.sidebar.radio("Navigate", i18n.translate_options(page_options, language))
    page_name = i18n.original_option(selected_page, page_options, language)
    st.sidebar.caption("Volunteer permissions are simulated for this prototype.")
    if st.sidebar.button("Sign out"):
        st.session_state.pop("portal_role", None)
        st.session_state.pop("document_preview", None)
        st.rerun()
    if page_name == "Volunteer Desk":
        _volunteer()
    elif page_name == "Community Insights":
        _insights()
    else:
        _directory()


if "citizen_id" not in st.session_state:
    st.session_state["citizen_id"] = None

active_language = str(st.session_state["language"])
_site_header()
if st.session_state.get("portal_role") != "volunteer" and st.session_state["citizen_id"] is None:
    _language_selector("Preferred language")
    active_language = str(st.session_state["language"])
    voice.render(active_language)

if st.session_state.get("portal_role") == "volunteer":
    _volunteer_portal()
elif st.session_state["citizen_id"] is None:
    _login_screen()
else:
    active_citizen = db.get_citizen(str(st.session_state["citizen_id"]))
    if active_citizen is None:
        st.session_state["citizen_id"] = None
        st.rerun()
    _portal(active_citizen)

_site_footer()