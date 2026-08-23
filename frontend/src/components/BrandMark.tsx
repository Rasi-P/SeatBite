export default function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className="brand-mark">
      <span className="brand-icon"><i /><i /><i /></span>
      {!compact && <span>SeatBite</span>}
    </div>
  );
}

