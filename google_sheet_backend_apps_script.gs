/**
 * Google Sheet response backend for the Streamlit HOI-SAN user study.
 *
 * Setup:
 * 1. Create a private Google Sheet for responses.
 * 2. Open Extensions -> Apps Script.
 * 3. Paste this file into Code.gs.
 * 4. Deploy -> New deployment -> Web app.
 *    - Execute as: Me
 *    - Who has access: Anyone
 * 5. Copy the Web App URL into Streamlit secrets as:
 *    GOOGLE_SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/.../exec"
 *
 * The Web App URL is a secret write endpoint. Do not publish it in GitHub.
 */

const RESPONSE_SHEET_NAME = "responses_long";

const HEADERS = [
  "submission_id",
  "submitted_at_utc",
  "saved_at_utc",
  "participant_slot",
  "prolific_pid",
  "study_id",
  "session_id",
  "preview_mode",
  "robot_attitude",
  "instruction_check_answer",
  "hf_media_revision",
  "trial_number",
  "trial_id",
  "trial_order",
  "repeat_index_for_video",
  "clip_team_id",
  "clip_number",
  "source",
  "scene_sequence",
  "camera_id",
  "interactive_obj",
  "interaction_type",
  "selected_frame_index",
  "scene_image_path",
  "target_annotation_image_path",
  "vlm_input_image_path",
  "pred_interaction",
  "human_state",
  "object_property",
  "spatial_context",
  "risk_factor",
  "clarity",
  "proactive_need",
  "concerns_json",
  "other_concern",
  "primary_response",
  "other_primary",
  "secondary_responses_json",
  "other_secondary",
  "rationale",
  "constraints_json",
  "other_constraints",
  "attribute_accuracy_json",
  "payload_json"
];

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    const payload = JSON.parse(e.postData.contents || "{}");
    const result = savePayload_(payload);
    return jsonResponse_(result);
  } catch (error) {
    return jsonResponse_({ ok: false, error: String(error) });
  } finally {
    lock.releaseLock();
  }
}

function doGet() {
  return jsonResponse_({
    ok: true,
    message: "HOI-SAN response backend is running. Use POST from Streamlit to save responses."
  });
}

function savePayload_(payload) {
  const sheet = getOrCreateResponseSheet_();
  ensureHeaders_(sheet);

  const submittedAt = value_(payload.submitted_at_utc);
  const savedAt = new Date().toISOString();
  const participantSlot = value_(payload.participant_slot);
  const prolificPid = value_(payload.prolific_pid);
  const sessionId = value_(payload.session_id);
  const submissionId = [
    participantSlot || "NO_SLOT",
    prolificPid || "NO_PROLIFIC_PID",
    sessionId || "NO_SESSION"
  ].join("__");

  deleteExistingSubmissionRows_(sheet, submissionId);

  const trials = Array.isArray(payload.trials) ? payload.trials : [];
  const rows = trials.map((trial) => {
    const assignment = trial.assignment || {};
    const media = trial.media || {};
    const predictions = trial.vlm_predictions || {};
    const answers = trial.answers || {};
    return [
      submissionId,
      submittedAt,
      savedAt,
      participantSlot,
      prolificPid,
      value_(payload.study_id),
      sessionId,
      String(Boolean(payload.preview_mode)),
      value_(payload.robot_attitude),
      value_(payload.instruction_check_answer),
      value_(payload.hf_media_revision),
      value_(trial.trial_number),
      value_(assignment.trial_id),
      value_(assignment.trial_order),
      value_(assignment.repeat_index_for_video),
      value_(assignment.clip_team_id),
      value_(assignment.clip_number),
      value_(assignment.source),
      value_(assignment.scene_sequence),
      value_(assignment.camera_id),
      value_(assignment.interactive_obj),
      value_(assignment.interaction_type),
      value_(assignment.selected_frame_index),
      value_(media.scene_image_path),
      value_(media.target_annotation_image_path),
      value_(media.vlm_input_image_path),
      value_(predictions.pred_interaction),
      value_(predictions.human_state),
      value_(predictions.object_property),
      value_(predictions.spatial_context),
      value_(predictions.risk_factor),
      value_(answers.clarity),
      value_(answers.proactive_need),
      JSON.stringify(answers.concerns || []),
      value_(answers.other_concern),
      value_(answers.primary_response),
      value_(answers.other_primary),
      JSON.stringify(answers.secondary_responses || []),
      value_(answers.other_secondary),
      value_(answers.rationale),
      JSON.stringify(answers.constraints || {}),
      value_(answers.other_constraints),
      JSON.stringify(answers.attribute_accuracy || {}),
      JSON.stringify(payload)
    ];
  });

  if (rows.length > 0) {
    sheet.getRange(sheet.getLastRow() + 1, 1, rows.length, HEADERS.length).setValues(rows);
  }

  return {
    ok: true,
    submission_id: submissionId,
    participant_slot: participantSlot,
    rows_saved: rows.length
  };
}

function getOrCreateResponseSheet_() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  return spreadsheet.getSheetByName(RESPONSE_SHEET_NAME) || spreadsheet.insertSheet(RESPONSE_SHEET_NAME);
}

function ensureHeaders_(sheet) {
  const existing = sheet.getRange(1, 1, 1, HEADERS.length).getValues()[0];
  const needsHeaders = existing.every((cell) => cell === "");
  if (needsHeaders) {
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
    sheet.setFrozenRows(1);
  }
}

function deleteExistingSubmissionRows_(sheet, submissionId) {
  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return;
  const ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues().map((row) => row[0]);
  for (let index = ids.length - 1; index >= 0; index--) {
    if (ids[index] === submissionId) {
      sheet.deleteRow(index + 2);
    }
  }
}

function value_(value) {
  if (value === null || value === undefined) return "";
  return String(value);
}

function jsonResponse_(object) {
  return ContentService
    .createTextOutput(JSON.stringify(object))
    .setMimeType(ContentService.MimeType.JSON);
}
