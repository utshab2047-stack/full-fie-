import React from 'react';
import { investorTypes } from '../data/investorTypes';

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

export default InvestorSelection;