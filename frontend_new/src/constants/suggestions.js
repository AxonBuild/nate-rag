import { Home, RefreshCw, BookOpen, BarChart2 } from 'lucide-react';

export const SUGGESTIONS = [
  { icon: Home,      title: 'Explain the STR loophole', desc: 'How a W-2 earner deducts rental losses against salary', q: 'Explain how the short-term rental loophole works for a high-income W-2 earner' },
  { icon: RefreshCw, title: '1031 exchange timeline',   desc: 'The 45 / 180-day rules and how to avoid boot', q: 'Walk me through a 1031 exchange and the 45 and 180 day rules' },
  { icon: BookOpen,  title: 'Augusta Rule + kids',      desc: 'Owner strategies that move income out of bracket', q: 'How do the Augusta Rule and paying my children reduce taxes?' },
  { icon: BarChart2, title: 'Should I elect S-Corp?',   desc: 'Reasonable salary vs. distributions math', q: 'When should I elect S-Corp status and what is a reasonable salary?' },
];

/** Illustrative breakdowns when the API does not return chart aggregates. */
export const STATS_CHARTS = {
  by_type: [
    { label: 'Guides',    value: 2140, color: 'var(--type-guide)' },
    { label: 'Scripts',   value: 1880, color: 'var(--type-script)' },
    { label: 'Q&A Pairs', value: 4280, color: 'var(--type-qa)' },
    { label: 'SEO',       value: 1460, color: 'var(--type-seo)' },
    { label: 'Research',  value: 720,  color: 'var(--type-research)' },
  ],
  by_topic: [
    { label: '1031s', value: 88 }, { label: 'STR', value: 96 }, { label: 'REPS', value: 72 },
    { label: 'Cost Seg', value: 64 }, { label: 'S Corp', value: 80 }, { label: 'QOZ', value: 44 },
    { label: 'Augusta', value: 58 },
  ],
};
