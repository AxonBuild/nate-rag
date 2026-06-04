import { useRef, useCallback, useEffect } from 'react';

const TICK_MS = 14;
const TARGET_TICKS = 300;

function prefersReducedMotion() {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * After SSE `done`, reveal the full answer with a short typewriter effect.
 */
export function useAnswerReveal(patchAi) {
  const timerRef = useRef(null);

  const clearReveal = useCallback(() => {
    if (timerRef.current != null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => clearReveal, [clearReveal]);

  const revealAnswer = useCallback(
    (aiId, data) => {
      clearReveal();
      const full = data.answer || '';
      const meta = {
        search: data.search,
        timing: data.timing,
        verification: data.verification ?? null,
        status: null,
        error: false,
      };

      if (!full || prefersReducedMotion()) {
        patchAi(aiId, { ...meta, answer: full, streaming: false });
        return;
      }

      patchAi(aiId, { ...meta, answer: '', streaming: true });
      const step = Math.max(1, Math.ceil(full.length / TARGET_TICKS));
      let shown = 0;

      const tick = () => {
        shown = Math.min(full.length, shown + step);
        patchAi(aiId, {
          ...meta,
          answer: full.slice(0, shown),
          streaming: shown < full.length,
        });
        if (shown < full.length) {
          timerRef.current = setTimeout(tick, TICK_MS);
        }
      };

      tick();
    },
    [patchAi, clearReveal],
  );

  return { revealAnswer, clearReveal };
}
