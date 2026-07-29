import csv
import io
import re
from typing import Any

import requests
import streamlit as st


st.set_page_config(
    page_title="Robot Proactive Task and Constraints",
    page_icon="robot",
    layout="wide",
)

# The public assignment table contains the fixed P001-P134 allocations.  Each
# visitor receives only the ten rows matching their `slot` URL parameter.
ASSIGNMENTS_CSV_URL = (
    "https://raw.githubusercontent.com/Lixiangqi2002/proactive-hoi-san/main/"
    "data/participant_assignments134_jrdb_hunavsim_with_vlm.csv"
)
MEDIA_MANIFEST_CSV_URL = (
    "https://huggingface.co/datasets/SelinaXiangqi/proactive-hoi-san-media/resolve/main/"
    "media_manifest.csv"
)


def get_participant_slot() -> str:
    """Read the fixed Taskflow slot from the allocated study URL."""
    slot = str(st.query_params.get("slot", "P001")).strip().upper()
    match = re.fullmatch(r"P(\d{3})", slot)
    if not match or not 1 <= int(match.group(1)) <= 134:
        st.error("This study link has an invalid participant slot.")
        st.stop()
    return slot


def get_preview_mode() -> bool:
    """Allow researchers to inspect the survey without answering every item."""
    # Preview is deliberately opt-in via a researcher-only parameter.  Old test
    # links with `preview=1` should not silently disable required-answer checks.
    value = str(st.query_params.get("researcher_preview", "")).strip().lower()
    return value in {"1", "true", "yes", "y", "preview"}


PARTICIPANT_SLOT = get_participant_slot()
PREVIEW_MODE = get_preview_mode()
TRIAL_COUNT = 10

DEFAULT_COMPLETION_URL = "https://app.prolific.com/submissions/complete?cc=CD10CDO9"
NO_CONSENT_COMPLETION_URL = "https://app.prolific.com/submissions/complete?cc=C1FAF7FV"
FAILED_CHECK_COMPLETION_URL = "https://app.prolific.com/submissions/complete?cc=CI0WWZBS"

ATTITUDES = [
    "A. I am very interested in them and generally positive.",
    "B. I am somewhat interested or open-minded.",
    "C. I am neutral.",
    "D. I am cautious but willing to evaluate them fairly.",
    "E. I strongly dislike them and would prefer not to engage with this topic.",
]

CLARITY_SCALE = [
    "Not clear at all",
    "Mostly unclear",
    "Partly clear, but uncertain",
    "Mostly clear",
    "Completely clear",
]

PROACTIVE_NEED_SCALE = [
    "Definitely not needed",
    "Probably not needed",
    "Unsure / depends on other information",
    "Probably needed",
    "Definitely needed",
]

SITUATION_CONCERNS = [
    "The person directly involved may need assistance.",
    "The person directly involved may be at risk.",
    "Nearby people may be at risk or otherwise affected.",
    "The object or ongoing event may create a local hazard.",
    "The person's access to the relevant object or work area may be disrupted.",
    "The person's likely walking or movement path may be disrupted.",
    "A nearby corridor, doorway, or shared route may become obstructed.",
    "The robot could disturb or interrupt the ongoing human-object interaction.",
    "The situation may change or is uncertain, so continued observation may be useful.",
]
NO_SPECIAL_CONCERN = "No special concern is present; the event does not require special consideration."
NOT_ENOUGH_CONCERN_INFO = "There is not enough information to determine the relevant concerns."

PRIMARY_RESPONSES = [
    "Continue - Continue its original plan without any special response.",
    "Monitor - Continue observing the event before deciding whether intervention is needed.",
    "Avoid - Adjust its movement to stay clear of the event and avoid interfering.",
    "Assist - Offer or provide help to the relevant person.",
    "Warn - Alert the relevant person or people about a possible problem or risk.",
    "Not enough information to decide.",
]
SECONDARY_RESPONSES = ["Continue", "Monitor", "Avoid", "Assist", "Warn"]
NO_ADDITIONAL_RESPONSE = "No additional response would be appropriate."

