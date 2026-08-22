"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).
import { useEffect, useState } from "react";

import { ApiError } from "@/services/api";
import { transitionTestCase, updateTestCase } from "@/services/testcases";
import type { Priority, TestCaseRecord, User } from "@/types/api";
import { FieldError, StateBlock } from "./state-block";

interface TestCaseEditorProps {
  token: string;
  user: User;
  record: TestCaseRecord | null;
  onChanged: (record: TestCaseRecord) => void;
}

function message(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return error instanceof Error ? error.message : "Không thể cập nhật test case.";
}

function splitLines(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

interface EditorState {
  summary: string;
  steps: string;
  expected: string;
  priority: Priority;
  note: string;
  setSummary: (value: string) => void;
  setSteps: (value: string) => void;
  setExpected: (value: string) => void;
  setPriority: (value: Priority) => void;
  setNote: (value: string) => void;
}

function useEditorState(record: TestCaseRecord | null): EditorState {
  const [summary, setSummary] = useState("");
  const [steps, setSteps] = useState("");
  const [expected, setExpected] = useState("");
  const [priority, setPriority] = useState<Priority>("medium");
  const [note, setNote] = useState("");
  useEffect(() => {
    if (!record) return;
    queueMicrotask(() => {
      setSummary(record.summary);
      setSteps(record.steps.join("\n"));
      setExpected(record.expected_result);
      setPriority(record.priority);
      setNote(record.review_note ?? "");
    });
  }, [record]);
  return { summary, steps, expected, priority, note, setSummary, setSteps, setExpected, setPriority, setNote };
}

export function TestCaseEditor({ token, user, record, onChanged }: TestCaseEditorProps) {
  const editor = useEditorState(record);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const currentRecord = record;
  if (!currentRecord)
    return (
      <section className="panel">
        <StateBlock empty emptyText="Chọn một test case để review." />
      </section>
    );
  const activeRecord: TestCaseRecord = currentRecord;
  const errors = getEditorErrors(editor);
  const formInvalid = Object.values(errors).some(Boolean);
  async function run(action: () => Promise<TestCaseRecord>, successText: string) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const updated = await action();
      onChanged(updated);
      setNotice(successText);
    } catch (requestError) {
      setError(message(requestError));
    } finally {
      setBusy(false);
    }
  }
  async function save() {
    await run(
      () =>
        updateTestCase(token, activeRecord, {
          summary: editor.summary,
          steps: splitLines(editor.steps),
          expectedResult: editor.expected,
          priority: editor.priority,
          reviewNote: editor.note,
        }),
      "Đã lưu phiên bản chỉnh sửa.",
    );
  }
  async function transition(action: "review" | "approve" | "request-fix" | "reject") {
    await run(() => transitionTestCase(token, activeRecord, action, editor.note), `Đã chuyển trạng thái: ${action}.`);
  }
  return (
    <section className="panel editor-panel">
      <EditorHeader record={activeRecord} />
      <EditorFields editor={editor} errors={errors} />
      <EditorActions user={user} busy={busy} invalid={formInvalid} onSave={save} onTransition={transition} />
      {error ? <div className="state state-error">{error}</div> : null}
      {notice ? <div className="state state-success">{notice}</div> : null}
    </section>
  );
}

function getEditorErrors(editor: EditorState) {
  return {
    summary: editor.summary.trim().length < 3 ? "Summary phải có ít nhất 3 ký tự." : "",
    steps: splitLines(editor.steps).length === 0 ? "Cần ít nhất một bước thực hiện." : "",
    expected: editor.expected.trim().length < 3 ? "Expected Result phải có ít nhất 3 ký tự." : "",
  };
}

function EditorHeader({ record }: { record: TestCaseRecord }) {
  return (
    <div className="panel-heading">
      <div>
        <div className="eyebrow">Human-in-the-loop</div>
        <h3>TC #{record.id}</h3>
      </div>
      <span className={`status-badge status-${record.status}`}>
        {record.status} · v{record.lock_version}
      </span>
    </div>
  );
}

function EditorFields({ editor, errors }: { editor: EditorState; errors: ReturnType<typeof getEditorErrors> }) {
  return (
    <div className="form-grid">
      <label className="wide-field">
        Summary
        <input
          value={editor.summary}
          onChange={(event) => editor.setSummary(event.target.value)}
          minLength={3}
          maxLength={300}
        />
        <FieldError message={errors.summary} />
      </label>
      <label>
        Priority
        <select value={editor.priority} onChange={(event) => editor.setPriority(event.target.value as Priority)}>
          <option value="high">high</option>
          <option value="medium">medium</option>
          <option value="low">low</option>
        </select>
      </label>
      <label className="wide-field">
        Steps
        <textarea rows={7} value={editor.steps} onChange={(event) => editor.setSteps(event.target.value)} />
        <FieldError message={errors.steps} />
      </label>
      <label className="wide-field">
        Expected Result
        <textarea rows={4} value={editor.expected} onChange={(event) => editor.setExpected(event.target.value)} />
        <FieldError message={errors.expected} />
      </label>
      <label className="wide-field">
        Review Note
        <textarea rows={3} value={editor.note} onChange={(event) => editor.setNote(event.target.value)} />
      </label>
    </div>
  );
}

interface ActionProps {
  user: User;
  busy: boolean;
  invalid: boolean;
  onSave: () => Promise<void>;
  onTransition: (action: "review" | "approve" | "request-fix" | "reject") => Promise<void>;
}
function EditorActions({ user, busy, invalid, onSave, onTransition }: ActionProps) {
  const canReview = user.role === "qa" || user.role === "manager";
  return (
    <div className="button-row wrap-row">
      <button
        className="secondary-button"
        disabled={busy || !canReview || invalid}
        onClick={() => void onSave()}
        type="button"
      >
        Lưu chỉnh sửa
      </button>
      <button
        className="primary-button"
        disabled={busy || !canReview}
        onClick={() => void onTransition("review")}
        type="button"
      >
        Submit Review
      </button>
      <button
        className="primary-button"
        disabled={busy || !canReview}
        onClick={() => void onTransition("approve")}
        type="button"
      >
        Approve
      </button>
      <button
        className="warning-button"
        disabled={busy || !canReview}
        onClick={() => void onTransition("request-fix")}
        type="button"
      >
        Request Fix
      </button>
      <button
        className="danger-button"
        disabled={busy || !canReview}
        onClick={() => void onTransition("reject")}
        type="button"
      >
        Reject
      </button>
    </div>
  );
}
