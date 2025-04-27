// src/utils/getTickFormat.js
export function getTickFormat(xData, isTSS) {
  const maxTicks = 6;
  const tickEvery = Math.max(1, Math.floor(xData.length / maxTicks));
  const tickIndices = xData.map((_, i) => i).filter(i => i % tickEvery === 0);

  const tickvals = tickIndices.map(i => xData[i]);
  const ticktext = tickIndices.map(i => {
    if (isTSS) {
      const sec = xData[i];
      const m = Math.floor(sec / 60).toString().padStart(2, '0');
      const s = Math.floor(sec % 60).toString().padStart(2, '0');
      return `${m}:${s}`;
    } else {
      const date = xData[i];
      if (!(date instanceof Date)) return '';
      const elapsed = (xData.at(-1) - xData[0]) / 1000;
      const showSec = elapsed < 300;
      return date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        ...(showSec ? { second: '2-digit' } : {}),
      });
    }
  });

  return { tickvals, ticktext };
}