CONSTRAINT_ROWS = [
    "Keep the space around and between the person and the relevant object clear so that the interaction is not interrupted.",
    "Avoid blocking the person's likely walking or movement path.",
    "Keep any nearby corridor, doorway, or shared passage clear.",
    "Keep the robot out of the area around a dangerous object or event.",
    "Avoid passing through the immediate area around the relevant person.",
    "Keep a greater-than-usual safety distance from the relevant person.",
    "Keep a greater-than-usual safety distance from a dangerous object.",
    "Move slowly and predictably near the event.",
    "Respond or approach more quickly only if the situation appears urgent.",
    "Keep the relevant person, object, or event within the robot's view.",
    "Approach or communicate with the relevant person to offer assistance.",
    "Warn the relevant person about a possible danger.",
    "Alert other nearby people who may be affected.",
]
CONSTRAINT_SCALE = [
    "Required",
    "Helpful but not required",
    "Not needed in this event",
    "Inappropriate or potentially disruptive",
    "Cannot determine from the available information",
]

ATTRIBUTE_SCALE = [
    "Completely inaccurate",
    "Mostly inaccurate",
    "Partly accurate",
    "Mostly accurate",
    "Completely accurate",
    "Cannot judge from the model input",
]

CONSENT_STATEMENTS = [
    "I confirm that I have read and understood the participant information for this study.",
    "I confirm that I am aged 18 or over.",
    "I understand that my participation is voluntary and that I may stop taking part at any time before submitting the questionnaire, without giving a reason.",
    "I understand what participation involves, including reviewing 10 RGB scene frames, reading brief text descriptions, and answering questions about proactive robot responses and navigation constraints.",
    "I understand that the questionnaire will not ask for my name, email address, signature, or other directly identifying information.",
    "I understand that my Prolific ID may be used only to manage participation, payment, completion checking, and data quality review.",
    "I understand that confidentiality and anonymity will be maintained and that research outputs will not identify me as an individual participant.",
    "I understand that, after I submit my pseudonymous questionnaire responses and they have been combined with other data, it may not be possible to withdraw them.",
    "I agree for my pseudonymous questionnaire responses to be used for academic research, including anonymised or aggregated reporting and appropriate research-data retention or sharing.",
]


@st.cache_data(ttl=300, show_spinner="Loading your assigned study materials...")
def load_assigned_trials(slot: str) -> list[dict[str, Any]]:
    """Load the ten pre-assigned rows for one participant from GitHub."""
    response = requests.get(ASSIGNMENTS_CSV_URL, timeout=30)
    response.raise_for_status()
    # lstrip handles the current JRDB file's UTF-8 BOM and future clean files.
    rows = csv.DictReader(io.StringIO(response.text.lstrip("\ufeff")))
    trials = [
        row for row in rows
        if str(row.get("participant_id", "")).strip().upper() == slot
    ]
    trials.sort(key=lambda row: int(row.get("trial_order", 0)))
    if len(trials) != TRIAL_COUNT:
        raise RuntimeError(f"Expected {TRIAL_COUNT} trials for {slot}, received {len(trials)}.")
    return trials


@st.cache_data(ttl=300, show_spinner="Loading hosted media links...")
def load_media_manifest(slot: str) -> dict[int, dict[str, str]]:
    """Load direct Hugging Face media URLs for this participant slot."""
    response = requests.get(MEDIA_MANIFEST_CSV_URL, timeout=30)
    response.raise_for_status()
    rows = csv.DictReader(io.StringIO(response.text.lstrip("\ufeff")))
    manifest: dict[int, dict[str, str]] = {}
    for row in rows:
        if str(row.get("participant_id", "")).strip().upper() != slot:
            continue
        manifest[int(row["trial_order"])] = row
    if len(manifest) != TRIAL_COUNT:
        raise RuntimeError(f"Expected {TRIAL_COUNT} hosted media rows for {slot}, received {len(manifest)}.")
    return manifest


def get_trial(trial_number: int) -> dict[str, Any]:
    """Return this slot's actual assigned trial and any available VLM fields."""
    if "assigned_trials" not in st.session_state:
        st.session_state.assigned_trials = load_assigned_trials(PARTICIPANT_SLOT)
    if "media_manifest" not in st.session_state:
        st.session_state.media_manifest = load_media_manifest(PARTICIPANT_SLOT)

    source = st.session_state.assigned_trials[trial_number - 1]
    media = st.session_state.media_manifest.get(trial_number, {})
    return {
        "scene_image_url": media.get("scene_image_url") or media.get("video_url") or source.get("image_link") or None,
        "target_annotation_image_url": media.get("target_annotation_image_url") or media.get("scene_image_url") or media.get("image_url") or source.get("image_link") or None,
        "text_description": source.get("text_description") or None,
        "vlm_input_image_url": media.get("vlm_input_image_url") or media.get("image_url") or source.get("image_link") or None,
        "human_state": source.get("human_state") or None,
        "object_property": source.get("object_property") or None,
        "spatial_context": source.get("spatial_context") or None,
        "risk_factor": source.get("risk_factor") or None,
    }


