export default function LoadingSpinner() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%' }}>
      <div className="spinner" style={{ marginBottom: '16px' }}></div>
      <p style={{ color: '#94a3b8' }}>Loading initial graph data...</p>
    </div>
  );
}
