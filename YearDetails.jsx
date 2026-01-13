import React, { useState, useEffect } from 'react';
import { ChevronDown, Check, Rocket, Settings, Save, Calculator } from 'lucide-react';
import { nepaleseStocks } from '../data/nepaleseStocks';

import NepaliCalendarWidget from './NepaliCalendarWidget';

const YearDetails = ({ year, currentYear, totalYears, prefix, budget, totalEquity, riskPercentage, onSpentChange, marketData = {} }) => {
  // State for interactive stock selection
  const [expandedSector, setExpandedSector] = useState(null);
  const [selectedStocks, setSelectedStocks] = useState({});
  const [isSaved, setIsSaved] = useState(false);

  const [savedSectorAllocations, setSavedSectorAllocations] = useState({});

  // Calculate stats
  const totalSpent = Object.keys(selectedStocks).reduce((acc, symbol) => {
    const stock = selectedStocks[symbol];
    if (!stock) return acc;
    const price = Number(stock.purchasePrice) || 0;
    const qty = Number(stock.purchaseQty) || 0;
    return acc + (price * qty);
  }, 0);

  // Sync total spent with parent
  useEffect(() => {
    if (onSpentChange) {
      onSpentChange(totalSpent);
    }
  }, [totalSpent, onSpentChange]);

  const remainingBalance = totalEquity - totalSpent;
  const isLowBalance = remainingBalance < (totalEquity * 0.1); // Alert if < 10%

  const toggleStock = (stockSymbol) => {
    // Find the stock to get its current/live price for default
    let defaultPrice = 500;
    for (const [sec, stocks] of Object.entries(nepaleseStocks)) {
      const found = stocks.find(s => s.symbol === stockSymbol);
      if (found) {
        defaultPrice = marketData[stockSymbol]?.ltp || found.price || 500;
        break;
      }
    }

    setSelectedStocks(prev => ({
      ...prev,
      [stockSymbol]: prev[stockSymbol] ? null : {
        percent: '',
        purchasePrice: defaultPrice,
        purchaseQty: '',
        targetPrice: '',
        sellingQty: '',
        weight: 5
      }
    }));
  };

  // Helper:  Calculate total percent for indices (real-time)
  const calculateSectorTotal = (sectorName) => {
    const stocksInSector = nepaleseStocks[sectorName] || [];
    return stocksInSector.reduce((acc, stock) => {
      const stockData = selectedStocks[stock.symbol];
      return acc + (stockData ? (Number(stockData.weight) || 0) : 0);
    }, 0);
  };

  // Helper: Get effective percent (Live > Saved > Default)
  const getEffectiveSectorPercent = (sectorName) => {
    const stocksInSector = nepaleseStocks[sectorName] || [];
    // Check if any stock in this sector is selected (and not null)
    const hasActiveSelection = stocksInSector.some(s => selectedStocks[s.symbol]);

    if (hasActiveSelection) {
      return calculateSectorTotal(sectorName);
    }

    // Fallback to saved or default
    const sector = year.allocation?.find(s => s.sector === sectorName);
    return savedSectorAllocations[sectorName] !== undefined
      ? savedSectorAllocations[sectorName]
      : (sector?.percent || 0);
  };

  // Running Calculation Logic
  const calculateSectorStats = (sectorName) => {
    const allocPercent = getEffectiveSectorPercent(sectorName);

    // REFACTOR:  Allocation based on TOTAL EQUITY
    const allocatedAmount = (totalEquity * allocPercent) / 100;

    // Calculate actual spent in this sector
    // Need to correctly identify stocks belonging to this sector
    const stocksInSector = nepaleseStocks[sectorName] || [];
    const sectorSpent = stocksInSector.reduce((acc, stock) => {
      const details = selectedStocks[stock.symbol];
      if (details) {
        const price = Number(details.purchasePrice) || 0;
        const qty = Number(details.purchaseQty) || 0;
        return acc + (price * qty);
      }
      return acc;
    }, 0);

    return { allocatedAmount, sectorSpent, remaining: allocatedAmount - sectorSpent };
  };

  const handleSaveSector = (sectorName) => {
    const total = calculateSectorTotal(sectorName);
    setSavedSectorAllocations(prev => ({
      ...prev,
      [sectorName]: total
    }));
    // Optional: Add a brief flash or toast here if needed
  };

  const handleDetailsChange = (stockSymbol, field, value) => {
    setSelectedStocks(prev => ({
      ...prev,
      [stockSymbol]: { ...prev[stockSymbol], [field]: value }
    }));
  };

  const handleSaveAllocation = (target) => { // target can be 'all' or specific
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2000);
  };

  return (
    <div className="space-y-6">


      <div className="flex flex-col lg:flex-row gap-6">
        {/* LEFT COLUMN:  STOCK SELECTION & INPUTS */}
        <div className="flex-1 space-y-6">
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <div className="flex items-center gap-2 mb-4">
              <Settings className="text-orange-400" size={20} />
              <h3 className="text-lg font-bold text-blue-400">Optimize Your Portfolio (Interactive)</h3>
            </div>
            <p className="text-slate-400 text-sm mb-6">Select specific stocks for {prefix} {currentYear} to customize your weights. </p>

            {/* Restored Grid Layout */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.keys(nepaleseStocks).map((sectorName, idx) => {
                // Determine allocation:  Use saved, or year. allocation if exists, else 0
                const sectorConfig = year.allocation?.find(s => s.sector === sectorName);
                const isExpanded = expandedSector === sectorName;
                const sectorStocks = nepaleseStocks[sectorName] || []; // Access array from object

                // Specific Sector Stats
                const { allocatedAmount, sectorSpent, remaining } = calculateSectorStats(sectorName);

                // Display Percent
                const displayedPercent = getEffectiveSectorPercent(sectorName);

                return (
                  <div key={idx} className={`bg-slate-900/50 rounded-lg border transition-all ${isExpanded ? 'border-blue-500 ring-1 ring-blue-500/50 col-span-1 md:col-span-2 lg:col-span-3' : 'border-slate-700 hover:border-slate-600'}`}>
                    {/* HEADER */}
                    <div
                      className="p-4 flex items-center justify-between cursor-pointer"
                      onClick={() => setExpandedSector(isExpanded ? null : sectorName)}
                    >
                      <div>
                        <div className="text-2xl font-bold text-emerald-400">
                          {displayedPercent}%
                        </div>
                        <div className="text-sm font-medium text-slate-300">{sectorName}</div>
                        {isExpanded && (
                          <div className="text-xs text-slate-500 mt-1">
                            Alloc: NPR {allocatedAmount.toLocaleString()} | Spent: NPR {sectorSpent.toLocaleString()}
                          </div>
                        )}
                      </div>
                      <ChevronDown className={`text-slate-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                    </div>

                    {/* EXPANDED CONTENT */}
                    {isExpanded && (
                      <div className="p-4 border-t border-slate-700 bg-slate-900/80">
                        <div className="mb-3 flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Select Stocks</span>
                          <span className={`text-xs font-bold ${remaining < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                            Rem: {remaining.toLocaleString()}
                          </span>
                        </div>
                        <div className="space-y-2 max-h-60 overflow-y-auto custom-scrollbar pr-2">
                          {sectorStocks.map(stock => {
                            const isSelected = !!selectedStocks[stock.symbol];
                            return (
                              <div
                                key={stock.symbol}
                                className={`flex items-center justify-between p-3 rounded border cursor-pointer transition-colors ${isSelected ? 'bg-blue-900/30 border-blue-500/50' : 'bg-slate-800 border-slate-700 hover:border-slate-600'}`}
                                onClick={() => toggleStock(stock.symbol)}
                              >
                                <div className="flex items-center gap-3">
                                  <div className={`w-4 h-4 rounded border flex items-center justify-center ${isSelected ? 'bg-blue-500 border-blue-500' : 'border-slate-500'}`}>
                                    {isSelected && <Check size={12} className="text-white" />}
                                  </div>
                                  <div>
                                    <div className="font-bold text-sm text-slate-200">{stock.symbol}</div>
                                    <div className="text-xs text-slate-500">{stock.name}</div>
                                  </div>
                                </div>
                                <div className="text-right">
                                  {/* Percent Input */}
                                  {isSelected ? (
                                    <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                                      <input
                                        type="number"
                                        className="w-12 bg-slate-950 border border-slate-600 rounded px-1 py-0.5 text-right text-xs text-white focus:border-blue-500 outline-none"
                                        placeholder="%"
                                        value={selectedStocks[stock.symbol]?.weight || ''}
                                        onChange={(e) => {
                                          const val = parseFloat(e.target.value) || 0;
                                          handleDetailsChange(stock.symbol, 'weight', val);
                                        }}
                                      />
                                      <span className="text-xs text-slate-500">%</span>
                                    </div>
                                  ) : (
                                    <div className="text-xs text-slate-600 font-mono">
                                      NPR {marketData[stock.symbol]?.ltp ? marketData[stock.symbol].ltp : stock.price}
                                    </div>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                        <div className="mt-4 pt-3 border-t border-slate-700 flex justify-between items-center">
                          <div className="text-xs text-slate-400">
                            Total:  <span className="text-white font-bold">
                              {Object.keys(selectedStocks)
                                .filter(sym => nepaleseStocks[sectorName].find(s => s.symbol === sym))
                                .reduce((sum, sym) => sum + (selectedStocks[sym]?.weight || 0), 0)}%
                            </span>
                          </div>
                          <button
                            onClick={() => handleSaveAllocation(sectorName)}
                            className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs rounded shadow transition-colors flex items-center gap-1"
                          >
                            <Save size={12} /> Save
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Execution Targets */}
          {Object.keys(selectedStocks).filter(sym => selectedStocks[sym]).length > 0 && (
            <div className={`rounded-xl p-6 border transition-all duration-300 ${isLowBalance ? 'bg-red-900/10 border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.2)]' : 'bg-slate-800/50 border-slate-700'}`}>
              <div className="flex items-center gap-2 mb-6">
                <Rocket className={isLowBalance ? "text-red-400" : "text-yellow-400"} size={20} />
                <h3 className={`text-lg font-bold ${isLowBalance ? "text-red-400" : "text-emerald-400"}`}>
                  Execution Targets for Selected Stocks
                  {isLowBalance && <span className="ml-3 text-xs bg-red-500 text-white px-2 py-0.5 rounded-full animate-pulse">LOW BALANCE</span>}
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.keys(selectedStocks).filter(sym => selectedStocks[sym]).map(symbol => {
                  // Need to find stock in the nested structure
                  let stock = null;
                  let sectorName = '';
                  for (const [sec, stocks] of Object.entries(nepaleseStocks)) {
                    const found = stocks.find(s => s.symbol === symbol);
                    if (found) {
                      stock = found;
                      sectorName = sec;
                      break;
                    }
                  }
                  if (!stock) return null;

                  const details = selectedStocks[symbol];
                  if (!details) return null;

                  const livePrice = marketData[symbol]?.ltp || stock.price;
                  const entryPrice = details.purchasePrice || livePrice;
                  const targetPrice = details.targetPrice || Math.round(entryPrice * 1.1);

                  return (
                    <div key={symbol} className="bg-slate-900 rounded-lg p-5 border border-slate-700 relative overflow-hidden group hover:border-blue-500/50 transition-all">
                      <div className="absolute top-0 right-0 p-4 opacity-10 group-hover: opacity-20 transition-opacity">
                        <h1 className="text-6xl font-black text-slate-500">{symbol}</h1>
                      </div>

                      <div className="relative z-10">
                        <div className="flex justify-between items-start mb-6">
                          <div>
                            <h4 className="text-xl font-bold text-white flex items-center gap-2">
                              {symbol}
                              <span className="text-xs font-normal px-2 py-0.5 bg-slate-800 rounded-full text-slate-400 border border-slate-700">
                                {sectorName}
                              </span>
                            </h4>
                            <div className="text-sm text-slate-500">{stock.name}</div>
                          </div>
                          <div className="text-right">
                            <div className="text-xs text-slate-500 mb-1">Current Price</div>
                            <div className="text-xl font-bold text-yellow-400">
                              NPR {livePrice}
                            </div>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 bg-slate-950/50 rounded-lg p-4 mb-4 backdrop-blur-sm border border-slate-800/50">
                          <div>
                            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Purchase Price</div>
                            <div className="flex items-baseline gap-1">
                              <span className="text-slate-500 text-xs">NPR</span>
                              <input
                                type="number"
                                className="bg-transparent border-b border-slate-600 focus:border-blue-500 outline-none w-20 font-mono text-white text-lg"
                                value={details.purchasePrice || ''}
                                onChange={(e) => handleDetailsChange(symbol, 'purchasePrice', Number(e.target.value) || 0)}
                              />
                            </div>
                            <div className="text-[10px] text-slate-600 mt-1">Market execution</div>
                          </div>

                          <div>
                            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Purchase Qty</div>
                            <input
                              type="number"
                              placeholder="Qty"
                              className="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm w-full text-blue-400 font-bold focus:border-blue-500 outline-none"
                              value={details.purchaseQty || ''}
                              onChange={(e) => handleDetailsChange(symbol, 'purchaseQty', Number(e.target.value) || 0)}
                            />
                          </div>

                          <div>
                            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Target Sell Price</div>
                            <div className="flex items-baseline gap-1">
                              <span className="text-slate-500 text-xs">NPR</span>
                              <input
                                type="number"
                                className="bg-transparent border-b border-emerald-500/30 focus:border-emerald-500 outline-none w-20 font-mono text-emerald-400 font-bold text-lg"
                                value={details.targetPrice || Math.round((details.purchasePrice || livePrice) * 1.1)}
                                onChange={(e) => handleDetailsChange(symbol, 'targetPrice', Number(e.target.value) || 0)}
                              />
                            </div>
                          </div>

                          <div>
                            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Selling Qty</div>
                            <input
                              type="number"
                              placeholder="Qty"
                              className="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm w-full text-emerald-400 font-bold focus:border-emerald-500 outline-none"
                              value={details.sellingQty || ''}
                              onChange={(e) => handleDetailsChange(symbol, 'sellingQty', Number(e.target.value) || 0)}
                            />
                          </div>
                        </div>

                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-4">
                            <div>
                              <span className="block text-slate-600 mb-0.5">Planned Weight</span>
                              <span className="font-bold text-white">+{details.weight || 0}%</span>
                            </div>
                          </div>

                          <div className="flex-1 max-w-[120px]">
                            <div className="flex justify-between text-[10px] text-slate-500 mb-1">
                              <span>Entry</span>
                              <span>Target</span>
                            </div>
                            <div className="h-1. 5 bg-slate-800 rounded-full overflow-hidden flex">
                              <div className="w-1/3 bg-blue-500 rounded-full"></div>
                              <div className="w-2/3 bg-slate-700/30"></div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: RUNNING CALCULATIONS (STICKY) */}
        {/* Only show if a sector is expanded OR stocks are selected */}
        {(expandedSector || Object.keys(selectedStocks).filter(sym => selectedStocks[sym]).length > 0) && (
          <div className="w-full lg:w-80 transition-all duration-300 animate-in slide-in-from-right">
            <div className="sticky top-6 space-y-4">
              <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden shadow-xl">
                <div className="px-4 py-3 bg-slate-900 border-b border-slate-700 flex items-center justify-between">
                  <h4 className="font-bold text-slate-300 flex items-center gap-2">
                    <Calculator size={16} className="text-blue-400" />
                    Running Calc
                  </h4>
                  <div className="text-[10px] uppercase font-bold text-slate-500 bg-slate-800 px-2 py-0.5 rounded">
                    Live
                  </div>
                </div>

                <div className="p-4 space-y-4">
                  {/* Summary Block */}
                  <div className="space-y-2">
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-slate-400">Total Equity</span>
                      <span className="font-bold text-white">NPR {totalEquity?.toLocaleString()}</span>
                    </div>
                    <div className="w-full bg-slate-700/50 h-1 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 transition-all duration-500"
                        style={{ width: '100%' }}
                      ></div>
                    </div>
                  </div>

                  <div className="border-t border-slate-700 my-2"></div>

                  {/* Sector Breakdown */}
                  <div className="space-y-3">
                    {Object.keys(nepaleseStocks).map((sectorName, idx) => {
                      const { allocatedAmount, sectorSpent, remaining } = calculateSectorStats(sectorName);
                      // Use saved allocation or default.  If user hasn't allocated, default is 0 unless set in year. 
                      const sectorConfig = year.allocation?.find(s => s.sector === sectorName);
                      const percent = getEffectiveSectorPercent(sectorName);

                      if (percent === 0 && sectorSpent === 0) return null; // Only hide if 0% allocated AND 0 spent

                      const progress = allocatedAmount > 0 ? Math.min((sectorSpent / allocatedAmount) * 100, 100) : 0;

                      return (
                        <div key={idx} className="space-y-1">
                          <div className="flex justify-between items-center text-xs">
                            <span className="text-slate-300 font-medium">{sectorName}</span>
                            <span className="text-slate-500">{percent}%</span>
                          </div>
                          <div className="flex justify-between items-center text-[10px]">
                            <span className="text-slate-500">Alloc: {allocatedAmount.toLocaleString()}</span>
                            <span className={`${remaining < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                              Rem: {remaining.toLocaleString()}
                            </span>
                          </div>
                          <div className="w-full bg-slate-700 h-1 rounded-full overflow-hidden">
                            <div
                              className={`h-full transition-all duration-500 ${remaining < 0 ? 'bg-red-500' : 'bg-emerald-500'}`}
                              style={{ width: `${progress}%` }}
                            ></div>
                          </div>

                          {/* Detailed Stock Breakdown */}
                          <div className="space-y-0. 5 pt-1">
                            {(nepaleseStocks[sectorName] || []).filter(s => selectedStocks[s.symbol]).map(stock => {
                              const details = selectedStocks[stock.symbol];
                              if (!details) return null;

                              const price = Number(details.purchasePrice) || 0;
                              const qty = Number(details.purchaseQty) || 0;
                              const total = price * qty;

                              if (qty === 0) return null;

                              return (
                                <div key={stock.symbol} className="flex justify-between items-center text-[9px] text-slate-400 pl-2 border-l border-slate-700 ml-1">
                                  <span>
                                    <span className="text-slate-300 font-semibold">{stock.symbol}</span>:  {qty} x {price.toLocaleString()}
                                  </span>
                                  <span>{total.toLocaleString()}</span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <div className="border-t border-slate-700 my-2"></div>

                  {/* Total Summary */}
                  <div className="bg-slate-900/50 rounded-lg p-3 space-y-2 border border-slate-700/50">
                    <div className="flex justify-between items-center text-xs text-slate-400">
                      <span>Total Allocated</span>
                      <span>{Object.keys(nepaleseStocks).reduce((acc, sector) => acc + getEffectiveSectorPercent(sector), 0)}%</span>
                    </div>
                    <div className="flex justify-between items-center text-sm font-bold">
                      <span className={isLowBalance ? "text-red-400" : "text-blue-400"}>Rem Balance</span>
                      <span className={isLowBalance ? "text-red-400" : "text-white"}>
                        NPR {remainingBalance.toLocaleString()}
                      </span>
                    </div>

                    <div className="flex justify-between items-center text-xs pt-1 border-t border-slate-700/50">
                      <span className="text-slate-500">Protected Equity</span>
                      <span className="text-emerald-500 font-bold">
                        NPR {(remainingBalance - (remainingBalance * (riskPercentage || 0) / 100)).toLocaleString()}
                      </span>
                    </div>

                    {/* MARKET CALENDAR SECTION REMOVED FROM HERE */}
                    {/* MARKET CALENDAR SECTION REMOVED */}
                  </div>
                </div>
              </div>

              {/* NEW STANDALONE NEPSE CALENDAR SECTION */}
              <div className="w-full animate-in slide-in-from-right delay-200">
                <NepaliCalendarWidget />
              </div>
            </div>
          </div>
        )}


      </div>

      {/* Helper Component defined in same file for modularity */}
      {/* Helper Component moved to end of file */}

      {/* Save Action Button for this section */}
      {
        Object.keys(selectedStocks).filter(sym => selectedStocks[sym]).length > 0 && (
          <div className="flex justify-end mt-6"> {/* Added mt-6 for spacing */}
            <button
              onClick={() => handleSaveAllocation('all')} // Changed to 'all' or specific sector if needed
              className={`bg-blue-600 hover: bg-blue-500 text-white px-8 py-3 rounded-xl font-bold shadow-lg transition-all flex items-center gap-2 ${isSaved ? 'bg-emerald-500 hover:bg-emerald-400' : ''}`}
            >
              {isSaved ? '✅ Allocation Saved' : '💾 Save Allocation'}
            </button>
          </div>
        )
      }

      {/* 3.  ORIGINAL STATIC VIEW (Same as your provided code) */}
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

        {year.allocation && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
              🛡️ Portfolio Allocation (Reference)
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

        {year.strategy && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-2">Strategy</h3>
            <p className="text-lg text-slate-300">{year.strategy}</p>
          </div>
        )}

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

        <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-start gap-3">
          <span className="text-amber-400 mt-1 text-xl">⚠️</span>
          <div>
            <div className="font-semibold text-amber-300 mb-1">Key Action</div>
            <div className="text-slate-300">{year.action}</div>
          </div>
        </div>
      </div>

      {
        currentYear === totalYears && (
          <div className="bg-gradient-to-r from-emerald-500/20 to-blue-500/20 border border-emerald-500/30 rounded-xl p-8 text-center">
            <div className="text-6xl mb-4">✅</div>
            <h3 className="text-2xl font-bold mb-2">Target Achieved!</h3>
            <p className="text-xl text-emerald-400 font-semibold mb-2">≈ NPR 400,000+</p>
            <p className="text-slate-300">Exit or continue your SIP cycle for further growth</p>
          </div>
        )
      }
    </div >
  );
};

export default YearDetails;