def display_attribute(value: str | None) -> str:
    return value if value else "No prediction was supplied for this trial."


def primary_label_to_short_label(value: str | None) -> str | None:
    if not value:
        return None
    for label in SECONDARY_RESPONSES:
        if value.startswith(label):
            return label
    return None


def initialise_state() -> None:
    st.session_state.setdefault("page", "consent")
    st.session_state.setdefault("trial_number", 1)


def move_to(page: str) -> None:
    st.session_state.page = page
    st.rerun()


def render_progress() -> None:
    pages = {
        "consent": 0,
        "background": 1,
        "instruction": 2,
        "trial": 3,
        "completion": 4,
        "no_consent": 0,
        "not_engaging": 1,
        "failed_check": 2,
    }
    labels = ["Consent", "Background", "Instruction check", "10 trials", "Completion"]
    current = pages[st.session_state.page]
    st.progress(current / (len(labels) - 1))
    st.caption(" -> ".join(f"**{label}**" if i == current else label for i, label in enumerate(labels)))


def render_exit(title: str, text: str, completion_url: str, code: str) -> None:
    st.header(title)
    st.warning(text)
    st.write("Please return to Prolific using the completion URL below.")
    st.link_button("Return to Prolific", completion_url, type="primary")
    st.caption(f"If Prolific asks for a code instead, use: {code}")


def render_media(url: str, media_type: str, caption: str | None = None) -> None:
    """Render direct hosted media URLs in Streamlit."""
    if media_type == "video":
        st.video(url)
    else:
        st.image(url, caption=caption)


