import React, { useState } from 'react';
import { TrendingUp } from 'lucide-react';

// ============= DATA FILES =============
// data/investorTypes.js
const investorTypes = [
  { id: 'job', label: 'Job Holder', icon: '💼' },
  { id: 'business', label: 'Businessman', icon: '🏢' },
  { id: 'household', label: 'Household Woman', icon: '🏠' },
  { id: 'retired', label: 'Retired Personnel', icon: '🎯' },
  { id: 'hnwi', label: 'High Net Worth Individual', icon: '💎' }
];

// data/


// data/strategies.js
const strategies = {
  '5yr': {
    sipAmount: 3000,
    targetAmount: 400000,
    yearlyPlan: [
      {
        year: 1,
        title: 'Accumulation Phase',
        allocation: [
          { sector: 'Banks', percent: 30 },
          { sector: 'Hydropower', percent: 15 },
          { sector: 'Life Insurance', percent: 15 },
          { sector: 'Mutual Funds', percent: 15 },
          { sector: 'Microfinance', percent: 10 },
          { sector: 'Others', percent: 15 }
        ],
        action: 'Any sector > 35%? Book partial profit → Shift to Banks/Mutual Funds'
      },
      {
        year: 2,
        title: 'Growth Positioning',
        focus: ['Hydropower', 'Microfinance', 'Insurance'],
        action: 'Hydropower gain > 40%? Rebalance → Shift gains to Insurance'
      },
      {
        year: 3,
        title: 'Aggressive Expansion',
        strategy: 'High Equity Allocation',
        action: 'Book 15–20% profit from fast movers'
      },
      {
        year: 4,
        title: 'Profit Protection',
        increase: ['Banks', 'Mutual Funds', 'Preference Shares'],
        action: 'Market overheated? Reduce high beta stocks'
      },
      {
        year: 5,
        title: 'Capital Consolidation',
        allocation: [
          { sector: 'Banks', percent: 35 },
          { sector: 'Mutual Funds', percent: 20 },
          { sector: 'Life Insurance', percent: 20 },
          { sector: 'Preference Shares', percent: 25 }
        ],
        action: 'Create cash buffer & lock gains'
      }
    ]
  },
  // Add 10yr and 20yr strategies here later
};

// ============= CUSTOM HOOK =============
// hooks/useInvestmentFlow.js
const useInvestmentFlow = () => {
  const [step, setStep] = useState('start');
  const [investorType, setInvestorType] = useState('');
  const [goal, setGoal] = useState('');
  const [currentYear, setCurrentYear] = useState(0);

  const handleStart = () => setStep('investor');
  
  const handleInvestorSelect = (type) => {
    setInvestorType(type);
    setStep('goal');
  };
  
  const handleGoalSelect = (goalId) => {
    setGoal(goalId);
    if (strategies[goalId]) {
      setStep('strategy');
      setCurrentYear(0);
    }
  };

  const handleReset = () => {
    setStep('start');
    setInvestorType('');
    setGoal('');
    setCurrentYear(0);
  };

  return {
    step,
    investorType,
    goal,
    currentYear,
    setCurrentYear,
    handleStart,
    handleInvestorSelect,
    handleGoalSelect,
    handleReset
  };
};

// ============= COMPONENTS =============
// components/StartScreen.jsx
const StartScreen = ({ onStart }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] space-y-8">
      <div className="text-center space-y-4 max-w-2xl">
        <h2 className="text-3xl font-semibold">Begin Your Wealth Journey</h2>
        <p className="text-slate-300 text-lg">
          A personalized investment strategy tailored to your profile and goals
        </p>
      </div>
      <button
        onClick={onStart}
        className="group px-8 py-4 bg-gradient-to-r from-blue-500 to-emerald-500 rounded-xl font-semibold text-lg hover:scale-105 transition-transform shadow-lg shadow-blue-500/50 flex items-center gap-3"
      >
        Start Investment Journey
        <span className="group-hover:translate-x-1 transition-transform">→</span>
      </button>
    </div>
  );
};

