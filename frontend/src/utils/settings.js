const STORAGE_KEY = 'nate_ai_user_settings';

export const RETRIEVAL_MIN = 5;
export const RETRIEVAL_MAX = 20;

export const DEFAULT_SETTINGS = {
  /** null = let query refinement pick chunk count (5–20) */
  retrievalLimit: null,
  systemPrompt: '',
};

export function loadSettings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT_SETTINGS };
    const parsed = JSON.parse(raw);
    return {
      retrievalLimit:
        parsed.retrievalLimit == null || parsed.retrievalLimit === ''
          ? null
          : Number(parsed.retrievalLimit),
      systemPrompt: typeof parsed.systemPrompt === 'string' ? parsed.systemPrompt : '',
    };
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
}

export function saveSettings(settings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}

/** Extra fields for chat/search API bodies. */
export function requestSettingsPayload(settings) {
  const body = {};
  const limit = settings?.retrievalLimit;
  if (limit != null && !Number.isNaN(limit)) {
    body.retrieval_limit = Math.max(RETRIEVAL_MIN, Math.min(RETRIEVAL_MAX, Math.round(limit)));
  }
  const sys = settings?.systemPrompt?.trim();
  if (sys) body.system_prompt = sys;
  return body;
}
