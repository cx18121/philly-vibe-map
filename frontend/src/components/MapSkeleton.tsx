export default function MapSkeleton() {
  return (
    <div style={{
      width: '100%',
      height: '100vh',
      background: '#1a1a2e',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <div style={{
        color: '#666',
        fontSize: '1.2rem',
        animation: 'pulse 1.5s ease-in-out infinite',
      }}>
        Loading map...
      </div>
    </div>
  );
}
