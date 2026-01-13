import React, { useState, useEffect } from 'react';
import { TrendingUp, DollarSign, Shield, Target, AlertCircle, Edit2, Save, X, Plus, Trash2, ArrowRight } from 'lucide-react';
import LoginRegistrationModal from './LoginRegistrationModal';

export default function PMSPortfolioPage({ onContinue, onLoginSuccess }) {
    const [isEditingBudget, setIsEditingBudget] = useState(false);
    const [isEditingRisk, setIsEditingRisk] = useState(false);
    const [isEditingCategories, setIsEditingCategories] = useState(false);
    const [newCategory, setNewCategory] = useState('');

    // Login Modal State
    const [showLoginModal, setShowLoginModal] = useState(false);

    const [portfolioData, setPortfolioData] = useState({
        totalBudget: 1000000,
        riskTolerance: 25,
        selectedCategories: ['Banking', 'Hydropower', 'Insurance'],
        stocks: [
            {
                id: 1,
                name: 'NABIL',
                category: 'Banking',
                purchasePrice: 100,
                targetSellPrice: 110,
                currentPrice: 105
            },
            {
                id: 2,
                name: 'CHCL',
                category: 'Hydropower',
                purchasePrice: 450,
                targetSellPrice: 500,
                currentPrice: 465
            },
            {
                id: 3,
                name: 'NICL',
                category: 'Insurance',
                purchasePrice: 850,
                targetSellPrice: 900,
                currentPrice: 870
            }
        ]
    });

    const [tempBudget, setTempBudget] = useState(portfolioData.totalBudget);
    const [tempRisk, setTempRisk] = useState(portfolioData.riskTolerance);
    const [editingStockId, setEditingStockId] = useState(null);
    const [tempStockData, setTempStockData] = useState({});

    const calculatePercentage = (purchase, target) => {
        return (((target - purchase) / purchase) * 100).toFixed(2);
    };

    const calculateRiskAmount = () => {
        return (portfolioData.totalBudget * portfolioData.riskTolerance) / 100;
    };

    const getProgressPercentage = (current, purchase, target) => {
        const progress = ((current - purchase) / (target - purchase)) * 100;
        return Math.min(Math.max(progress, 0), 100);
    };

    const handleSaveBudget = () => {
        setPortfolioData({ ...portfolioData, totalBudget: tempBudget });
        setIsEditingBudget(false);
    };

    const handleSaveRisk = () => {
        setPortfolioData({ ...portfolioData, riskTolerance: tempRisk });
        setIsEditingRisk(false);
    };

    const handleAddCategory = () => {
        if (newCategory.trim()) {
            setPortfolioData({
                ...portfolioData,
                selectedCategories: [...portfolioData.selectedCategories, newCategory.trim()]
            });
            setNewCategory('');
        }
    };

    const handleRemoveCategory = (category) => {
        setPortfolioData({
            ...portfolioData,
            selectedCategories: portfolioData.selectedCategories.filter(c => c !== category)
        });
    };

    const handleEditStock = (stock) => {
        setEditingStockId(stock.id);
        setTempStockData({ ...stock });
    };

    const handleSaveStock = () => {
        setPortfolioData({
            ...portfolioData,
            stocks: portfolioData.stocks.map(s =>
                s.id === editingStockId ? tempStockData : s
            )
        });
        setEditingStockId(null);
        setTempStockData({});
    };

    const handleCancelEdit = () => {
        setEditingStockId(null);
        setTempStockData({});
    };

    const handleDeleteStock = (stockId) => {
        setPortfolioData({
            ...portfolioData,
            stocks: portfolioData.stocks.filter(s => s.id !== stockId)
        });
    };

    const handleAddStock = () => {
        const newStock = {
            id: Date.now(),
            name: 'NEW STOCK',
            category: portfolioData.selectedCategories[0] || 'Uncategorized',
            purchasePrice: 100,
            targetSellPrice: 110,
            currentPrice: 100
        };
        setPortfolioData({
            ...portfolioData,
            stocks: [...portfolioData.stocks, newStock]
        });
        setEditingStockId(newStock.id);
        setTempStockData(newStock);
    };

    // Live Market Data State
    const [marketData, setMarketData] = useState({});
    const [isSaving, setIsSaving] = useState(false);

    // Fetch Live Market Data
    useEffect(() => {
        const fetchMarketData = async () => {
            try {
                const res = await fetch('http://localhost:8002/api/market');
                const data = await res.json();
                // Transform list to dict for fast lookup: { "NABIL": { ltp: 1234, ... } }
                const lookup = {};
                if (data.stocks) {
                    // Start thinking about "stocks" as dictionary based on scraper structure
                    // If data.stocks is dict:
                    if (!Array.isArray(data.stocks)) {
                        Object.assign(lookup, data.stocks); // scraper returns dict mapping symbol -> data
                    } else {
                        // If it's list
                        data.stocks.forEach(s => lookup[s.symbol] = s);
                    }
                }
                setMarketData(lookup);

                // Live update current prices in portfolio
                setPortfolioData(prev => ({
                    ...prev,
                    stocks: prev.stocks.map(stock => {
                        const live = lookup[stock.name];
                        return live ? { ...stock, currentPrice: live.ltp || stock.currentPrice } : stock;
                    })
                }));
            } catch (err) {
                console.error("Failed to fetch market data:", err);
            }
        };

        fetchMarketData();
        const interval = setInterval(fetchMarketData, 5000);
        return () => clearInterval(interval);
    }, []);

    // Handle the proceed button click - Save to Backend THEN show login
    const handleProceedClick = async () => {
        setIsSaving(true);
        try {
            // Prepare payload for backend
            // We tag this as "WEEKLY" strategy to satisfy signal engine requirement
            const payload = {
                user_id: "guest_user", // This would normally come from auth context
                period: "WEEKLY",
                portfolio: portfolioData
            };

            const res = await fetch('http://localhost:8002/api/user/trading-config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                console.log("Portfolio configuration saved!");
            } else {
                console.warn("Failed to save configuration via API");
            }
        } catch (e) {
            console.error("Error saving portfolio:", e);
        } finally {
            setIsSaving(false);
            setShowLoginModal(true);
        }
    };

    // Handle successful login/registration
    const handleLoginSuccess = () => {
        setShowLoginModal(false);
        // Sync global auth state
        if (onLoginSuccess) {
            onLoginSuccess();
        } else if (onContinue) {
            // Fallback for independent usage
            onContinue();
        }
    };

    return (
        <div className="space-y-6">
            {/* Login/Registration Modal */}
            <LoginRegistrationModal
                isOpen={showLoginModal}
                onClose={() => setShowLoginModal(false)}
                onSuccess={handleLoginSuccess}
            />

            <div className="text-center mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">Step 2: Setup Your Portfolio</h1>
                <p className="text-slate-400">Define your investment budget and current holdings</p>
            </div>

            {/* Section 1: Investment Overview */}
            <div className="grid md:grid-cols-2 gap-6">
                {/* Total Budget Card */}
                <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-2xl p-6 shadow-2xl">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div className="bg-white/20 p-3 rounded-xl">
                                <DollarSign className="w-6 h-6 text-white" />
                            </div>
                            <h2 className="text-xl font-semibold text-white">Total Investment Budget</h2>
                        </div>
                        <button
                            onClick={() => setIsEditingBudget(!isEditingBudget)}
                            className="bg-white/20 hover:bg-white/30 p-2 rounded-lg transition-all"
                        >
                            <Edit2 className="w-5 h-5 text-white" />
                        </button>
                    </div>

                    {isEditingBudget ? (
                        <div className="space-y-3">
                            <input
                                type="number"
                                value={tempBudget}
                                onChange={(e) => setTempBudget(Number(e.target.value))}
                                className="w-full bg-white/20 text-white text-2xl font-bold px-4 py-3 rounded-lg border-2 border-white/40 focus:outline-none focus:border-white"
                            />
                            <div className="flex gap-2">
                                <button
                                    onClick={handleSaveBudget}
                                    className="flex-1 bg-white text-blue-600 px-4 py-2 rounded-lg font-semibold hover:bg-blue-50 transition-all flex items-center justify-center gap-2"
                                >
                                    <Save className="w-4 h-4" /> Save
                                </button>
                                <button
                                    onClick={() => setIsEditingBudget(false)}
                                    className="flex-1 bg-white/20 text-white px-4 py-2 rounded-lg font-semibold hover:bg-white/30 transition-all"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    ) : (
                        <>
                            <p className="text-5xl font-bold text-white mb-2">
                                NPR {portfolioData.totalBudget.toLocaleString()}
                            </p>
                            <p className="text-blue-100">Available for investment</p>
                        </>
                    )}
                </div>

                {/* Risk Tolerance Card */}
                <div className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-2xl p-6 shadow-2xl">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div className="bg-white/20 p-3 rounded-xl">
                                <Shield className="w-6 h-6 text-white" />
                            </div>
                            <h2 className="text-xl font-semibold text-white">Risk Tolerance</h2>
                        </div>
                        <button
                            onClick={() => setIsEditingRisk(!isEditingRisk)}
                            className="bg-white/20 hover:bg-white/30 p-2 rounded-lg transition-all"
                        >
                            <Edit2 className="w-5 h-5 text-white" />
                        </button>
                    </div>

                    {isEditingRisk ? (
                        <div className="space-y-3">
                            <div className="space-y-2">
                                <input
                                    type="range"
                                    min="0"
                                    max="100"
                                    value={tempRisk}
                                    onChange={(e) => setTempRisk(Number(e.target.value))}
                                    className="w-full"
                                />
                                <input
                                    type="number"
                                    value={tempRisk}
                                    onChange={(e) => setTempRisk(Number(e.target.value))}
                                    className="w-full bg-white/20 text-white text-2xl font-bold px-4 py-3 rounded-lg border-2 border-white/40 focus: outline-none focus: border-white"
                                    min="0"
                                    max="100"
                                />
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={handleSaveRisk}
                                    className="flex-1 bg-white text-purple-600 px-4 py-2 rounded-lg font-semibold hover:bg-purple-50 transition-all flex items-center justify-center gap-2"
                                >
                                    <Save className="w-4 h-4" /> Save
                                </button>
                                <button
                                    onClick={() => setIsEditingRisk(false)}
                                    className="flex-1 bg-white/20 text-white px-4 py-2 rounded-lg font-semibold hover:bg-white/30 transition-all"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    ) : (
                        <>
                            <div className="flex items-baseline gap-4 mb-2">
                                <p className="text-5xl font-bold text-white">{portfolioData.riskTolerance}%</p>
                                <p className="text-2xl font-semibold text-purple-100">
                                    NPR {calculateRiskAmount().toLocaleString()}
                                </p>
                            </div>
                            <p className="text-purple-100">Maximum risk capacity</p>
                        </>
                    )}
                </div>
            </div>

            {/* Section 2: Selected Categories & Stocks */}
            <div className="bg-slate-800/50 backdrop-blur-lg rounded-2xl p-6 shadow-2xl border border-slate-700">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Target className="w-6 h-6 text-emerald-400" />
                        Selected Investment Portfolio
                    </h2>
                    <button
                        onClick={() => setIsEditingCategories(!isEditingCategories)}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg transition-all flex items-center gap-2"
                    >
                        <Edit2 className="w-4 h-4" />
                        {isEditingCategories ? 'Done' : 'Edit Categories'}
                    </button>
                </div>

                {/* Categories */}
                <div className="mb-6">
                    <p className="text-slate-400 text-sm mb-3">Investment Categories</p>
                    <div className="flex flex-wrap gap-3">
                        {portfolioData.selectedCategories.map((category, idx) => (
                            <span
                                key={idx}
                                className="px-4 py-2 bg-emerald-600/20 text-emerald-300 rounded-lg border border-emerald-600/40 font-medium flex items-center gap-2"
                            >
                                {category}
                                {isEditingCategories && (
                                    <button
                                        onClick={() => handleRemoveCategory(category)}
                                        className="hover:bg-red-500/20 rounded p-1 transition-all"
                                    >
                                        <X className="w-4 h-4" />
                                    </button>
                                )}
                            </span>
                        ))}

                        {isEditingCategories && (
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={newCategory}
                                    onChange={(e) => setNewCategory(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && handleAddCategory()}
                                    placeholder="New category"
                                    className="px-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:outline-none focus:border-emerald-500"
                                />
                                <button
                                    onClick={handleAddCategory}
                                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-all"
                                >
                                    <Plus className="w-5 h-5" />
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* Stock Count */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-slate-300">
                        <AlertCircle className="w-5 h-5" />
                        <p>{portfolioData.stocks.length} stocks selected for trading</p>
                    </div>
                    <button
                        onClick={handleAddStock}
                        className="bg-blue-600 hover: bg-blue-700 text-white px-4 py-2 rounded-lg transition-all flex items-center gap-2"
                    >
                        <Plus className="w-4 h-4" />
                        Add Stock
                    </button>
                </div>
            </div>

            {/* Section 3: Trading Rules */}
            <div className="bg-slate-800/50 backdrop-blur-lg rounded-2xl p-6 shadow-2xl border border-slate-700">
                <h2 className="text-2xl font-bold text-white mb-6">Trading Rules & Target Prices</h2>

                <div className="space-y-4">
                    {portfolioData.stocks.map((stock) => {
                        const isEditing = editingStockId === stock.id;
                        const displayStock = isEditing ? tempStockData : stock;
                        const percentChange = calculatePercentage(displayStock.purchasePrice, displayStock.targetSellPrice);
                        const priceChange = displayStock.targetSellPrice - displayStock.purchasePrice;
                        const progress = getProgressPercentage(displayStock.currentPrice, displayStock.purchasePrice, displayStock.targetSellPrice);

                        return (
                            <div
                                key={stock.id}
                                className="bg-slate-900/50 rounded-xl p-6 border border-slate-700 hover:border-slate-600 transition-all"
                            >
                                {/* Stock Header */}
                                <div className="flex items-center justify-between mb-6">
                                    <div className="flex-1">
                                        {isEditing ? (
                                            <input
                                                type="text"
                                                value={tempStockData.name}
                                                onChange={(e) => setTempStockData({ ...tempStockData, name: e.target.value })}
                                                className="text-2xl font-bold bg-slate-800 text-white px-3 py-2 rounded-lg border border-slate-600 focus:outline-none focus:border-blue-500 mb-2"
                                            />
                                        ) : (
                                            <h3 className="text-2xl font-bold text-white mb-1">{displayStock.name}</h3>
                                        )}

                                        {isEditing ? (
                                            <select
                                                value={tempStockData.category}
                                                onChange={(e) => setTempStockData({ ...tempStockData, category: e.target.value })}
                                                className="text-sm bg-slate-800 text-white px-3 py-1 rounded-full border border-slate-600 focus:outline-none focus:border-blue-500"
                                            >
                                                {portfolioData.selectedCategories.map((cat) => (
                                                    <option key={cat} value={cat}>{cat}</option>
                                                ))}
                                            </select>
                                        ) : (
                                            <span className="text-sm text-slate-400 bg-slate-800 px-3 py-1 rounded-full">
                                                {displayStock.category}
                                            </span>
                                        )}
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <div className="text-right mr-4">
                                            <p className="text-sm text-slate-400 mb-1">Current Price</p>
                                            {isEditing ? (
                                                <input
                                                    type="number"
                                                    value={tempStockData.currentPrice}
                                                    onChange={(e) => setTempStockData({ ...tempStockData, currentPrice: Number(e.target.value) })}
                                                    className="text-xl font-bold bg-slate-800 text-amber-400 px-3 py-1 rounded-lg border border-slate-600 focus:outline-none focus:border-blue-500 w-32 text-right"
                                                />
                                            ) : (
                                                <p className="text-2xl font-bold text-amber-400">NPR {displayStock.currentPrice}</p>
                                            )}
                                        </div>

                                        {isEditing ? (
                                            <>
                                                <button
                                                    onClick={handleSaveStock}
                                                    className="bg-emerald-600 hover:bg-emerald-700 text-white p-2 rounded-lg transition-all"
                                                >
                                                    <Save className="w-5 h-5" />
                                                </button>
                                                <button
                                                    onClick={handleCancelEdit}
                                                    className="bg-slate-700 hover:bg-slate-600 text-white p-2 rounded-lg transition-all"
                                                >
                                                    <X className="w-5 h-5" />
                                                </button>
                                            </>
                                        ) : (
                                            <>
                                                <button
                                                    onClick={() => handleEditStock(stock)}
                                                    className="bg-blue-600 hover: bg-blue-700 text-white p-2 rounded-lg transition-all"
                                                >
                                                    <Edit2 className="w-5 h-5" />
                                                </button>
                                                <button
                                                    onClick={() => handleDeleteStock(stock.id)}
                                                    className="bg-red-600 hover:bg-red-700 text-white p-2 rounded-lg transition-all"
                                                >
                                                    <Trash2 className="w-5 h-5" />
                                                </button>
                                            </>
                                        )}
                                    </div>
                                </div>

                                {/* Price Metrics */}
                                <div className="grid grid-cols-3 gap-4 mb-6">
                                    <div className="bg-slate-800/50 rounded-lg p-4">
                                        <p className="text-slate-400 text-sm mb-2">Purchase Price</p>
                                        {isEditing ? (
                                            <input
                                                type="number"
                                                value={tempStockData.purchasePrice}
                                                onChange={(e) => setTempStockData({ ...tempStockData, purchasePrice: Number(e.target.value) })}
                                                className="w-full text-xl font-bold bg-slate-700 text-white px-3 py-2 rounded-lg border border-slate-600 focus:outline-none focus:border-blue-500"
                                            />
                                        ) : (
                                            <p className="text-2xl font-bold text-white">NPR {displayStock.purchasePrice}</p>
                                        )}
                                    </div>

                                    <div className="bg-emerald-900/30 rounded-lg p-4 border border-emerald-700/50">
                                        <p className="text-emerald-300 text-sm mb-2">Target Sell Price</p>
                                        {isEditing ? (
                                            <input
                                                type="number"
                                                value={tempStockData.targetSellPrice}
                                                onChange={(e) => setTempStockData({ ...tempStockData, targetSellPrice: Number(e.target.value) })}
                                                className="w-full text-xl font-bold bg-emerald-950/50 text-emerald-400 px-3 py-2 rounded-lg border border-emerald-700 focus:outline-none focus:border-emerald-500"
                                            />
                                        ) : (
                                            <p className="text-2xl font-bold text-emerald-400">NPR {displayStock.targetSellPrice}</p>
                                        )}
                                    </div>

                                    <div className="bg-blue-900/30 rounded-lg p-4 border border-blue-700/50">
                                        <p className="text-blue-300 text-sm mb-2">Target Gain</p>
                                        <div className="flex items-center gap-2">
                                            <TrendingUp className="w-5 h-5 text-blue-400" />
                                            <p className="text-2xl font-bold text-blue-400">+{percentChange}%</p>
                                        </div>
                                        <p className="text-sm text-blue-300 mt-1">NPR +{priceChange}</p>
                                    </div>
                                </div>

                                {/* Progress Bar */}
                                <div className="space-y-2">
                                    <div className="flex justify-between items-center">
                                        <p className="text-sm text-slate-400">Progress to Target</p>
                                        <p className="text-sm font-semibold text-slate-300">{progress.toFixed(1)}%</p>
                                    </div>
                                    <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full transition-all duration-500"
                                            style={{ width: `${progress}%` }}
                                        />
                                    </div>
                                    <div className="flex justify-between text-xs text-slate-500">
                                        <span>Bought:  NPR {displayStock.purchasePrice}</span>
                                        <span>Target: NPR {displayStock.targetSellPrice}</span>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Summary Footer */}
            <div className="bg-slate-800/30 rounded-xl p-6 border border-slate-700 text-center flex flex-col items-center gap-4">
                <p className="text-slate-400 text-sm">
                    Portfolio tracking {portfolioData.stocks.length} stocks across {portfolioData.selectedCategories.length} categories
                </p>

                {/* Proceed Button - Now triggers login modal */}
                <button
                    onClick={handleProceedClick}
                    className="bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white px-8 py-3 rounded-xl font-bold text-lg shadow-lg flex items-center gap-2 transform transition-all hover:scale-105"
                >
                    Save & Proceed to Goal Selection <ArrowRight className="w-5 h-5" />
                </button>
            </div>
        </div>
    );
}