import { useState, useEffect } from 'react';
import { strategies } from '../data/strategies';

export const useInvestmentFlow = () => {
  const [step, setStepState] = useState('start');
  const [investorType, setInvestorType] = useState('');
  const [goal, setGoal] = useState('');
  const [currentYear, setCurrentYear] = useState(0);

  // New Authentication States
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);

  // Helper to update state and push a new history entry
  const setStep = (newStep, shouldPush = true) => {
    setStepState(newStep);
    if (shouldPush) {
      window.history.pushState({ step: newStep }, '', `#${newStep}`);
    }
  };

  // Sync with browser "Back" button
  useEffect(() => {
    const handlePopState = (event) => {
      if (event.state && event.state.step) {
        setStepState(event.state.step);
      } else {
        // Fallback or initial state
        setStepState('start');
      }
    };

    // Add initial state if null so "Back" can return somewhere if necessary, 
    // though typically the first load doesn't need a pushState unless we want to enforce it.
    // For now, attaching listener is key.
    window.addEventListener('popstate', handlePopState);

    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, []);

  const handleStart = () => setStep('investor');

  const handleInvestorSelect = (type) => {
    setInvestorType(type);
    setStep('portfolio_setup');
  };

  const handlePortfolioSetup = () => {
    // Intercept flow: Check if authenticated
    if (isAuthenticated) {
      setStep('goal');
    } else {
      setShowLoginModal(true);
      // We don't change 'step' here, just show modal.
      // If user cancels, they stay on 'portfolio_setup'
    }
  };

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
    setShowLoginModal(false);
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
    // Optional: decided if reset should clear auth. usually yes for a demo/wizard flow.
    setIsAuthenticated(false);
    setShowLoginModal(false);

    // Clear history fragment
    window.history.pushState({ step: 'start' }, '', '#start');
  };

  return {
    step,
    investorType,
    goal,
    currentYear,
    setCurrentYear,
    isAuthenticated,
    showLoginModal,
    setShowLoginModal,
    handleLoginSuccess,
    handleStart,
    handleInvestorSelect,
    handlePortfolioSetup,
    handleGoalSelect,
    handleReset
  };
};