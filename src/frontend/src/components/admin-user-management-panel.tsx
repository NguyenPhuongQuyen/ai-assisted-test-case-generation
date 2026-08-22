"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

import { FormEvent, useCallback, useEffect, useState } from "react";

import { createUser, listUsers, updateUser } from "@/services/admin";
import { ApiError } from "@/services/api";
import { USER_ROLE } from "@/constants/user-role";
import type { User, UserRole } from "@/types/api";

import { FieldError, StateBlock } from "./state-block";

interface AdminUserManagementPanelProps {
  token: string;
  onNotice: (value: string) => void;
}

interface UserActionProps {
  token: string;
  onChanged: () => Promise<void>;
  onNotice: (value: string) => void;
  onError: (value: string) => void;
}

interface CreateUserFieldsProps {
  email: string;
  password: string;
  role: UserRole;
  emailError: string;
  passwordError: string;
  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onRoleChange: (value: UserRole) => void;
}

function errorText(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

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

function CreateUserFields(props: CreateUserFieldsProps) {
  return (
    <>
      <label>
        Email
        <input
          type="email"
          value={props.email}
          onChange={(event) => props.onEmailChange(event.target.value)}
          required
        />
        <FieldError message={props.emailError} />
      </label>

      <label>
        Password
        <input
          type="password"
          value={props.password}
          onChange={(event) => props.onPasswordChange(event.target.value)}
          minLength={10}
          maxLength={128}
          required
        />
        <FieldError message={props.passwordError} />
      </label>

      <label>
        Role
        <select value={props.role} onChange={(event) => props.onRoleChange(event.target.value as UserRole)}>
          <option value={USER_ROLE.QA}>QA</option>
          <option value={USER_ROLE.MANAGER}>Manager</option>
          <option value={USER_ROLE.ADMIN}>Admin</option>
        </select>
      </label>
    </>
  );
}

function useCreateUserForm(props: UserActionProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>(USER_ROLE.QA);
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

  return {
    email,
    setEmail,
    password,
    setPassword,
    role,
    setRole,
    busy,
    emailError,
    passwordError,
    submit,
  };
}

function CreateUserForm(props: UserActionProps) {
  const form = useCreateUserForm(props);

  const disabled = form.busy || Boolean(form.emailError || form.passwordError) || !form.email || !form.password;

  return (
    <form className="stack-form" onSubmit={form.submit}>
      <CreateUserFields
        email={form.email}
        password={form.password}
        role={form.role}
        emailError={form.emailError}
        passwordError={form.passwordError}
        onEmailChange={form.setEmail}
        onPasswordChange={form.setPassword}
        onRoleChange={form.setRole}
      />

      <button className="primary-button" disabled={disabled} type="submit">
        {form.busy ? "Đang tạo..." : "Tạo tài khoản"}
      </button>
    </form>
  );
}

function useUserRowActions(props: UserActionProps & { user: User }) {
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

  return {
    role,
    setRole,
    busy,
    save,
  };
}

function UserRow(props: UserActionProps & { user: User }) {
  const actions = useUserRowActions(props);

  return (
    <div className="user-row">
      <div>
        <strong>{props.user.email}</strong>
        <span className="muted-text">#{props.user.id}</span>
      </div>

      <select
        value={actions.role}
        onChange={(event) => actions.setRole(event.target.value as UserRole)}
        disabled={actions.busy}
        aria-label={`Vai trò của ${props.user.email}`}
      >
        <option value={USER_ROLE.QA}>QA</option>
        <option value={USER_ROLE.MANAGER}>Manager</option>
        <option value={USER_ROLE.ADMIN}>Admin</option>
      </select>

      <button
        className="ghost-button compact"
        disabled={actions.busy || actions.role === props.user.role}
        onClick={() => actions.save({ role: actions.role })}
        type="button"
      >
        Lưu role
      </button>

      <button
        className="ghost-button compact"
        disabled={actions.busy}
        onClick={() =>
          actions.save({
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
