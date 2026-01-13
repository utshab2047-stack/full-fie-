import React from 'react';

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

export default StartScreen;