import {
  ApprovalsApi,
  AuthApi,
  ChangesApi,
  CompletionApi,
  Configuration,
  DocumentsApi,
  EvidenceApi,
  HistoryApi,
  ImpactsApi,
  LatexApi,
  SystemApi,
} from "@/api/generated";

const configuration = new Configuration({
  basePath: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  baseOptions: {
    withCredentials: true,
  },
});

export const approvalsApi = new ApprovalsApi(configuration);
export const authApi = new AuthApi(configuration);
export const changesApi = new ChangesApi(configuration);
export const completionApi = new CompletionApi(configuration);
export const documentsApi = new DocumentsApi(configuration);
export const evidenceApi = new EvidenceApi(configuration);
export const historyApi = new HistoryApi(configuration);
export const impactsApi = new ImpactsApi(configuration);
export const latexApi = new LatexApi(configuration);
export const systemApi = new SystemApi(configuration);