def render_trial(trial_number: int) -> None:
    try:
        trial = get_trial(trial_number)
    except RuntimeError as error:
        st.error(f"Study materials could not be loaded: {error}")
        st.stop()
    st.header(f"Trial #{trial_number} of {TRIAL_COUNT}")
    st.caption(f"Assigned participant slot: {PARTICIPANT_SLOT}")

    with st.container(border=True):
        st.subheader("RGB scene frame and target crop annotation")
        if trial["target_annotation_image_url"]:
            render_media(
                trial["target_annotation_image_url"],
                "image",
                "Left: original RGB scene frame. Right: target crop with human/object boxes.",
            )
        elif trial["scene_image_url"]:
            render_media(trial["scene_image_url"], "image", "Original RGB scene frame")
        else:
            st.warning("No RGB scene frame was supplied for this trial.")
        st.markdown("**Scene description**")
        st.write(trial["text_description"] or "No additional text description is provided for this trial.")

    with st.form(f"trial_form_{trial_number}", border=False):
        st.subheader("2.1. Scene understanding")
        clarity = st.radio(
            "How clearly can you understand what is happening in this scene, based on the RGB scene frame and the text description?",
            CLARITY_SCALE,
            index=None,
            horizontal=True,
            key=f"clarity_{trial_number}",
        )

        st.subheader("2.2. Need for a proactive response")
        proactive_need = st.radio(
            "For this event, should the robot take some kind of proactive response?",
            PROACTIVE_NEED_SCALE,
            index=None,
            horizontal=True,
            key=f"proactive_need_{trial_number}",
        )

        st.subheader("2.3. Situation assessment")
        st.write("Which of the following concerns or needs are present in this event and should influence the robot's decision? Select all that apply.")
        st.caption('If you select "No special concern is present" or "There is not enough information", please do not select any other option.')
        concerns = []
        for concern in SITUATION_CONCERNS:
            if st.checkbox(concern, key=f"concern_{trial_number}_{concern}"):
                concerns.append(concern)
        if st.checkbox(NO_SPECIAL_CONCERN, key=f"concern_none_{trial_number}"):
            concerns.append(NO_SPECIAL_CONCERN)
        if st.checkbox(NOT_ENOUGH_CONCERN_INFO, key=f"concern_uncertain_{trial_number}"):
            concerns.append(NOT_ENOUGH_CONCERN_INFO)
        if st.checkbox("Other (please specify)", key=f"concern_other_{trial_number}"):
            concerns.append("Other (please specify)")
        other_concern = st.text_input(
            'If you selected "Other (please specify)", please describe the other concern or need.',
            key=f"other_concern_{trial_number}",
        )

        st.subheader("2.4. Primary high-level response")
        primary_response = st.radio(
            "Given this event, which ONE high-level response should be the robot's primary response?",
            PRIMARY_RESPONSES + ["Other (please specify)"],
            index=None,
            key=f"primary_response_{trial_number}",
        )
        other_primary = st.text_input(
            'If you selected "Other (please specify)", please specify the other primary response.',
            key=f"other_primary_{trial_number}",
        )

        st.subheader("2.5a. Additional high-level responses")
        selected_primary_short = primary_label_to_short_label(primary_response)
        secondary_options = [
            option for option in SECONDARY_RESPONSES if option != selected_primary_short
        ]
        st.caption(
            'Please do not select the same response that you selected as the primary response. '
            'If you select "No additional response would be appropriate", please do not select any other option.'
        )
        secondary_responses = []
        for response in secondary_options:
            if st.checkbox(response, key=f"secondary_{trial_number}_{response}"):
                secondary_responses.append(response)
        if st.checkbox(
            NO_ADDITIONAL_RESPONSE,
            key=f"secondary_none_{trial_number}",
        ):
            secondary_responses.append(NO_ADDITIONAL_RESPONSE)
        if st.checkbox(
            "Other (please specify)",
            key=f"secondary_other_{trial_number}",
        ):
            secondary_responses.append("Other (please specify)")
        other_secondary = st.text_input(
            'If you selected "Other (please specify)", please specify the other additional response.',
            key=f"other_secondary_{trial_number}",
        )

        st.subheader("2.5b. Rationale")
        rationale = st.text_area(
            "Briefly explain the main reason for your selected primary response. You may also explain why another response could be reasonable.",
            key=f"rationale_{trial_number}",
        )

        st.subheader("2.6. Movement and interaction requirements")
        st.caption("How should the robot move or interact while carrying out its response in this event? Rate each option.")
        constraint_answers = {}
        for row_number, row in enumerate(CONSTRAINT_ROWS):
            constraint_answers[row] = st.radio(
                row,
                CONSTRAINT_SCALE,
                index=None,
                horizontal=True,
                key=f"constraint_{trial_number}_{row_number}",
            )

        st.subheader("2.7. Other movement or interaction requirements")
        other_constraints = st.text_area(
            "Are there any other movement or interaction requirements that are not listed above?",
            key=f"other_constraints_{trial_number}",
        )

        attribute_answers = {}
        has_vlm_attributes = any(
            trial[field]
            for field in ("vlm_input_image_url", "human_state", "object_property", "spatial_context", "risk_factor")
        )
        if has_vlm_attributes:
            st.divider()
            st.subheader(f"Trial #{trial_number} - VLM Attribute Review")
            if trial["vlm_input_image_url"]:
                render_media(trial["vlm_input_image_url"], "image", "Image provided to the vision-language model")
            st.caption("Below are the attributes predicted by the vision-language model.")

            st.subheader("2.8. Predicted attribute accuracy")
            st.caption("Based on the available visual evidence, how accurate is each predicted attribute?")
            attribute_rows = {
                f"Human state: {display_attribute(trial['human_state'])}": None,
                f"Object property: {display_attribute(trial['object_property'])}": None,
                f"Spatial context: {display_attribute(trial['spatial_context'])}": None,
                f"Risk factor(s): {display_attribute(trial['risk_factor'])}": None,
            }
            for row_number, row in enumerate(attribute_rows):
                attribute_answers[row] = st.radio(
                    row,
                    ATTRIBUTE_SCALE,
                    index=None,
                    horizontal=True,
                    key=f"attribute_{trial_number}_{row_number}",
                )

        previous, submit = st.columns([1, 2])
        with previous:
            go_back = st.form_submit_button("Previous trial", disabled=trial_number == 1)
        with submit:
            advance_label = "Finish study" if trial_number == TRIAL_COUNT else "Save and continue to next trial"
            go_forward = st.form_submit_button(advance_label, type="primary")

    if go_back:
        st.session_state.trial_number -= 1
        st.rerun()

    if go_forward:
        special_answers = {NO_SPECIAL_CONCERN, NOT_ENOUGH_CONCERN_INFO}
        concerns_are_valid = bool(concerns) and not (
            set(concerns) & special_answers and len(concerns) > 1
        )
        no_additional_is_valid = bool(secondary_responses) and not (
            NO_ADDITIONAL_RESPONSE in secondary_responses and len(secondary_responses) > 1
        )
        all_constraints_answered = all(value is not None for value in constraint_answers.values())
        all_attributes_answered = all(value is not None for value in attribute_answers.values())
        other_values_are_valid = (
            ("Other (please specify)" not in concerns or other_concern.strip())
            and (primary_response != "Other (please specify)" or other_primary.strip())
            and ("Other (please specify)" not in secondary_responses or other_secondary.strip())
        )
        if not PREVIEW_MODE and not all([clarity, proactive_need, concerns_are_valid, primary_response, no_additional_is_valid, all_constraints_answered, all_attributes_answered, other_values_are_valid]):
            st.error("Please answer every required question and resolve the mutually exclusive selections before continuing.")
        else:
            st.session_state[f"trial_{trial_number}_submitted"] = {
                "clarity": clarity,
                "proactive_need": proactive_need,
                "concerns": concerns,
                "primary_response": primary_response,
                "secondary_responses": secondary_responses,
                "rationale": rationale,
                "constraints": constraint_answers,
                "other_constraints": other_constraints,
                "attribute_accuracy": attribute_answers,
            }
            if trial_number == TRIAL_COUNT:
                move_to("completion")
            else:
                st.session_state.trial_number += 1
                st.rerun()


