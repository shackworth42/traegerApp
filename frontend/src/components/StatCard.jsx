import React from 'react';

const StatCard = ({
  label,
  value,
  unit,
  sd = null,
  scopeOptions,
  selectedScope,
  onScopeChange,
  children,
}) => (
  <div className="bg-white text-black border border-gray-300 p-4 rounded-md shadow">
    <div className="flex justify-between items-center mb-2">
      <div className="text-sm font-semibold">
        {label}: {value.toFixed(1)}{unit}
      </div>
      {scopeOptions && (
        <select
          className="text-xs border border-gray-300 rounded bg-white text-black"
          value={selectedScope}
          onChange={(e) => onScopeChange(e.target.value)}
        >
          {scopeOptions.map(opt => (
            <option key={opt} value={opt}>
              {opt === 'all' ? 'All Time' : `${opt}m`}
            </option>
          ))}
        </select>
      )}
    </div>

    {sd !== null && (
      <div className="text-xs text-gray-600 mb-1">
        ±SD: {sd.toFixed(1)}{unit}
      </div>
    )}

    {children && (
      <div className="mt-2 text-xs text-gray-800 space-y-1">
        {children}
      </div>
    )}
  </div>
);

export default StatCard;