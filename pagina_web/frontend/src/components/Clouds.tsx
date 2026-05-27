// Nubes decorativas que derivan lentamente. Puramente visual (aria-hidden).
export default function Clouds({ className = '' }: { className?: string }) {
  return (
    <div className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`} aria-hidden="true">
      <div className="cloud cloud-a" />
      <div className="cloud cloud-b" />
      <div className="cloud cloud-c" />
    </div>
  )
}
