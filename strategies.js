const baseStrategy = {
  sipAmount: 3000,
  targetAmount: 400000,
  yearlyPlan: [
    {
      year: 1,
      title: 'Accumulation Phase',
      allocation: [
        { sector: 'Commercial Banks', percent: 30 },
        { sector: 'Hydropower', percent: 15 },
        { sector: 'Life Insurance', percent: 15 },
        { sector: 'Mutual Funds', percent: 15 },
        { sector: 'Microfinance', percent: 10 },
        { sector: 'Others', percent: 15 }
      ],
      action: 'Any sector > 35%? Book partial profit → Shift to Commercial Banks/Mutual Funds'
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
      increase: ['Commercial Banks', 'Mutual Funds', 'Preference Shares'],
      action: 'Market overheated? Reduce high beta stocks'
    },
    {
      year: 5,
      title: 'Capital Consolidation',
      allocation: [
        { sector: 'Commercial Banks', percent: 35 },
        { sector: 'Mutual Funds', percent: 20 },
        { sector: 'Life Insurance', percent: 20 },
        { sector: 'Preference Shares', percent: 25 }
      ],
      action: 'Create cash buffer & lock gains'
    }
  ]
};

const weeklyStrategy = {
  // Custom labels for the UI
  labels: {
    title: 'Trading Strategy',
    sip: 'Total Equity',
    target: 'Risk Tolerance',
    timelinePrefix: 'Day'
  },
  sipAmount: 50000,
  targetAmount: '20', // Risk Tolerance (%)
  yearlyPlan: [
    { year: 1, title: 'Day 1: Market Analysis', action: 'Analyze trend & volume' },
    { year: 2, title: 'Day 2: Entry Positions', action: 'Enter high momentum stocks' },
    { year: 3, title: 'Day 3: Monitor & Adjust', action: 'Check stop-losses' },
    { year: 4, title: 'Day 4: Profit Booking', action: 'Book 50% profits on spikes' },
    { year: 5, title: 'Day 5: Week Closing', action: 'Square off intraday positions' },
    { year: 6, title: 'Day 6: Review', action: 'Review weekly performance' }
  ]
};

const monthlyStrategy = {
  labels: {
    title: 'Monthly Strategy',
    sip: 'Monthly Budget',
    target: 'Risk Tolerance (%)',
    timelinePrefix: 'Week'
  },
  sipAmount: 100000,
  targetAmount: '20',
  yearlyPlan: [
    { year: 1, title: 'Week 1: Initial Allocation', action: 'Deploy capital in core sectors' },
    { year: 2, title: 'Week 2: Momentum Building', action: 'Add to winning positions' },
    { year: 3, title: 'Week 3: Mid-Month Review', action: 'Rebalance underperforming stocks' },
    { year: 4, title: 'Week 4: Profit Taking', action: 'Trim high RSI stocks' },
    { year: 5, title: 'Last Week: Closing/Rollover', action: 'Finalize monthly P&L' }
  ]
};

const trimesterStrategy = {
  labels: {
    title: 'Trimester Trading Strategy',
    sip: 'Monthly SIP',
    target: 'Risk Tolerance (%)',
    timelinePrefix: 'Period'
  },
  sipAmount: 3000,
  targetAmount: '20',
  yearlyPlan: [
    { year: 1, title: '18 Days Period 1', action: 'Initial Entry & Setup' },
    { year: 2, title: '18 Days Period 2', action: 'Momentum Capture' },
    { year: 3, title: '18 Days Period 3', action: 'Mid-term Review & Rebalance' },
    { year: 4, title: '18 Days Period 4', action: 'Profit Booking Zone' },
    { year: 5, title: '18 Days Period 5', action: 'Final Exit & Assessment' }
  ]
};

export const strategies = {
  'weekly': weeklyStrategy,
  'monthly': monthlyStrategy,
  '3month': trimesterStrategy,
  '6month': baseStrategy,
  '1yr': baseStrategy,
  '3yr': baseStrategy,
  '5yr': baseStrategy,
  '10yr': baseStrategy,
  '20yr': baseStrategy
};