initialise_state()

prolific_pid = st.query_params.get("PROLIFIC_PID", "PREVIEW_PID")
study_id = st.query_params.get("STUDY_ID", "PREVIEW_STUDY")
session_id = st.query_params.get("SESSION_ID", "PREVIEW_SESSION")

st.title("Robot Proactive Task and Constraints")
st.caption(f"Assigned participant slot: {PARTICIPANT_SLOT}  |  Prolific PID: {prolific_pid}")
if PREVIEW_MODE:
    st.info(
        "Researcher preview mode is on: required-answer checks are disabled. "
        "Use the normal slot URL without `researcher_preview=1` for real participants."
    )
render_progress()

if st.session_state.page == "consent":
    st.header("Participant Information and Online Consent")
    st.caption(f"Assigned study slot: {PARTICIPANT_SLOT}")
    st.markdown("### Invitation")
    st.write(
        "You are invited to take part in a research study conducted at King's College London. "
        "Please read the information below carefully before deciding whether to participate. "
        "You may stop at any time before submitting the questionnaire."
    )
    st.markdown("### Purpose of the study")
    st.write(
        "This study examines how people interpret everyday human-robot interaction scenes and "
        "what proactive actions or navigation constraints they think a robot should follow. "
        "The results will help build a knowledge base for proactive robot task selection and socially aware navigation."
    )
    st.markdown("### Why you have been invited")
    st.write(
        "You are invited as an adult, English-fluent participant who can complete an online questionnaire involving RGB scene frames and written scene descriptions."
    )
    st.markdown("### What you will be asked to do")
    st.write(
        "You will review 10 RGB scene frames and read brief scene descriptions. "
        "Some scenes may also include a separate frame used by a vision-language model. "
        "The visual simulation may not always be fully realistic, so the text description is provided to help you understand the scene. "
        "For each scene, you will judge what is happening, what proactive response the robot should take, and what movement or interaction constraints are relevant."
    )
    st.write("The questionnaire is expected to take approximately 40 minutes.")
    st.markdown("### Voluntary participation, risks, and data use")
    st.write(
        "Participation is voluntary. You may choose not to take part or stop before submission without giving a reason. "
        "The study is considered minimum risk. Some scenes may involve possible risks or assistance needs in everyday environments, but no graphic or distressing content is intended."
    )
    st.write(
        "The questionnaire will not ask for your name, email address, signature, or other direct identifiers. "
        "Your Prolific ID is used only for participation management, payment, completion checking, and data-quality review. "
        "Responses are stored securely for academic research; publications, presentations, and thesis outputs will not identify you."
    )
    st.write(
        "After submission, responses may be combined with other pseudonymous or anonymised data, so withdrawal may no longer be possible."
    )
    st.markdown("### Questions or concerns")
    st.write(
        "Researcher: Li Xiangqi, King's College London, xiangqi.1.li@kcl.ac.uk  \\n"
        "Supervisor: Oya Celiktutan, King's College London, oya.celiktutan@kcl.ac.uk"
    )
    st.markdown("### Consent check")
    st.write("Please tick every statement to confirm your consent. Unticked statements mean that you do not consent to that element of the study.")
    consent_confirmations = []
    for statement_number, statement in enumerate(CONSENT_STATEMENTS):
        consent_confirmations.append(
            st.checkbox(statement, key=f"consent_statement_{statement_number}")
        )
    consent = st.radio(
        "Do you consent to participate in this study?",
        ["Yes, I consent and wish to continue.", "No, I do not consent."],
        index=None,
    )
    if st.button("Continue", type="primary"):
        if PREVIEW_MODE and consent is None:
            move_to("background")
        elif consent == "Yes, I consent and wish to continue.":
            if PREVIEW_MODE or all(consent_confirmations):
                move_to("background")
            else:
                st.error("Please tick every consent statement before continuing.")
        elif consent == "No, I do not consent.":
            move_to("no_consent")
        else:
            st.error("Please select Yes or No before continuing.")

