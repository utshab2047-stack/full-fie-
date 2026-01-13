import React, { useState, useEffect } from 'react';
import { strategies } from '../data/strategies';
import YearDetails from './YearDetails';
import { Edit2, Save, ChevronLeft, ChevronRight } from 'lucide-react';

const StrategyDisplay = ({ goal, currentYear, onYearChange, onReset }) => {
  const strategy = strategies[goal];

  // Local state for editable fields
  const [editableSip, setEditableSip] = useState('');
  const [editableTarget, setEditableTarget] = useState('');

  // Sync state when goal/strategy changes
  useEffect(() => {
    if (strategy) {
      setEditableSip(strategy.sipAmount);
      setEditableTarget(strategy.targetAmount);
    }
  }, [goal, strategy]);

  const [currentSpent, setCurrentSpent] = useState(0);

  // Live Market Data State
  const [marketData, setMarketData] = useState({});

  // Fetch Live Market Data
  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        const res = await fetch('http://localhost:8002/api/market');
        const data = await res.json();
        const lookup = {};
        if (data.stocks) {
          if (!Array.isArray(data.stocks)) {
            Object.assign(lookup, data.stocks);
          } else {
            data.stocks.forEach(s => lookup[s.symbol] = s);
          }
        }
        setMarketData(lookup);
      } catch (err) {
        console.error("Failed to fetch market data:", err);
      }
    };

    fetchMarketData();
    const interval = setInterval(fetchMarketData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (!strategy) {
    return (
      <div className="text-center p-8">
        <p className="text-xl text-slate-300">Strategy for this goal is coming soon!</p>
        <button
          onClick={onReset}
          className="mt-4 px-6 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg font-semibold transition-colors"
        >
          Go Back
        </button>
      </div>
    );
  }

  const { yearlyPlan, labels } = strategy;

  // Defaults/Fallback
  const titleText = labels?.title || `${goal.toUpperCase()} Wealth Accumulation Strategy`;
  const sipLabel = labels?.sip || 'Monthly SIP';
  const targetLabel = labels?.target || 'Target Amount';
  const timelinePrefix = labels?.timelinePrefix || 'Year';

  const handlePrev = () => {
    if (currentYear > 0) onYearChange(currentYear - 1);
  };

  const handleNext = () => {
    if (currentYear < yearlyPlan.length) onYearChange(currentYear + 1);
  };

  const handleSaveConfig = () => {
    // Simulate save
    // In a real app, this would save editableSip and editableTarget to backend/context
    alert("Configuration Saved!");
  };

  return (
    <div className="space-y-8">
      <div className="bg-gradient-to-r from-emerald-500/20 to-blue-500/20 border border-emerald-500/30 rounded-xl p-6 backdrop-blur">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex-1">
            <h2 className="text-2xl font-bold mb-2">{titleText}</h2>
            <div className="flex items-center gap-2 text-slate-300">
              <span>{sipLabel}: NPR</span>
              <input
                type="text"
                value={editableSip}
                onChange={(e) => setEditableSip(e.target.value)}
                className="bg-transparent border-b border-emerald-500/50 focus:border-emerald-500 outline-none w-32 font-medium text-emerald-300 placeholder-slate-500"
                placeholder="Enter Amount"
              />
              <Edit2 size={14} className="text-slate-500" />
            </div>
          </div>

          {/* CENTER: MAXIMUM ALLOWED LOSS */}
          <div className="text-center px-6 py-2 bg-slate-900/50 rounded-lg border border-slate-700">
            <div className="text-xs text-slate-400 uppercase font-bold tracking-wider mb-1">Maximum Allowed Loss</div>
            <div className={`text-2xl font-black ${((Number(editableSip) || 0) - (currentSpent || 0)) * ((Number(editableTarget) || 0) / 100) < 1000
              ? 'text-red-500 animate-pulse'
              : 'text-blue-400'
              }`}>
              NPR {Math.max(0, ((Number(editableSip) || 0) - (currentSpent || 0)) * ((Number(editableTarget) || 0) / 100)).toLocaleString()}
            </div>
          </div>

          <div className="text-right">
            <div className="text-sm text-slate-400 mb-1">{targetLabel}</div>
            <div className="flex items-center justify-end gap-2 text-3xl font-bold text-emerald-400">
              <input
                type="number"
                value={editableTarget}
                onChange={(e) => setEditableTarget(e.target.value)}
                className="bg-transparent border-b border-emerald-500/50 focus:border-emerald-500 outline-none w-24 text-right font-bold text-emerald-400 placeholder-emerald-700/50"
                placeholder="%"
              />
              <span>%</span>
              <Edit2 size={18} className="text-emerald-600" />
            </div>

            <button
              onClick={handleSaveConfig}
              className="flex items-center gap-2 px-3 py-1 bg-slate-700 hover:bg-slate-600 rounded text-xs font-semibold text-slate-300 transition-colors mt-1"
            >
              <Save size={14} />
              Save Config
            </button>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between gap-2">
        <button
          onClick={handlePrev}
          disabled={currentYear === 0}
          className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          title="Previous"
        >
          <ChevronLeft size={24} />
        </button>

        <div className="flex gap-2 overflow-x-auto pb-2 custom-scrollbar flex-1">
          <button
            onClick={() => onYearChange(0)}
            className={`px-6 py-3 rounded-lg font-semibold whitespace-nowrap transition-all ${currentYear === 0 ? 'bg-blue-500 shadow-lg shadow-blue-500/50' : 'bg-slate-800 hover:bg-slate-700'
              }`}
          >
            Overview
          </button>
          {yearlyPlan.map((_, idx) => (
            <button
              key={idx}
              onClick={() => onYearChange(idx + 1)}
              className={`px-6 py-3 rounded-lg font-semibold whitespace-nowrap transition-all ${currentYear === idx + 1 ? 'bg-blue-500 shadow-lg shadow-blue-500/50' : 'bg-slate-800 hover:bg-slate-700'
                }`}
            >
              {timelinePrefix} {idx + 1}
            </button>
          ))}
        </div>

        <button
          onClick={handleNext}
          disabled={currentYear === yearlyPlan.length}
          className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          title="Next"
        >
          <ChevronRight size={24} />
        </button>
      </div>

      {
        currentYear === 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {yearlyPlan.map((item) => (
              <div
                key={item.year}
                className="p-6 bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl hover:border-blue-500 transition-all cursor-pointer"
                onClick={() => onYearChange(item.year)}
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center text-xl font-bold">
                    {item.year}
                  </div>
                  <div>
                    <div className="font-semibold text-sm text-slate-400">{timelinePrefix} {item.year}</div>
                    <div className="font-bold">{item.title}</div>
                  </div>
                </div>
                <div className="text-sm text-slate-300">{item.action}</div>
              </div>
            ))}
          </div>
        )
      }

      {
        currentYear > 0 && (
          <YearDetails
            year={yearlyPlan[currentYear - 1]}
            currentYear={currentYear}
            totalYears={yearlyPlan.length}
            prefix={timelinePrefix} // Pass prefix down if needed
            budget={(Number(editableSip) || 0) * ((Number(editableTarget) || 0) / 100)} // Calculate budget based on Risk %
            totalEquity={(Number(editableSip) || 0)} // Pass raw Total Equity (SIP Amount)
            riskPercentage={(Number(editableTarget) || 0)} // Pass Risk %
            onSpentChange={setCurrentSpent}
            marketData={marketData}
          />
        )
      }

      <div className="text-center pt-4">
        <button
          onClick={onReset}
          className="px-6 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg font-semibold transition-colors"
        >
          Start New Journey
        </button>
      </div>
    </div >
  );
};

export default StrategyDisplay;