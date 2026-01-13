import React from 'react';
import { TrendingUp } from 'lucide-react';
import { useInvestmentFlow } from './hooks/useInvestmentFlow';
import StartScreen from './components/StartScreen';
import InvestorSelection from './components/InvestorSelection';
import PMSPortfolioPage from './components/PMSPortfolioPage';
import GoalSelection from './components/GoalSelection';
import StrategyDisplay from './components/StrategyDisplay';
import LoginRegistrationModal from './components/LoginRegistrationModal';

export default function App() {
  const {
    step,
    goal,
    currentYear,
    setCurrentYear,
    showLoginModal,
    setShowLoginModal,
    handleLoginSuccess,
    handleStart,
    handleInvestorSelect,
    handlePortfolioSetup,
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

        {/* Modular Navigation Logic */}
        {step === 'start' && <StartScreen onStart={handleStart} />}
        {step === 'investor' && <InvestorSelection onSelect={handleInvestorSelect} />}
        {step === 'portfolio_setup' && <PMSPortfolioPage onContinue={handlePortfolioSetup} onLoginSuccess={handleLoginSuccess} />}
        {step === 'goal' && <GoalSelection onSelect={handleGoalSelect} />}
        {step === 'strategy' && (
          <StrategyDisplay
            goal={goal}
            currentYear={currentYear}
            onYearChange={setCurrentYear}
            onReset={handleReset}
          />
        )}

        {/* Login Modal Overlay */}
        <LoginRegistrationModal
          isOpen={showLoginModal}
          onClose={() => setShowLoginModal(false)}
          onSuccess={handleLoginSuccess}
        />

      </div>
    </div>
  );
}
