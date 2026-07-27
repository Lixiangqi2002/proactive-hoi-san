import streamlit as st


st.set_page_config(
    page_title="Robot Proactive Task and Constraints",
    page_icon="🤖",
    layout="wide",
)

# This public repository intentionally contains no real participant assignments,
# OneDrive links, or VLM attributes. Those belong in private Streamlit secrets or
# a private database before the study is launched.
PARTICIPANT_SLOT = "P001"
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
    "Continue — Continue its original plan without any special response.",
    "Monitor — Continue observing the event before deciding whether intervention is needed.",
    "Avoid — Adjust its movement to stay clear of the event and avoid interfering.",
    "Assist — Offer or provide help to the relevant person.",
    "Warn — Alert the relevant person or people about a possible problem or risk.",
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


def get_trial(trial_number: int) -> dict:
    """Safe public placeholder for the private P001 assignment record."""
    return {
        "video_url": None,
        "text_description": None,
        "image_url": None,
        "human_state": None,
        "object_property": None,
        "spatial_context": None,
        "risk_factor": None,
    }


def display_attribute(value: str | None) -> str:
    return value if value else "[Will load from the secure assignment record]"


def primary_label_to_short_label(value: str | None) -> str | None:
    if not value:
        return None
    for label in SECONDARY_RESPONSES:
        if value.startswith(label + " —"):
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
    st.caption(" → ".join(f"**{label}**" if i == current else label for i, label in enumerate(labels)))


def render_exit(title: str, text: str, completion_url: str, code: str) -> None:
    st.header(title)
    st.warning(text)
    st.write("Please return to Prolific using the completion URL below.")
    st.link_button("Return to Prolific", completion_url, type="primary")
    st.caption(f"If Prolific asks for a code instead, use: {code}")


def render_trial(trial_number: int) -> None:
    trial = get_trial(trial_number)
    st.header(f"Trial #{trial_number} of {TRIAL_COUNT}")
    st.caption(f"Assigned participant slot: {PARTICIPANT_SLOT}")

    with st.container(border=True):
        st.subheader("Video and scene description")
        if trial["video_url"]:
            st.video(trial["video_url"])
        else:
            st.info("The assigned video will load here from the secure participant-assignment record.")
        st.markdown("**Scene description**")
        st.write(trial["text_description"] or "No additional text description is provided for this trial.")

    with st.form(f"trial_form_{trial_number}", border=False):
        st.subheader("2.1. Scene understanding")
        clarity = st.radio(
            "How clearly can you understand what is happening in this scene, based on the video and the text description?",
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

        st.divider()
        st.subheader(f"Trial #{trial_number} – VLM Attribute Review")
        if trial["image_url"]:
            st.image(trial["image_url"], caption="Event image provided to the vision-language model")
        else:
            st.caption("No separate event image link is provided; answer based on the available video and text description.")
        st.caption("Below are the attributes predicted by the vision-language model.")

        st.subheader("2.8. Predicted attribute accuracy")
        st.caption("Based on the available visual evidence, how accurate is each predicted attribute?")
        attribute_rows = {
            f"Human state: {display_attribute(trial['human_state'])}": None,
            f"Object property: {display_attribute(trial['object_property'])}": None,
            f"Spatial context: {display_attribute(trial['spatial_context'])}": None,
            f"Risk factor(s): {display_attribute(trial['risk_factor'])}": None,
        }
        attribute_answers = {}
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
        if not all([clarity, proactive_need, concerns_are_valid, primary_response, no_additional_is_valid, all_constraints_answered, all_attributes_answered, other_values_are_valid]):
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
render_progress()

if st.session_state.page == "consent":
    st.header("Participant Information and Consent Check")
    st.radio("Assigned participant ID", [PARTICIPANT_SLOT], index=0, disabled=True)
    consent = st.radio(
        "Do you consent to participate in this study?",
        ["Yes, I consent to participate in this study.", "No, I do not consent."],
        index=None,
        help=(
            "Please read the study information sheet and consent form before continuing. By selecting Yes, you confirm that you have read and understood the study information, voluntarily agree to participate, understand that you may stop at any time, and agree that your survey responses will be stored securely and used only for research purposes."
        ),
    )
    if st.button("Continue", type="primary"):
        if consent == "Yes, I consent to participate in this study.":
            move_to("background")
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
        "In this study, you will watch short scenes from a robot's point of view and, when provided, a simple top-down view. Text descriptions clarify the scene, especially when the simulator rendering is not realistic enough to fully convey the human-object interaction, object properties, spatial context, or potential risks."
    )
    st.write(
        "For each scene, please judge what is happening and what the robot should do based only on the video, the top-down view if provided, and the text description. There are no right or wrong answers; some scenes may be ambiguous."
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
        if attitude is None:
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
            "Only the video, top-down view if provided, and scene description.",
            "My prior assumptions about robots.",
            "Random guesses.",
            "What I think the researcher wants.",
        ],
        index=None,
        help="This question checks whether the task instructions are clear.",
    )
    if st.button("Continue", type="primary"):
        if instruction_answer is None:
            st.error("Please select one answer before continuing.")
        elif instruction_answer.startswith("Only the video"):
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
