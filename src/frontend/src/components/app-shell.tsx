"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).
import { USER_ROLE } from "@/constants/user-role";
import type { ReactNode } from "react";

import type { User } from "@/types/api";

export type WorkspaceKey = "requirements" | "testcases" | "modules" | "admin";

interface AppShellProps {
  user: User;
  active: WorkspaceKey;
  onChange: (workspace: WorkspaceKey) => void;
  onLogout: () => void;
  children: ReactNode;
}

const labels: Record<WorkspaceKey, string> = {
  requirements: "Requirement & AI",
  testcases: "Review Test Case",
  modules: "Module & Coverage",
  admin: "System Config",
};

export function AppShell({ user, active, onChange, onLogout, children }: AppShellProps) {
  const workspaces = (Object.keys(labels) as WorkspaceKey[]).filter(
    (key) => key !== "admin" || user.role === USER_ROLE.ADMIN,
  );
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <div className="brand-mark">AI</div>
          <div className="brand-title">Test Case Generator</div>
          <div className="role-pill">{user.role.toUpperCase()}</div>
        </div>
        <nav className="side-nav" aria-label="Điều hướng chính">
          {workspaces.map((workspace) => (
            <button
              className={active === workspace ? "nav-button active" : "nav-button"}
              key={workspace}
              onClick={() => onChange(workspace)}
              type="button"
            >
              {labels[workspace]}
            </button>
          ))}
        </nav>
        <button className="ghost-button" onClick={onLogout} type="button">
          Đăng xuất
        </button>
      </aside>
      <section className="main-area">
        <header className="topbar">
          <div>
            <div className="eyebrow">Human-in-the-loop QA workspace</div>
            <h2>{labels[active]}</h2>
          </div>
          <div className="user-chip">{user.email}</div>
        </header>
        <div className="workspace">{children}</div>
      </section>
    </div>
  );
}
