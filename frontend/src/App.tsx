import { useState, useEffect } from 'react';
import { Simulation } from './Simulation';

function App() {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate initial load for smooth transition
    const timer = setTimeout(() => setIsLoading(false), 800);
    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return (
      <div className="h-screen w-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-800 flex items-center justify-center">
        <div className="text-center">
          <div className="relative mb-6">
            <div className="w-16 h-16 rounded-full border-2 border-cyan-500/20 animate-spin" style={{ animationDuration: '2s' }}>
              <div className="absolute inset-0 rounded-full border-t-2 border-cyan-400" />
            </div>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-2xl">◈</span>
            </div>
          </div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
            SYNTHESIA
          </h1>
          <p className="text-sm text-gray-500 mt-2">Initializing ecosystem...</p>
        </div>
      </div>
    );
  }

  return <Simulation />;
}

export default App;
