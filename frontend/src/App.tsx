import VibeMap from './components/VibeMap';
import Legend from './components/Legend';

export default function App() {
  return (
    <div style={{ position: 'relative', width: '100%', height: '100vh' }}>
      <VibeMap />
      <Legend />
    </div>
  );
}
