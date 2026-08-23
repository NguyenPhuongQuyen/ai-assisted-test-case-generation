"use client";

// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

import { USER_ROLE } from "@/constants/user-role";
import { useState } from "react";

import type { User } from "@/types/api";

import { AdminPromptConfigPanel } from "./admin-prompt-config-panel";
import { AdminUserManagementPanel } from "./admin-user-management-panel";
import { StateBlock } from "./state-block";

interface AdminWorkspaceProps {
  token: string;
  user: User;
}

export function AdminWorkspace({ token, user }: AdminWorkspaceProps) {
  const [notice, setNotice] = useState("");

  if (user.role !== USER_ROLE.ADMIN) {
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
