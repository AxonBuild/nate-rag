import { Sun, Moon } from 'lucide-react';

export default function ThemeToggle({ theme, onToggle }) {
  return (
    <button type="button" className="theme-toggle" onClick={onToggle} title="Toggle theme">
      <span className="knob">
        {theme === 'dark' ? <Moon size={14} /> : <Sun size={14} />}
      </span>
    </button>
  );
}