elif st.session_state.page == "no_consent":
    render_exit(
        "You have chosen not to consent",
        "Thank you for considering this study. Because you did not consent, please do not continue with the survey.",
        NO_CONSENT_COMPLETION_URL,
        "C1FAF7FV",
    )

elif st.session_state.page == "background":
    st.header("Background Information")
    st.write(
        "In this study, you will review RGB scene frames from a robot-related everyday environment. Text descriptions clarify the scene, especially when the simulator rendering is not realistic enough to fully convey the human-object interaction, object properties, spatial context, or potential risks."
    )
    st.write(
        "For each scene, please judge what is happening and what the robot should do based only on the RGB scene frame, the VLM input image if provided for attribute review, and the text description. There are no right or wrong answers; some scenes may be ambiguous."
    )
    st.markdown(
        "**Main response types:** Continue (continue its original plan), Monitor (observe without intervening yet), Avoid (stay clear or avoid interfering), Assist (offer or perform help), and Warn (alert people about a possible problem or risk)."
    )
    attitude = st.radio(
        "Which statement best describes your attitude toward robots or autonomous technologies in everyday environments?",
        ATTITUDES,
        index=None,
    )
    if st.button("Continue", type="primary"):
        if PREVIEW_MODE and attitude is None:
            move_to("instruction")
        elif attitude is None:
            st.error("Please choose one statement before continuing.")
        elif attitude.startswith("E."):
            move_to("not_engaging")
        else:
            move_to("instruction")

elif st.session_state.page == "not_engaging":
    render_exit(
        "Study exit",
        "You indicated that you would prefer not to engage with this topic, so the survey will not continue.",
        FAILED_CHECK_COMPLETION_URL,
        "CI0WWZBS",
    )

elif st.session_state.page == "instruction":
    st.header("Survey Instructions Check")
    instruction_answer = st.radio(
        "In this study, what should you base your answers on?",
        [
            "Only the RGB scene frame, VLM input image if provided, and scene description.",
            "My prior assumptions about robots.",
            "Random guesses.",
            "What I think the researcher wants.",
        ],
        index=None,
        help="This question checks whether the task instructions are clear.",
    )
    if st.button("Continue", type="primary"):
        if PREVIEW_MODE and instruction_answer is None:
            move_to("trial")
        elif instruction_answer is None:
            st.error("Please select one answer before continuing.")
        elif instruction_answer.startswith("Only the RGB scene frame"):
            move_to("trial")
        else:
            move_to("failed_check")

elif st.session_state.page == "failed_check":
    render_exit(
        "The instruction check was not passed",
        "Based on your answer, it seems the task instructions may not have been understood.",
        FAILED_CHECK_COMPLETION_URL,
        "CI0WWZBS",
    )

elif st.session_state.page == "trial":
    render_trial(st.session_state.trial_number)

elif st.session_state.page == "completion":
    st.header("Thank you for completing the study")
    st.success("Your responses have been recorded for this prototype session.")
    st.write("Please return to Prolific using the completion URL below.")
    st.link_button("Return to Prolific", DEFAULT_COMPLETION_URL, type="primary")
    st.caption("If Prolific asks for a code instead, use: CD10CDO9")
    with st.expander("Prototype status"):
        st.json(
            {
                "participant_slot": PARTICIPANT_SLOT,
                "prolific_pid": prolific_pid,
                "study_id": study_id,
                "session_id": session_id,
                "storage": "Session-only. Add a private database before recruiting participants.",
            }
        )
