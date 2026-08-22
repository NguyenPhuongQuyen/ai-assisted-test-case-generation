"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).
import { FormEvent, useState } from "react";

import { login } from "@/services/auth";
import { ApiError, saveToken } from "@/services/api";
import type { AuthResponse } from "@/types/api";
import { FieldError } from "./StateBlock";

interface LoginScreenProps {
  onLogin: (session: AuthResponse) => void;
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Không thể đăng nhập. Vui lòng thử lại.";
}

export function LoginScreen({ onLogin }: LoginScreenProps) {
  const [email, setEmail] = useState("qa@example.com");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const validEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const emailError = email.length > 0 && !validEmail ? "Email chưa đúng định dạng." : "";
  const passwordError = password.length === 0 ? "Vui lòng nhập mật khẩu." : "";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!validEmail || !password) return;
    setLoading(true);
    setError("");
    try {
      const session = await login(email, password);
      saveToken(session.access_token);
      onLogin(session);
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <div className="eyebrow">ITEC4401 · Đề tài #13</div>
        <h1>AI Test Case Generator</h1>
        <p>Đăng nhập để nhập requirement, sinh test case bằng AI và thực hiện Human-in-the-loop review.</p>
        <LoginForm
          values={{ email, password }}
          loading={loading}
          error={error}
          errors={{ email: emailError, password: passwordError }}
          setters={{ email: setEmail, password: setPassword }}
          onSubmit={handleSubmit}
        />
        <p className="login-note">Tài khoản demo được tạo bằng script seed; mật khẩu lấy từ DEMO_USER_PASSWORD.</p>
      </section>
    </main>
  );
}

interface LoginFormProps {
  values: { email: string; password: string };
  loading: boolean;
  error: string;
  errors: { email: string; password: string };
  setters: { email: (value: string) => void; password: (value: string) => void };
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}

function LoginForm(props: LoginFormProps) {
  return (
    <form onSubmit={props.onSubmit} className="stack-form">
      <label>
        Email
        <input
          type="email"
          value={props.values.email}
          onChange={(event) => props.setters.email(event.target.value)}
          required
        />
        <FieldError message={props.errors.email} />
      </label>
      <label>
        Mật khẩu
        <input
          type="password"
          value={props.values.password}
          onChange={(event) => props.setters.password(event.target.value)}
          minLength={1}
          maxLength={128}
          required
        />
        <FieldError message={props.errors.password} />
      </label>
      {props.error ? <div className="state state-error">{props.error}</div> : null}
      <button
        className="primary-button"
        disabled={props.loading || Boolean(props.errors.email || props.errors.password)}
        type="submit"
      >
        {props.loading ? "Đang đăng nhập..." : "Đăng nhập"}
      </button>
    </form>
  );
}
