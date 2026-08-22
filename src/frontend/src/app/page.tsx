"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).
import { useEffect, useState } from "react";

import { AdminWorkspace } from "@/components/AdminWorkspace";
import { AppShell, type WorkspaceKey } from "@/components/AppShell";
import { LoginScreen } from "@/components/LoginScreen";
import { ModuleWorkspace } from "@/components/ModuleWorkspace";
import { RequirementWorkspace } from "@/components/RequirementWorkspace";
import { TestCaseWorkspace } from "@/components/TestCaseWorkspace";
import { clearToken, readToken } from "@/services/api";
import type { AuthResponse, User } from "@/types/api";

const USER_KEY = "testcase_ai_user";

function readStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export default function HomePage() {
  const [token, setToken] = useState("");
  const [user, setUser] = useState<User | null>(null);
  const [workspace, setWorkspace] = useState<WorkspaceKey>("requirements");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    queueMicrotask(() => {
      setToken(readToken() ?? "");
      setUser(readStoredUser());
      setReady(true);
    });
  }, []);

  function handleLogin(session: AuthResponse) {
    setToken(session.access_token);
    setUser(session.user);
    window.localStorage.setItem(USER_KEY, JSON.stringify(session.user));
    setWorkspace(session.user.role === "admin" ? "admin" : "requirements");
  }

  function logout() {
    clearToken();
    window.localStorage.removeItem(USER_KEY);
    setToken("");
    setUser(null);
    setWorkspace("requirements");
  }

  if (!ready)
    return (
      <main className="login-page">
        <div className="state state-loading">Đang khởi tạo...</div>
      </main>
    );
  if (!token || !user) return <LoginScreen onLogin={handleLogin} />;
  return (
    <AppShell user={user} active={workspace} onChange={setWorkspace} onLogout={logout}>
      {workspace === "requirements" ? <RequirementWorkspace token={token} user={user} /> : null}
      {workspace === "testcases" ? <TestCaseWorkspace token={token} user={user} /> : null}
      {workspace === "modules" ? <ModuleWorkspace token={token} user={user} /> : null}
      {workspace === "admin" ? <AdminWorkspace token={token} user={user} /> : null}
    </AppShell>
  );
}
