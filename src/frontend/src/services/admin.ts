// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

import type { PromptConfig, PromptConfigListResponse, User, UserListResponse, UserRole } from "@/types/api";
import { apiRequest } from "./api";

export function listUsers(token: string): Promise<UserListResponse> {
  return apiRequest<UserListResponse>("/users?page=1&pageSize=100", {}, token);
}

export function createUser(token: string, email: string, password: string, role: UserRole): Promise<User> {
  return apiRequest<User>("/users", { method: "POST", body: JSON.stringify({ email, password, role }) }, token);
}

export function updateUser(
  token: string,
  userId: number,
  input: { email?: string; password?: string; role?: UserRole; isActive?: boolean },
): Promise<User> {
  return apiRequest<User>(
    `/users/${userId}`,
    {
      method: "PATCH",
      body: JSON.stringify({
        ...(input.email !== undefined ? { email: input.email } : {}),
        ...(input.password !== undefined ? { password: input.password } : {}),
        ...(input.role !== undefined ? { role: input.role } : {}),
        ...(input.isActive !== undefined ? { is_active: input.isActive } : {}),
      }),
    },
    token,
  );
}

export function listPromptConfigs(token: string): Promise<PromptConfigListResponse> {
  return apiRequest<PromptConfigListResponse>("/prompt-configs?page=1&pageSize=100", {}, token);
}

export function getActivePromptConfig(token: string): Promise<PromptConfig> {
  return apiRequest<PromptConfig>("/prompt-configs/active", {}, token);
}

export function createPromptConfig(
  token: string,
  input: {
    name: string;
    systemPrompt: string;
    userPromptTemplate: string;
    modelName: string;
    schemaVersion: string;
    maxOutputTokens: number;
  },
): Promise<PromptConfig> {
  return apiRequest<PromptConfig>(
    "/prompt-configs",
    {
      method: "POST",
      body: JSON.stringify({
        name: input.name,
        system_prompt: input.systemPrompt,
        user_prompt_template: input.userPromptTemplate,
        model_name: input.modelName,
        schema_version: input.schemaVersion,
        max_output_tokens: input.maxOutputTokens,
      }),
    },
    token,
  );
}
