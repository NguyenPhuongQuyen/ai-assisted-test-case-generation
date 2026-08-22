"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

import { FormEvent, useCallback, useEffect, useState } from "react";

import { createUser, listUsers, updateUser } from "@/services/admin";
import { ApiError } from "@/services/api";
import type { User, UserRole } from "@/types/api";

import { FieldError, StateBlock } from "./StateBlock";

interface AdminUserManagementPanelProps {
  token: string;
  onNotice: (value: string) => void;
}

function errorText(error: unknown): string {
  if (error instanceof ApiError) return error.message;

  return error instanceof Error ? error.message : "Không thể cập nhật người dùng.";
}

export function AdminUserManagementPanel({ token, onNotice }: AdminUserManagementPanelProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      setUsers((await listUsers(token)).data);
    } catch (requestError) {
      setError(errorText(requestError));
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    queueMicrotask(() => void load());
  }, [load]);

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <div className="eyebrow">NC-10 · UC02</div>
          <h3>Quản lý User</h3>
        </div>
      </div>

      <CreateUserForm token={token} onChanged={load} onNotice={onNotice} onError={setError} />

      <StateBlock
        loading={loading}
        error={error}
        empty={!loading && !error && users.length === 0}
        emptyText="Chưa có user."
      />

      <div className="version-list">
        {users.map((user) => (
          <UserRow key={user.id} token={token} user={user} onChanged={load} onNotice={onNotice} onError={setError} />
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

    if (emailError || passwordError || !email || !password) {
      return;
    }

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
        {busy ? "Đang tạo..." : "Tạo tài khoản"}
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

      <select
        value={role}
        onChange={(event) => setRole(event.target.value as UserRole)}
        disabled={busy}
        aria-label={`Vai trò của ${props.user.email}`}
      >
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
        onClick={() =>
          save({
            isActive: !props.user.isActive,
          })
        }
        type="button"
      >
        {props.user.isActive ? "Vô hiệu hóa" : "Kích hoạt"}
      </button>
    </div>
  );
}
