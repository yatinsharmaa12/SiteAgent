export type Company = { id: number; name: string; website_url: string };
export type CrawlJob = {
  job_id: number; company_id: number; status: string; max_pages: number; max_depth: number;
  pages_discovered: number; pages_crawled: number; pages_indexed: number; pages_failed: number;
  pages_new: number; pages_changed: number; pages_unchanged: number; pages_deactivated: number;
  attempt_count: number; error: string | null; created_at: string; started_at: string | null;
  completed_at: string | null; duration_seconds: number | null;
};
export type ChatResponse = { answer: string; sources: { title: string | null; url: string }[] };
