import { useState } from 'react';
import { ChevronRight } from 'lucide-react';

export default function Disclosure({ icon: Icon, label, count, defaultOpen = false, children }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="disclosure">
      <button className={`disc-head${open ? ' open' : ''}`} onClick={() => setOpen(!open)}>
        <span className="chev"><ChevronRight size={15} /></span>
        {Icon && <span className="dico"><Icon size={15} /></span>}
        <span>{label}</span>
        {count != null && <span className="dcount">{count}</span>}
      </button>
      <div className={`disc-body${open ? ' open' : ''}`}>
        <div><div className="disc-inner">{children}</div></div>
      </div>
    </div>
  );
}
