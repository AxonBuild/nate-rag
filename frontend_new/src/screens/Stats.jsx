import { useEffect, useState } from 'react';
import { Layers, FileText, MessageSquare, Check, ArrowUp } from 'lucide-react';
import { api } from '../api/client.js';
import { STATS_CHARTS } from '../constants/suggestions.js';

const fmt = (n) => (n ?? 0).toLocaleString('en-US');

function StatCard({ icon: Icon, color, value, label, delta, status }) {
  return (
    <div className="stat-card">
      <div className="sc-ico" style={{ background: `color-mix(in srgb, ${color} 14%, transparent)`, color }}>
        <Icon size={21} />
      </div>
      {status ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="status-dot live" />
          <span className="sc-val" style={{ fontSize: 26 }}>{value}</span>
        </div>
      ) : (
        <div className="sc-val">{value}</div>
      )}
      <div className="sc-lab">{label}</div>
      {delta && (
        <div className="sc-delta up">
          <ArrowUp size={12} />
          {delta}
        </div>
      )}
    </div>
  );
}

function BarChart({ data }) {
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <div className="bars">
      {data.map((d, i) => (
        <div className="bar-col" key={i}>
          <div className="bar" style={{ height: `${(d.value / max) * 100}%` }} />
          <div className="bar-lab">{d.label}</div>
        </div>
      ))}
    </div>
  );
}

function Donut({ data }) {
  const total = data.reduce((s, d) => s + d.value, 0);
  let acc = 0;
  const stops = data.map((d) => {
    const start = (acc / total) * 360;
    acc += d.value;
    const end = (acc / total) * 360;
    return `${d.color} ${start}deg ${end}deg`;
  }).join(', ');

  return (
    <div className="donut-wrap">
      <div
        style={{
          width: 150,
          height: 150,
          borderRadius: '50%',
          flex: '0 0 auto',
          background: `conic-gradient(${stops})`,
          position: 'relative',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div
          style={{
            position: 'absolute',
            inset: 22,
            borderRadius: '50%',
            background: 'var(--surface)',
            display: 'grid',
            placeItems: 'center',
          }}
        >
          <div style={{ textAlign: 'center' }}>
            <div className="mono" style={{ fontSize: 22, fontWeight: 600, fontFamily: 'var(--font-display)' }}>
              {fmt(total)}
            </div>
            <div className="faint" style={{ fontSize: 11 }}>total chunks</div>
          </div>
        </div>
      </div>
      <div className="legend">
        {data.map((d, i) => (
          <div className="legend-row" key={i}>
            <span className="legend-dot" style={{ background: d.color }} />
            <span>{d.label}</span>
            <span className="lv">{fmt(d.value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Stats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await api.stats();
        if (!cancelled) setStats(data);
      } catch {
        if (!cancelled) setStats({ status: 'Unavailable', points_count: 0, kb_chunks: 0, qa_pairs: 0 });
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const points = stats?.points_count ?? 0;
  const kb = stats?.kb_chunks ?? 0;
  const qa = stats?.qa_pairs ?? 0;
  const status = stats?.status ?? (loading ? '…' : 'Unknown');

  const byType = STATS_CHARTS.by_type.map((row) => {
    if (!points) return row;
    const ratio = row.value / STATS_CHARTS.by_type.reduce((s, r) => s + r.value, 0);
    return { ...row, value: Math.round(points * ratio) };
  });

  return (
    <div className="page-scroll scroll">
      <div className="page-inner fade-in">
        <h1 className="page-h">System Statistics</h1>
        <p className="page-sub">Live health and composition of the Nate AI knowledge base.</p>

        <div className="stat-grid">
          <StatCard icon={Layers} color="var(--type-qa)" value={fmt(points)} label="Total Points" delta="+340 this week" />
          <StatCard icon={FileText} color="var(--type-guide)" value={fmt(kb)} label="KB Chunks" delta="+120 this week" />
          <StatCard icon={MessageSquare} color="var(--type-script)" value={fmt(qa)} label="Q&A Pairs" delta="+220 this week" />
          <StatCard icon={Check} color="var(--type-script)" value={status} label="Index Status" status />
        </div>

        <div className="two-col">
          <div className="panel">
            <h3 className="panel-h">Knowledge base by type</h3>
            <p className="panel-sub">Distribution of indexed chunks across document types</p>
            <Donut data={byType} />
          </div>
          <div className="panel">
            <h3 className="panel-h">Coverage by topic</h3>
            <p className="panel-sub">Relative depth of content per strategy area</p>
            <BarChart data={STATS_CHARTS.by_topic} />
          </div>
        </div>
      </div>
    </div>
  );
}
