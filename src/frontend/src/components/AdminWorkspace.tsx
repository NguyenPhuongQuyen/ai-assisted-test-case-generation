"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

import { useState } from "react";

import type { User } from "@/types/api";

import { AdminPromptConfigPanel } from "./AdminPromptConfigPanel";
import { AdminUserManagementPanel } from "./AdminUserManagementPanel";
import { StateBlock } from "./StateBlock";

interface AdminWorkspaceProps {
  token: string;
  user: User;
}

export function AdminWorkspace({ token, user }: AdminWorkspaceProps) {
  const [notice, setNotice] = useState("");

  if (user.role !== "admin") {
    return <StateBlock empty emptyText="Chỉ Admin được truy cập cấu hình hệ thống." />;
  }

  return (
    <div className="admin-layout">
      <AdminPromptConfigPanel token={token} onNotice={setNotice} />

      <AdminUserManagementPanel token={token} onNotice={setNotice} />

      {notice ? <div className="state state-success admin-notice">{notice}</div> : null}
    </div>
  );
}
