// ✅ CLEAN and FIXED App.jsx
import React, { useEffect, useState, useMemo } from 'react';
import TempPlot from './components/TempPlot';
import StatCard from './components/StatCard';
import IdleScreen from './components/IdleScreen';

function App() {
  const [dataPoints, setDataPoints] = useState([]);
  const [xAxisMode, setXAxisMode] = useState('tss');
  const [isStale, setIsStale] = useState(false);
  const [isSimulated, setIsSimulated] = useState(false);
  const [isIdle, setIsIdle] = useState(false);
  const [sessionStartTime, setSessionStartTime] = useState(null);
  const [avgScope, setAvgScope] = useState(10);
  const scopeOptions = ['5', '10', '30', 'all'];
  const [grillSet, setGrillSet] = useState(null);
  const [probeSet, setProbeSet] = useState(null);
  const [connected, setConnected] = useState(null);
  const [ambientTemp, setAmbientTemp] = useState(null);
  const [lastConnected, setLastConnected] = useState(null);
  const [cookTimerRemaining, setCookTimerRemaining] = useState(null);

  useEffect(() => {
    fetch(`http://localhost:8000/api/history`)
      .then(res => res.json())
      .then(data => {
        const parsed = data.map(d => ({
          ...d,
          time: new Date(d.time * 1000),
        }));
        setDataPoints(parsed);
      })
      .catch(err => console.error("Failed to fetch history:", err));
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      fetch(`http://localhost:8000/api/stats`)
        .then(res => res.json())
        .then(data => {
          setIsIdle(data.is_idle || false);
          const now = new Date();
          if (data.grill_temp === 0 && data.probe_temp === 0) return;

          const newPoint = {
            time: now,
            grill_temp: data.grill_temp,
            probe_temp: data.probe_temp,
          };

          setDataPoints(prev => [...prev, newPoint]);
          setIsSimulated(data.is_simulated || false);
          setIsIdle(data.is_idle || false);
          setIsStale(data.is_stale || false);
          setGrillSet(data.grill_set ?? null);
          setProbeSet(data.probe_set ?? null);
          setConnected(data.connected ?? null);
          setAmbientTemp(data.ambient_temp ?? null);
          setLastConnected(data.last_connected ?? null);

          if (!sessionStartTime && data.session_start_time) {
            setSessionStartTime(new Date(data.session_start_time));
          }

          setCookTimerRemaining(data.cook_timer_remaining ?? null);
        })
        .catch(err => console.error("Failed to fetch stats:", err));
    }, 2000);

    return () => clearInterval(interval);
  }, [sessionStartTime]);

  const formatTimeSinceStart = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const {
    elapsedSeconds,
    timestamps,
    grillY,
    probeY,
    avgGrill,
    avgProbe,
    sdGrill,
    sdProbe,
    probeRate,
    latestGrill,
    latestProbe,
  } = useMemo(() => {
    const now = Date.now();
    const baseTime = dataPoints[0]?.time?.getTime() || now;

    const timestamps = dataPoints.map(d => d.time);
    const elapsedSeconds = dataPoints.map(d => (d.time.getTime() - baseTime) / 1000);

    const avg = (arr, key) => (arr.length ? arr.reduce((sum, d) => sum + d[key], 0) / arr.length : 0);
    const stdDev = (arr, key) => {
      const mean = avg(arr, key);
      const variance = arr.reduce((acc, d) => acc + Math.pow(d[key] - mean, 2), 0) / arr.length;
      return Math.sqrt(variance);
    };

    const scoped = avgScope === 'all'
      ? dataPoints
      : dataPoints.filter(d => now - d.time.getTime() <= parseInt(avgScope) * 60 * 1000);

    const last30 = dataPoints.filter(d => now - d.time.getTime() <= 30 * 60 * 1000);

    const grillY = dataPoints.map(d => d.grill_temp);
    const probeY = dataPoints.map(d => d.probe_temp);

    const probeRate = (() => {
      if (last30.length < 2) return 0;
      const first = last30[0];
      const last = last30[last30.length - 1];
      const deltaTemp = last.probe_temp - first.probe_temp;
      const deltaTime = (last.time - first.time) / 60000;
      return deltaTime > 0 ? deltaTemp / deltaTime : 0;
    })();

    const latest = dataPoints.at(-1) || {};

    return {
      elapsedSeconds,
      timestamps,
      grillY,
      probeY,
      avgGrill: avg(scoped, 'grill_temp'),
      avgProbe: avg(scoped, 'probe_temp'),
      sdGrill: stdDev(scoped, 'grill_temp'),
      sdProbe: stdDev(scoped, 'probe_temp'),
      probeRate,
      latestGrill: latest.grill_temp ?? 0,
      latestProbe: latest.probe_temp ?? 0,
    };
  }, [dataPoints, avgScope]);

  const isTSS = xAxisMode === 'tss';

  if (isStale) return <div className="text-center text-4xl text-red-600 p-10">🚫 STALE MODE</div>;
  if (isIdle && !isSimulated) return <IdleScreen />;

  return (
    <div className="min-h-screen font-sans p-6 bg-cover bg-center" style={{ backgroundImage: "url('/images/wood.jpg')" }}>
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="w-full mb-6">
          <img src="/images/traegerBanner.jpg" alt="Traeger Banner" className="w-full max-h-[380px] object-cover rounded-lg shadow-md" />
        </div>

        <div className="flex flex-col sm:flex-row justify-between items-center bg-[#CC5C30] text-[#F5F0E6] shadow-md rounded p-4">
          <div className="flex items-baseline space-x-2">
            <h1 className="text-2xl font-bold leading-tight">Live:</h1>
            <div className="text-2xl flex items-baseline space-x-8">
              <span>Grill: <strong>{Math.round(latestGrill)}°F</strong></span>
              <span>Probe: <strong>{Math.round(latestProbe)}°F</strong></span>
            </div>
          </div>
          <button
            onClick={() => setXAxisMode(prev => prev === 'tss' ? 'clock' : 'tss')}
            className="px-2 py-1 text-sm border rounded bg-black text-white hover:bg-gray-700"
          >
            Toggle X Axis: {isTSS ? 'Clock Time' : 'Time Since Start'}
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6 bg-[#CC5C30] p-4 rounded-md shadow-md">
            <TempPlot
              title="Grill Temperature"
              x={isTSS ? elapsedSeconds : timestamps}
              y={grillY}
              lineColor="#ffffff"
              isTSS={isTSS}
              initialDtick={30}
            />
            <TempPlot
              title="Probe Temperature"
              x={isTSS ? elapsedSeconds : timestamps}
              y={probeY}
              lineColor="#ffffff"
              isTSS={isTSS}
              initialDtick={15}
            />
          </div>

          <div className="bg-[#CC5C30] text-black p-4 rounded-md space-y-6 shadow-md">
            <StatCard label="Avg Grill Temp" value={avgGrill} sd={sdGrill} unit="°F" scopeOptions={scopeOptions} selectedScope={avgScope} onScopeChange={setAvgScope}>
              {typeof grillSet === "number" && <div><strong>Setpoint:</strong> {grillSet.toFixed(1)}°F</div>}
            </StatCard>
            <StatCard label="Avg Probe Temp" value={avgProbe} sd={sdProbe} unit="°F" scopeOptions={scopeOptions} selectedScope={avgScope} onScopeChange={setAvgScope}>
              {typeof probeSet === "number" && <div><strong>Setpoint:</strong> {probeSet.toFixed(1)}°F</div>}
              <div><strong>Delta:</strong> {(probeSet - latestProbe).toFixed(1)}°F</div>
              {sessionStartTime && <div><strong>Elapsed:</strong> {formatTimeSinceStart((Date.now() - sessionStartTime.getTime()) / 1000)}</div>}
            </StatCard>
            <StatCard label="Δ Probe / Min (30m)" value={probeRate} unit="°F">
              {cookTimerRemaining !== null && <div><strong>Timer Left:</strong> {Math.round(cookTimerRemaining / 60)} min</div>}
              {ambientTemp !== null && <div><strong>Ambient:</strong> {ambientTemp.toFixed(1)}°F</div>}
              {typeof connected === "boolean" && <div><strong>Connected:</strong> {connected ? "Yes" : "No"}</div>}
              {lastConnected && <div><strong>Last Connected:</strong> {new Date(lastConnected).toLocaleString()}</div>}
            </StatCard>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