// components/InvestorSelection.jsx
const InvestorSelection = ({ onSelect }) => {
  return (
    <div className="space-y-8">
      <div className="text-center">
        <h2 className="text-3xl font-semibold mb-2">Select Your Profile</h2>
        <p className="text-slate-300">Choose the profile that best describes you</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {investorTypes.map((type) => (
          <button
            key={type.id}
            onClick={() => onSelect(type.id)}
            className="group p-6 bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl hover:border-blue-500 hover:bg-slate-800 transition-all hover:scale-105"
          >
            <div className="text-5xl mb-3">{type.icon}</div>
            <div className="text-xl font-semibold">{type.label}</div>
          </button>
        ))}
      </div>
    </div>
  );
};

// components/GoalSelection.jsx
const GoalSelection = ({ onSelect }) => {
  return (
    <div className="space-y-8">
      <div className="text-center">
        <h2 className="text-3xl font-semibold mb-2">Choose Your Investment Goal</h2>
        <p className="text-slate-300">Select your investment timeline</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {goals.map((g) => (
          <button
            key={g.id}
            onClick={() => onSelect(g.id)}
            className="group p-8 bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl hover:border-blue-500 hover:bg-slate-800 transition-all hover:scale-105"
          >
            <div className={`w-16 h-16 ${g.color} rounded-full flex items-center justify-center mb-4 mx-auto group-hover:scale-110 transition-transform`}>
              <span className="text-3xl">🎯</span>
            </div>
            <div className="text-2xl font-bold mb-2">{g.duration}</div>
            <div className="text-slate-400">{g.subtitle}</div>
          </button>
        ))}
      </div>
    </div>
  );
};

// components/StrategyDisplay.jsx
const StrategyDisplay = ({ goal, currentYear, onYearChange, onReset }) => {
  const strategy = strategies[goal];
  
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

  const { sipAmount, targetAmount, yearlyPlan } = strategy;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-500/20 to-blue-500/20 border border-emerald-500/30 rounded-xl p-6 backdrop-blur">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-2xl font-bold mb-1">{goal.toUpperCase()} Wealth Accumulation Strategy</h2>
            <p className="text-slate-300">Monthly SIP: NPR {sipAmount.toLocaleString()}</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-slate-400">Target Amount</div>
            <div className="text-3xl font-bold text-emerald-400">NPR {targetAmount.toLocaleString()}+</div>
          </div>
        </div>
      </div>

      {/* Year Navigation */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        <button
          onClick={() => onYearChange(0)}
          className={`px-6 py-3 rounded-lg font-semibold whitespace-nowrap transition-all ${
            currentYear === 0 ? 'bg-blue-500 shadow-lg shadow-blue-500/50' : 'bg-slate-800 hover:bg-slate-700'
          }`}
        >
          Overview
        </button>
        {yearlyPlan.map((_, idx) => (
          <button
            key={idx}
            onClick={() => onYearChange(idx + 1)}
            className={`px-6 py-3 rounded-lg font-semibold whitespace-nowrap transition-all ${
              currentYear === idx + 1 ? 'bg-blue-500 shadow-lg shadow-blue-500/50' : 'bg-slate-800 hover:bg-slate-700'
            }`}
          >
            Year {idx + 1}
          </button>
        ))}
      </div>

      {/* Overview */}
      {currentYear === 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {yearlyPlan.map((year) => (
            <div
              key={year.year}
              className="p-6 bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl hover:border-blue-500 transition-all cursor-pointer"
              onClick={() => onYearChange(year.year)}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center text-xl font-bold">
                  {year.year}
                </div>
                <div>
                  <div className="font-semibold text-sm text-slate-400">Year {year.year}</div>
                  <div className="font-bold">{year.title}</div>
                </div>
              </div>
              <div className="text-sm text-slate-300">{year.action}</div>
            </div>
          ))}
        </div>
      )}

      {/* Individual Year Details */}
      {currentYear > 0 && (
        <YearDetails 
          year={yearlyPlan[currentYear - 1]} 
          currentYear={currentYear}
          totalYears={yearlyPlan.length}
        />
      )}

      {/* Reset Button */}
      <div className="text-center pt-4">
        <button
          onClick={onReset}
          className="px-6 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg font-semibold transition-colors"
        >
          Start New Journey
        </button>
      </div>
    </div>
  );
};

