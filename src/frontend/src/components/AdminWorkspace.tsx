"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).
import { FormEvent, useCallback, useEffect, useState } from "react";

import {
  createPromptConfig,
  createUser,
  getActivePromptConfig,
  listPromptConfigs,
  listUsers,
  updateUser,
} from "@/services/admin";
import { ApiError } from "@/services/api";
import type { PromptConfig, User, UserRole } from "@/types/api";
import { FieldError, StateBlock } from "./StateBlock";

interface AdminWorkspaceProps {
  token: string;
  user: User;
}

function errorText(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return error instanceof Error ? error.message : "Không thể cập nhật cấu hình hệ thống.";
}

export function AdminWorkspace({ token, user }: AdminWorkspaceProps) {
  const [activePrompt, setActivePrompt] = useState<PromptConfig | null>(null);
  const [history, setHistory] = useState<PromptConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

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
    if (user.role !== "admin") return;
    queueMicrotask(() => void loadPromptData());
  }, [loadPromptData, user.role]);
  if (user.role !== "admin") return <StateBlock empty emptyText="Chỉ Admin được truy cập cấu hình hệ thống." />;
  return (
    <div className="admin-layout">
      <PromptConfigPanel
        token={token}
        active={activePrompt}
        history={history}
        loading={loading}
        error={error}
        onChanged={loadPromptData}
        onNotice={setNotice}
        onError={setError}
      />
      <UserManagementPanel token={token} onNotice={setNotice} onError={setError} />
      {notice ? <div className="state state-success admin-notice">{notice}</div> : null}
    </div>
  );
}

interface PromptPanelProps {
  token: string;
  active: PromptConfig | null;
  history: PromptConfig[];
  loading: boolean;
  error: string;
  onChanged: () => Promise<void>;
  onNotice: (value: string) => void;
  onError: (value: string) => void;
}

function usePromptForm(props: PromptPanelProps) {
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
    if (errors.name || errors.system || errors.template) return;
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

function PromptConfigPanel(props: PromptPanelProps) {
  const form = usePromptForm(props);
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <div className="eyebrow">NC-09 · UC03</div>
          <h3>Prompt / Model Config</h3>
        </div>
        {props.active ? <span className="status-badge">Active v{props.active.versionNumber}</span> : null}
      </div>
      <StateBlock loading={props.loading} error={props.error} />
      {props.active ? (
        <div className="help-box">
          <strong>{props.active.name}</strong>
          <p>
            {props.active.modelName} · schema {props.active.schemaVersion}
          </p>
        </div>
      ) : null}
      <PromptForm form={form} />
      <PromptHistory history={props.history} />
    </section>
  );
}

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
        Tạo version mới
      </button>
    </form>
  );
}

function PromptHistory({ history }: { history: PromptConfig[] }) {
  if (history.length === 0) return <StateBlock empty emptyText="Chưa có prompt history." />;
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

function useUsers(token: string, onError: (value: string) => void) {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true);
    onError("");
    try {
      setUsers((await listUsers(token)).data);
    } catch (requestError) {
      onError(errorText(requestError));
    } finally {
      setLoading(false);
    }
  }, [onError, token]);
  useEffect(() => {
    queueMicrotask(() => void load());
  }, [load]);
  return { users, loading, load };
}

function UserManagementPanel(props: {
  token: string;
  onNotice: (value: string) => void;
  onError: (value: string) => void;
}) {
  const state = useUsers(props.token, props.onError);
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <div className="eyebrow">NC-10 · UC02</div>
          <h3>Quản lý User</h3>
        </div>
      </div>
      <CreateUserForm token={props.token} onChanged={state.load} onNotice={props.onNotice} onError={props.onError} />
      <StateBlock
        loading={state.loading}
        empty={!state.loading && state.users.length === 0}
        emptyText="Chưa có user."
      />
      <div className="version-list">
        {state.users.map((user) => (
          <UserRow
            key={user.id}
            token={props.token}
            user={user}
            onChanged={state.load}
            onNotice={props.onNotice}
            onError={props.onError}
          />
        ))}
      </div>
    </section>
  );
}

interface UserActionProps {
  token: string;
  onChanged: () => Promise<void>;
  onNotice: (value: string) => void;
  onError: (value: string) => void;
}

function CreateUserForm(props: UserActionProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("qa");
  const [busy, setBusy] = useState(false);
  const emailError = email.length > 0 && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) ? "Email chưa đúng định dạng." : "";
  const passwordError = password.length > 0 && password.length < 10 ? "Mật khẩu phải có ít nhất 10 ký tự." : "";

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (emailError || passwordError || !email || !password) return;
    setBusy(true);
    props.onError("");
    try {
      const created = await createUser(props.token, email, password, role);
      props.onNotice(`Đã tạo ${created.role}: ${created.email}`);
      setEmail("");
      setPassword("");
      await props.onChanged();
    } catch (requestError) {
      props.onError(errorText(requestError));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="stack-form" onSubmit={submit}>
      <label>
        Email
        <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        <FieldError message={emailError} />
      </label>
      <label>
        Password
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          minLength={10}
          maxLength={128}
          required
        />
        <FieldError message={passwordError} />
      </label>
      <label>
        Role
        <select value={role} onChange={(event) => setRole(event.target.value as UserRole)}>
          <option value="qa">QA</option>
          <option value="manager">Manager</option>
          <option value="admin">Admin</option>
        </select>
      </label>
      <button
        className="primary-button"
        disabled={busy || Boolean(emailError || passwordError) || !email || !password}
        type="submit"
      >
        Tạo tài khoản
      </button>
    </form>
  );
}

function UserRow(props: UserActionProps & { user: User }) {
  const [role, setRole] = useState<UserRole>(props.user.role);
  const [busy, setBusy] = useState(false);
  async function save(input: { role?: UserRole; isActive?: boolean }) {
    setBusy(true);
    props.onError("");
    try {
      const updated = await updateUser(props.token, props.user.id, input);
      props.onNotice(`Đã cập nhật ${updated.email}.`);
      await props.onChanged();
    } catch (requestError) {
      props.onError(errorText(requestError));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="user-row">
      <div>
        <strong>{props.user.email}</strong>
        <span className="muted-text">#{props.user.id}</span>
      </div>
      <select value={role} onChange={(event) => setRole(event.target.value as UserRole)} disabled={busy}>
        <option value="qa">QA</option>
        <option value="manager">Manager</option>
        <option value="admin">Admin</option>
      </select>
      <button
        className="ghost-button compact"
        disabled={busy || role === props.user.role}
        onClick={() => save({ role })}
        type="button"
      >
        Lưu role
      </button>
      <button
        className="ghost-button compact"
        disabled={busy}
        onClick={() => save({ isActive: !props.user.isActive })}
        type="button"
      >
        {props.user.isActive ? "Vô hiệu hóa" : "Kích hoạt"}
      </button>
    </div>
  );
}
