"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

import { FormEvent, useCallback, useEffect, useState } from "react";

import { createPromptConfig, getActivePromptConfig, listPromptConfigs } from "@/services/admin";
import { ApiError } from "@/services/api";
import type { PromptConfig } from "@/types/api";

import { FieldError, StateBlock } from "./state-block";

interface AdminPromptConfigPanelProps {
  token: string;
  onNotice: (value: string) => void;
}

function errorText(error: unknown): string {
  if (error instanceof ApiError) return error.message;

  return error instanceof Error ? error.message : "Không thể cập nhật cấu hình hệ thống.";
}

export function AdminPromptConfigPanel({ token, onNotice }: AdminPromptConfigPanelProps) {
  const [activePrompt, setActivePrompt] = useState<PromptConfig | null>(null);
  const [history, setHistory] = useState<PromptConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadPromptData = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [active, configs] = await Promise.all([getActivePromptConfig(token), listPromptConfigs(token)]);

      setActivePrompt(active);
      setHistory(configs.data);
    } catch (requestError) {
      setError(errorText(requestError));
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    queueMicrotask(() => void loadPromptData());
  }, [loadPromptData]);

  const form = usePromptForm({
    token,
    onChanged: loadPromptData,
    onNotice,
    onError: setError,
  });

  return (
    <section className="panel">
      <PromptPanelHeader activePrompt={activePrompt} />
      <StateBlock loading={loading} error={error} />
      <ActivePromptSummary activePrompt={activePrompt} />
      <PromptForm form={form} />
      <PromptHistory history={history} />
    </section>
  );
}

function PromptPanelHeader({ activePrompt }: { activePrompt: PromptConfig | null }) {
  return (
    <div className="panel-heading">
      <div>
        <div className="eyebrow">NC-09 · UC03</div>
        <h3>Prompt / Model Config</h3>
      </div>

      {activePrompt ? <span className="status-badge">Active v{activePrompt.versionNumber}</span> : null}
    </div>
  );
}

function ActivePromptSummary({ activePrompt }: { activePrompt: PromptConfig | null }) {
  if (!activePrompt) {
    return null;
  }

  return (
    <div className="help-box">
      <strong>{activePrompt.name}</strong>
      <p>
        {activePrompt.modelName} · schema {activePrompt.schemaVersion}
      </p>
    </div>
  );
}

interface PromptFormProps {
  token: string;
  onChanged: () => Promise<void>;
  onNotice: (value: string) => void;
  onError: (value: string) => void;
}

function getPromptErrors(name: string, systemPrompt: string, template: string) {
  return {
    name: name.trim().length < 2 ? "Tên cấu hình phải có ít nhất 2 ký tự." : "",
    system: systemPrompt.trim().length < 20 ? "System Prompt phải có ít nhất 20 ký tự." : "",
    template:
      !template.includes("{requirement_text}") || !template.includes("{acceptance_criteria}")
        ? "Template phải có {requirement_text} và {acceptance_criteria}."
        : "",
  };
}

function usePromptFields() {
  const [name, setName] = useState("Week 07 Prompt");

  const [systemPrompt, setSystemPrompt] = useState(
    "You are a QA assistant. Generate structured test cases from requirements.",
  );

  const [template, setTemplate] = useState(
    "Requirement:\n{requirement_text}\nAcceptance Criteria:\n{acceptance_criteria}",
  );

  const [model, setModel] = useState("gpt-5");
  const [schema, setSchema] = useState("v1");

  const errors = getPromptErrors(name, systemPrompt, template);

  return {
    name,
    systemPrompt,
    template,
    model,
    schema,
    errors,
    setName,
    setSystemPrompt,
    setTemplate,
    setModel,
    setSchema,
  };
}

type PromptFieldsState = ReturnType<typeof usePromptFields>;

function usePromptSubmit(props: PromptFormProps, fields: PromptFieldsState) {
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (fields.errors.name || fields.errors.system || fields.errors.template) {
      return;
    }

    setBusy(true);
    props.onError("");

    try {
      await createPromptConfig(props.token, {
        name: fields.name,
        systemPrompt: fields.systemPrompt,
        userPromptTemplate: fields.template,
        modelName: fields.model,
        schemaVersion: fields.schema,
        maxOutputTokens: 4000,
      });

      props.onNotice("Đã tạo prompt/model version mới; active version cũ được giữ trong history.");

      await props.onChanged();
    } catch (requestError) {
      props.onError(errorText(requestError));
    } finally {
      setBusy(false);
    }
  }

  return {
    busy,
    submit,
  };
}

function usePromptForm(props: PromptFormProps) {
  const fields = usePromptFields();
  const submission = usePromptSubmit(props, fields);

  return {
    ...fields,
    ...submission,
  };
}

type PromptFormState = ReturnType<typeof usePromptForm>;

function PromptForm({ form }: { form: PromptFormState }) {
  const disabled = form.busy || Boolean(form.errors.name || form.errors.system || form.errors.template);

  return (
    <form className="stack-form" onSubmit={form.submit}>
      <PromptNameField form={form} />
      <PromptSystemField form={form} />
      <PromptTemplateField form={form} />
      <PromptModelFields form={form} />

      <button className="primary-button" disabled={disabled} type="submit">
        {form.busy ? "Đang tạo..." : "Tạo version mới"}
      </button>
    </form>
  );
}

function PromptNameField({ form }: { form: PromptFormState }) {
  return (
    <label>
      Name
      <input value={form.name} onChange={(event) => form.setName(event.target.value)} minLength={2} required />
      <FieldError message={form.errors.name} />
    </label>
  );
}

function PromptSystemField({ form }: { form: PromptFormState }) {
  return (
    <label>
      System Prompt
      <textarea
        value={form.systemPrompt}
        onChange={(event) => form.setSystemPrompt(event.target.value)}
        rows={4}
        minLength={20}
        required
      />
      <FieldError message={form.errors.system} />
    </label>
  );
}

function PromptTemplateField({ form }: { form: PromptFormState }) {
  return (
    <label>
      User Prompt Template
      <textarea
        value={form.template}
        onChange={(event) => form.setTemplate(event.target.value)}
        rows={6}
        minLength={20}
        required
      />
      <FieldError message={form.errors.template} />
    </label>
  );
}

function PromptModelFields({ form }: { form: PromptFormState }) {
  return (
    <div className="form-grid">
      <label>
        Model
        <input value={form.model} onChange={(event) => form.setModel(event.target.value)} required />
      </label>

      <label>
        Schema
        <input value={form.schema} onChange={(event) => form.setSchema(event.target.value)} required />
      </label>
    </div>
  );
}

function PromptHistory({ history }: { history: PromptConfig[] }) {
  if (history.length === 0) {
    return <StateBlock empty emptyText="Chưa có prompt history." />;
  }

  return (
    <div className="version-list">
      {history.map((config) => (
        <div className="version-row" key={config.id}>
          <span>
            v{config.versionNumber} · {config.name}
          </span>

          <strong>{config.isActive ? "active" : "history"}</strong>
        </div>
      ))}
    </div>
  );
}