// Year Details Sub-component
const YearDetails = ({ year, currentYear, totalYears }) => {
  return (
    <div className="space-y-6">
      <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-8">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-emerald-500 rounded-full flex items-center justify-center text-2xl font-bold">
            {currentYear}
          </div>
          <div>
            <div className="text-sm text-slate-400">Year {currentYear}</div>
            <div className="text-3xl font-bold">{year.title}</div>
          </div>
        </div>

        {/* Allocation */}
        {year.allocation && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
              🛡️ Portfolio Allocation
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {year.allocation.map((item, idx) => (
                <div key={idx} className="p-4 bg-slate-900/50 rounded-lg border border-slate-600">
                  <div className="text-2xl font-bold text-emerald-400 mb-1">{item.percent}%</div>
                  <div className="text-sm text-slate-300">{item.sector}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Focus Areas */}
        {year.focus && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-4">Increase Exposure</h3>
            <div className="flex flex-wrap gap-2">
              {year.focus.map((item, idx) => (
                <div key={idx} className="px-4 py-2 bg-blue-500/20 border border-blue-500/30 rounded-full text-blue-300">
                  {item}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Strategy */}
        {year.strategy && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-2">Strategy</h3>
            <p className="text-lg text-slate-300">{year.strategy}</p>
          </div>
        )}

        {/* Increase Areas */}
        {year.increase && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-4">Increase Allocation</h3>
            <div className="flex flex-wrap gap-2">
              {year.increase.map((item, idx) => (
                <div key={idx} className="px-4 py-2 bg-emerald-500/20 border border-emerald-500/30 rounded-full text-emerald-300">
                  {item}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action */}
        <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-start gap-3">
          <span className="text-amber-400 mt-1 text-xl">⚠️</span>
          <div>
            <div className="font-semibold text-amber-300 mb-1">Key Action</div>
            <div className="text-slate-300">{year.action}</div>
          </div>
        </div>
      </div>

      {/* Final Year Message */}
      {currentYear === totalYears && (
        <div className="bg-gradient-to-r from-emerald-500/20 to-blue-500/20 border border-emerald-500/30 rounded-xl p-8 text-center">
          <div className="text-6xl mb-4">✅</div>
          <h3 className="text-2xl font-bold mb-2">Target Achieved!</h3>
          <p className="text-xl text-emerald-400 font-semibold mb-2">≈ NPR 400,000+</p>
          <p className="text-slate-300">Exit or continue your SIP cycle for further growth</p>
        </div>
      )}
    </div>
  );
};

// ============= MAIN APP =============
// App.jsx
export default function App() {
  const {
    step,
    investorType,
    goal,
    currentYear,
    setCurrentYear,
    handleStart,
    handleInvestorSelect,
    handleGoalSelect,
    handleReset
  } = useInvestmentFlow();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 text-white p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-block p-3 bg-blue-500/20 rounded-full mb-4">
            <TrendingUp className="w-12 h-12 text-blue-400" />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
            Investment Journey
          </h1>
          <p className="text-slate-300 text-lg">Smart wealth building strategy for your future</p>
        </div>

        {/* Route to appropriate screen */}
        {step === 'start' && <StartScreen onStart={handleStart} />}
        {step === 'investor' && <InvestorSelection onSelect={handleInvestorSelect} />}
        {step === 'goal' && <GoalSelection onSelect={handleGoalSelect} />}
        {step === 'strategy' && (
          <StrategyDisplay
            goal={goal}
            currentYear={currentYear}
            onYearChange={setCurrentYear}
            onReset={handleReset}
          />
        )}
      </div>
    </div>
  );
}