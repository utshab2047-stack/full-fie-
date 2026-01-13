import React from 'react';
import { goals } from '../data/goals';

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

export default GoalSelection;