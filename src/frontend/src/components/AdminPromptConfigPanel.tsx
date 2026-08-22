"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

import { FormEvent, useCallback, useEffect, useState } from "react";

import { createPromptConfig, getActivePromptConfig, listPromptConfigs } from "@/services/admin";
import { ApiError } from "@/services/api";
import type { PromptConfig } from "@/types/api";

import { FieldError, StateBlock } from "./StateBlock";

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
      <div className="panel-heading">
        <div>
          <div className="eyebrow">NC-09 · UC03</div>
          <h3>Prompt / Model Config</h3>
        </div>

        {activePrompt ? <span className="status-badge">Active v{activePrompt.versionNumber}</span> : null}
      </div>

      <StateBlock loading={loading} error={error} />

      {activePrompt ? (
        <div className="help-box">
          <strong>{activePrompt.name}</strong>
          <p>
            {activePrompt.modelName} · schema {activePrompt.schemaVersion}
          </p>
        </div>
      ) : null}

      <PromptForm form={form} />

      <PromptHistory history={history} />
    </section>
  );
}

interface PromptFormProps {
  token: string;
  onChanged: () => Promise<void>;
  onNotice: (value: string) => void;
  onError: (value: string) => void;
}

function usePromptForm(props: PromptFormProps) {
  const [name, setName] = useState("Week 07 Prompt");

  const [systemPrompt, setSystemPrompt] = useState(
    "You are a QA assistant. Generate structured test cases from requirements.",
  );

  const [template, setTemplate] = useState(
    "Requirement:\n{requirement_text}\nAcceptance Criteria:\n{acceptance_criteria}",
  );

  const [model, setModel] = useState("gpt-5");
  const [schema, setSchema] = useState("v1");
  const [busy, setBusy] = useState(false);

  const errors = {
    name: name.trim().length < 2 ? "Tên cấu hình phải có ít nhất 2 ký tự." : "",
    system: systemPrompt.trim().length < 20 ? "System Prompt phải có ít nhất 20 ký tự." : "",
    template:
      !template.includes("{requirement_text}") || !template.includes("{acceptance_criteria}")
        ? "Template phải có {requirement_text} và {acceptance_criteria}."
        : "",
  };

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (errors.name || errors.system || errors.template) {
      return;
    }

    setBusy(true);
    props.onError("");

    try {
      await createPromptConfig(props.token, {
        name,
        systemPrompt,
        userPromptTemplate: template,
        modelName: model,
        schemaVersion: schema,
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
    name,
    systemPrompt,
    template,
    model,
    schema,
    busy,
    errors,
    setName,
    setSystemPrompt,
    setTemplate,
    setModel,
    setSchema,
    submit,
  };
}

type PromptFormState = ReturnType<typeof usePromptForm>;

function PromptForm({ form }: { form: PromptFormState }) {
  return (
    <form className="stack-form" onSubmit={form.submit}>
      <label>
        Name
        <input value={form.name} onChange={(event) => form.setName(event.target.value)} minLength={2} required />
        <FieldError message={form.errors.name} />
      </label>

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

      <button
        className="primary-button"
        disabled={form.busy || Boolean(form.errors.name || form.errors.system || form.errors.template)}
        type="submit"
      >
        {form.busy ? "Đang tạo..." : "Tạo version mới"}
      </button>
    </form>
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
