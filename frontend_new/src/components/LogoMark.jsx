export default function LogoMark({ size = 36 }) {
  return (
    <span style={{
      display: 'inline-grid', placeItems: 'center',
      width: size, height: size, borderRadius: size * 0.28,
      background: 'linear-gradient(150deg, var(--accent-strong), var(--accent))',
      boxShadow: '0 3px 10px color-mix(in srgb, var(--accent) 38%, transparent)',
      flex: '0 0 auto',
    }}>
      <svg width={size * 0.56} height={size * 0.56} viewBox="0 0 24 24" fill="none">
        <path d="M5 19V5l14 14V5" stroke="#0C1726" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </span>
  );
}
