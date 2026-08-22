import { USER_ROLE } from "@/constants/user-role";

// Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

export type UserRole = (typeof USER_ROLE)[keyof typeof USER_ROLE];
export type TestCaseStatus = "draft" | "in_review" | "needs_fix" | "approved" | "exported" | "rejected";
export type Priority = "high" | "medium" | "low";

export interface User {
  id: number;
  email: string;
  role: UserRole;
  isActive: boolean;
}

export interface UserListResponse {
  data: User[];
  total: number;
  page: number;
  pageSize: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ModuleRecord {
  id: number;
  name: string;
  parent_id: number | null;
  created_by: number;
  created_at: string;
}

export interface ModuleListResponse {
  data: ModuleRecord[];
  total: number;
  page: number;
  pageSize: number;
}

export interface CoverageResponse {
  moduleId: number;
  totalRequirements: number;
  coveredRequirements: number;
  requirementCoveragePercent: number;
  totalTestCases: number;
  approvedTestCases: number;
  statusCounts: Record<TestCaseStatus, number>;
}

export interface RequirementRecord {
  id: number;
  module_id: number;
  content: string;
  acceptance_criteria: string | null;
  lock_version: number;
}

export interface GenerationJob {
  id: number;
  requirement_id: number;
  status: "queued" | "running" | "completed" | "failed";
  error_code: string | null;
}

export interface TestCaseRecord {
  id: number;
  requirement_id: number;
  module_id: number;
  summary: string;
  preconditions: string[];
  steps: string[];
  expected_result: string;
  priority: Priority;
  test_techniques: string[];
  tags: string[];
  review_note: string | null;
  status: TestCaseStatus;
  lock_version: number;
  created_by: number;
  created_at: string;
}

export interface TestCaseListResponse {
  data: TestCaseRecord[];
  total: number;
  page: number;
  pageSize: number;
}

export interface DuplicateCandidate {
  id: number;
  requirement_id: number;
  summary: string;
  status: TestCaseStatus;
  priority: Priority;
  similarity: number;
}

export interface DuplicateCandidateListResponse {
  data: DuplicateCandidate[];
  total: number;
  page: number;
  pageSize: number;
  threshold: number;
  embeddingModel: string;
  embeddingDimensions: number;
}

export interface TestCaseVersion {
  versionNumber: number;
  snapshot: Record<string, unknown>;
  createdBy: number;
  createdAt: string;
}

export interface TestCaseVersionListResponse {
  data: TestCaseVersion[];
  total: number;
  page: number;
  pageSize: number;
}

export interface VersionCompareResponse {
  fromVersion: number;
  toVersion: number;
  changes: Record<string, { from: unknown; to: unknown }>;
}

export interface PromptConfig {
  id: number;
  versionNumber: number;
  name: string;
  systemPrompt: string;
  userPromptTemplate: string;
  modelName: string;
  schemaVersion: string;
  maxOutputTokens: number;
  isActive: boolean;
  createdBy: number | null;
  createdAt: string;
}

export interface PromptConfigListResponse {
  data: PromptConfig[];
  total: number;
  page: number;
  pageSize: number;
}
