import React, { useState } from 'react';
import Plot from 'react-plotly.js';

const TempPlot = ({ title, x, y, lineColor, isTSS, initialDtick = 20 }) => {
  const [layout, setLayout] = useState(null);
  const [hover, setHover] = useState(true);
  

  const handleRelayout = (newLayout) => {
    const yMin = newLayout['yaxis.range[0]'];
    const yMax = newLayout['yaxis.range[1]'];
    const xMin = newLayout['xaxis.range[0]'];
    const xMax = newLayout['xaxis.range[1]'];
  
    let newDtick = initialDtick;
  
    if (typeof yMin === 'number' && typeof yMax === 'number') {
      const yRange = yMax - yMin;
  
      if (yRange <= 10) newDtick = 1;
      else if (yRange <= 20) newDtick = 2;
      else if (yRange <= 40) newDtick = 5;
      else if (yRange <= 80) newDtick = 10;
      else newDtick = initialDtick;
    }
  
    setLayout(prev => ({
      ...prev,
      xaxis: {
        ...prev?.xaxis,
        range: xMin && xMax ? [xMin, xMax] : prev?.xaxis?.range,
      },
      yaxis: {
        ...prev?.yaxis,
        range: yMin && yMax ? [yMin, yMax] : prev?.yaxis?.range,
        dtick: newDtick,
        tickmode: 'linear',
      },
    }));
  };
  

  const handleResetZoom = () => {
    setLayout(prev => ({
      ...prev,
      xaxis: {
        ...prev?.xaxis,
        range: null,
      },
    }));
  };

  const maxTicks = 6;
  const tickEvery = Math.max(1, Math.floor(x.length / maxTicks));
  const tickIndices = x.map((_, i) => i).filter(i => i % tickEvery === 0);
  const tickVals = tickIndices.map(i => i);
  const tickTexts = tickIndices.map(i => x[i]);
  const isZoomed = layout?.xaxis?.range !== undefined;
  const yMin = Math.min(...y);
  const yMax = Math.max(...y);
  const yBuffer = 5;



  const sharedLayout = {
    autosize: true,
    margin: { t: 20, l: 50, r: 20, b: 40 },
    xaxis: {
      title: {
        text: isTSS ? 'Time Since Start (MM:SS)' : 'Time (HH:MM)',
        font: { size: 12, color: '#ffffff' },
      },
      ...(isZoomed
        ? {
            tickmode: 'auto',
            nticks: 8,
          }
        : {
            tickmode: 'array',
            tickvals: tickVals.map(i => x[i]),
            ticktext: tickTexts,
          }),
      showgrid: true,
      gridcolor: '#CC5C30',
      color: '#ffffff',
      ...(layout?.xaxis?.range ? { range: layout.xaxis.range } : {}),
    },    
    yaxis: {
      title: {
        text: 'Temperature (°F)',
        font: { size: 12, color: '#ffffff' },
      },
      tickmode: 'linear',
      dtick: layout?.yaxis?.dtick ?? initialDtick,
      range: [yMin - yBuffer, yMax + yBuffer],
      showgrid: true,
      gridcolor: '#CC5C30',
      color: '#ffffff',
    },
    
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#ffffff' },
    hovermode: hover ? 'closest' : false,
  };

  return (
    <div className="bg-black text-[white] border border-gray-700 rounded-md p-4 shadow-sm">
      <div className="flex justify-between items-center mb-2">
        <div className="text-sm font-medium">{title}</div>
        <button
          onClick={handleResetZoom}
          className="px-2 py-1 text-xs border border-gray-400 rounded bg-black text-white hover:bg-gray-700 transition"
        >
          Reset Zoom
        </button>
      </div>

      <div className="w-full h-[300px]">
      <Plot
  data={[{
    x, // ✅ x is the full array of time strings like '10:32' or '00:45'
    y,
    type: 'scatter',
    mode: 'lines',
    line: { color: lineColor, width: 2 },
    name: title,
    hovertemplate: hover
      ? `%{x}<br>%{y:.1f}°F<extra></extra>` // ✅ use time string for x
      : 'skip',
  }]}

          layout={sharedLayout}
          config={{ responsive: true, displayModeBar: false }}
          useResizeHandler
          style={{ width: '100%', height: '100%', position: 'relative' }}
          onRelayout={handleRelayout}
        />
      </div>
    </div>
  );
};

export default TempPlot;