import { apiClient } from '@/api/client';
import type { AnalysisDetail, AnalysisList, AnalysisSummary, DashboardStats } from '@/types';

export interface CreateAnalysisPayload {
  resume: File;
  jobDescription: string;
  jobTitle?: string;
  companyName?: string;
  title?: string;
  storeResumeText?: boolean;
}

export const analysesApi = {
  create: ({
    resume,
    jobDescription,
    jobTitle,
    companyName,
    title,
    storeResumeText = false,
  }: CreateAnalysisPayload) => {
    const form = new FormData();
    form.append('resume', resume);
    form.append('job_description', jobDescription);
    if (jobTitle) form.append('job_title', jobTitle);
    if (companyName) form.append('company_name', companyName);
    if (title) form.append('title', title);
    form.append('store_resume_text', String(storeResumeText));

    return apiClient
      .post<AnalysisDetail>('/analyses', form, {
        // The deterministic analysis plus an optional AI call can legitimately
        // take a while on a cold free-tier instance.
        timeout: 120_000,
      })
      .then((r) => r.data);
  },

  list: (page = 1, pageSize = 10) =>
    apiClient
      .get<AnalysisList>('/analyses', { params: { page, page_size: pageSize } })
      .then((r) => r.data),

  get: (id: string) => apiClient.get<AnalysisDetail>(`/analyses/${id}`).then((r) => r.data),

  rename: (id: string, title: string) =>
    apiClient.patch<AnalysisSummary>(`/analyses/${id}`, { title }).then((r) => r.data),

  remove: (id: string) => apiClient.delete<void>(`/analyses/${id}`).then(() => undefined),

  stats: () => apiClient.get<DashboardStats>('/analyses/stats/summary').then((r) => r.data),

  regenerateRecommendations: (id: string) =>
    apiClient
      .post<AnalysisDetail>(`/analyses/${id}/recommendations`, null, { timeout: 60_000 })
      .then((r) => r.data),
};
