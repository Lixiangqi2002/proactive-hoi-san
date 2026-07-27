import streamlit as st

st.set_page_config(
    page_title="Robot Proactive Task and Constraints",
    page_icon="🤖",
    layout="wide",
)

# Public prototype only: no real OneDrive links, participant data, or secrets.
PARTICIPANT_SLOT = "P001"
COMPLETION_URL = "https://app.prolific.com/submissions/complete?cc=CD10CD09"

ATTITUDES = [
    "A. I am very interested in them and generally positive.",
    "B. I am somewhat interested or open-minded.",
    "C. I am neutral.",
    "D. I strongly dislike them and would prefer not to engage with this topic.",
]
CLARITY = [
    "Not clear at all", "Mostly unclear", "Partly clear, but uncertain",
    "Mostly clear", "Completely clear",
]
NEED = [
    "Definitely not needed", "Probably not needed",
    "Unsure / depends on other information", "Probably needed",
    "Definitely needed",
]
LIKERT = [
    "Strongly disagree", "Disagree", "Neither agree nor disagree",
    "Agree", "Strongly agree",
]
TASKS = [
    "Continue: continue its original plan without a special response.",
    "Monitor: keep observing, but do not intervene yet.",
    "Avoid: adjust movement to stay away from the event or avoid interfering.",
    "Assist: actively offer or perform help.",
    "Warn: alert relevant people about a possible problem or risk.",
]
CONSTRAINTS = [
    "Preserve access between the grounded human and object.",
    "Preserve the human path corridor.",
    "Preserve a connected corridor candidate.",
    "Avoid danger region around the danger source.",
    "Avoid close/rear region of the grounded human.",
    "Expand human safety zone around the grounded human.",
    "Expand safety margin around dangerous object.",
    "Low-speed approach near robot/event approach area.",
    "Keep event visible.",
    "Communication/action anchor for assistance.",
    "Communication/action anchor for warning.",
    "Communication/action anchor for nearby people.",
]

if "phase" not in st.session_state:
    st.session_state.phase = 0
if "trial" not in st.session_state:
    st.session_state.trial = 1

pid = st.query_params.get("PROLIFIC_PID", "PREVIEW_PID")
study = st.query_params.get("STUDY_ID", "PREVIEW_STUDY")
session = st.query_params.get("SESSION_ID", "PREVIEW_SESSION")

st.title("Robot Proactive Task and Constraints")
st.caption(f"P001 prototype · Prolific PID: {pid}")

steps = ["Consent", "Background", "Instruction check", "10 trials", "Completion"]
st.progress(st.session_state.phase / 4)
st.caption(" → ".join(f"**{x}**" if i == st.session_state.phase else x for i, x in enumerate(steps)))

if st.session_state.phase == 0:
    st.header("Participant information and consent")
    st.write(
        "In this study, you will watch short scenes from a robot's point of "
        "view and, when provided, a simple top-down view. A text description "
        "is provided when the simulated visual scene alone may not make the "
        "situation sufficiently clear. For each scene, please judge what is "
        "happening and what the robot should do."
    )
    st.info("Prototype: the approved study-information and consent documents will be linked here.")
    consent = st.checkbox("I have read the study information and consent to participate.")
    if st.button("Continue", disabled=not consent, type="primary"):
        st.session_state.phase = 1
        st.rerun()

elif st.session_state.phase == 1:
    st.header("Background information")
    attitude = st.radio(
        "Which statement best describes your attitude toward robots or autonomous technologies in everyday environments?",
        ATTITUDES,
    )
    if st.button("Continue", type="primary"):
        st.session_state.phase = 4 if attitude.startswith("D.") else 2
        st.session_state.early_exit = attitude.startswith("D.")
        st.rerun()

elif st.session_state.phase == 2:
    st.header("Survey instructions check")
    st.write("Base each judgement only on the trial video, optional top-down view, and scene description.")
    answer = st.radio(
        "What information should you use to answer the trial questions?",
        [
            "Only the video, top-down view if provided, and scene description.",
            "My assumptions about what the robot probably knows.",
            "Information from other trials.",
            "Any information I can find online.",
        ],
    )
    if st.button("Start Trial 1", type="primary"):
        st.session_state.instruction_passed = answer.startswith("Only the video")
        st.session_state.phase = 3
        st.rerun()

elif st.session_state.phase == 3:
    trial = st.session_state.trial
    st.header(f"Trial #{trial} of 10")
    st.caption(f"Assigned participant slot: {PARTICIPANT_SLOT} · Trial order: {trial}")

    if not st.session_state.get("instruction_passed", False):
        st.error("Instruction check not passed. The final study will show the Prolific failed-check completion path.")
        if st.button("Continue to exit"):
            st.session_state.early_exit = True
            st.session_state.phase = 4
            st.rerun()
        st.stop()

    with st.container(border=True):
        st.subheader("Video and scene description")
        st.info(
            "Secure P001 video placeholder. In the production app, this panel "
            "will retrieve the matching OneDrive video and text description from "
            "a private assignment database."
        )
        st.text_area(
            "Scene description",
            value=f"P001 · Trial {trial}: description will load from the assignment record.",
            disabled=True,
            key=f"description_{trial}",
        )

    st.subheader("1. Scene understanding")
    st.radio("How clearly can you understand what is happening in this scene?", CLARITY, horizontal=True, key=f"clarity_{trial}")

    st.subheader("2. Need for proactive response")
    st.radio("For this event, should the robot take some kind of proactive response?", NEED, horizontal=True, key=f"need_{trial}")

    st.subheader("3. Information important to the robot")
    st.multiselect(
        "Select all that apply.",
        ["Human-object interaction", "Crowding or congestion", "Possible risk", "Access or route need", "Human difficulty or assistance need", "Supervision or monitoring need", "Unclear"],
        key=f"information_{trial}",
    )

    st.subheader("4. Recommended proactive task")
    st.caption("How much do you agree that each action is appropriate?")
    for number, task in enumerate(TASKS):
        st.radio(task, LIKERT, horizontal=True, key=f"task_{trial}_{number}")
    st.text_area("5. Are there other possible proactive tasks? Please briefly explain.", key=f"other_task_{trial}")

    st.subheader("6. Movement or interaction constraints")
    for number, constraint in enumerate(CONSTRAINTS):
        st.selectbox(constraint, ["Required", "Helpful but not required", "Not relevant"], key=f"constraint_{trial}_{number}")
    st.text_area("7. Are there other possible constraints for robot movement or interaction?", key=f"other_constraint_{trial}")

    left, right = st.columns(2)
    with left:
        if trial > 1 and st.button("Previous trial"):
            st.session_state.trial -= 1
            st.rerun()
    with right:
        if trial < 10:
            if st.button("Save and continue to next trial", type="primary"):
                st.session_state.trial += 1
                st.rerun()
        elif st.button("Submit prototype responses", type="primary"):
            st.session_state.early_exit = False
            st.session_state.phase = 4
            st.rerun()

else:
    if st.session_state.get("early_exit", False):
        st.header("Study exit")
        st.warning("Prototype early-exit route. The final version will use the correct Prolific completion URL.")
    else:
        st.header("Thank you for completing the study")
        st.success("Prototype complete. The production app will persist responses before showing the completion link.")
    st.link_button("Return to Prolific", COMPLETION_URL, type="primary")
    with st.expander("Prototype technical details"):
        st.json({"participant_slot": PARTICIPANT_SLOT, "prolific_pid": pid, "study_id": study, "session_id": session, "storage": "Session-only; Supabase comes next."})
