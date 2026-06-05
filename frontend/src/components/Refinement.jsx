export default function Refinement({ refined, keywords }) {
  return (
    <div>
      <div className="refine-row">
        <span className="lab">Refined query</span>
        <span className="val">"{refined}"</span>
      </div>
      <div className="refine-row" style={{ marginBottom: 8 }}>
        <span className="lab">Keywords</span>
      </div>
      <div className="kw-row">
        {(keywords || []).map((k, i) => <span key={i} className="kw">{k}</span>)}
      </div>
    </div>
  );
}
