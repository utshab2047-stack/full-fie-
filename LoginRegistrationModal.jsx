import React, { useState, useEffect } from 'react';
import { X, Upload, ScanLine, Check, Mail, Smartphone, ArrowRight, FileText, AlertCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8002/api';

const inputClass = "w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white outline-none focus:border-blue-500";

async function apiCall(endpoint, method, body) {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        return data;
    } catch (e) {
        console.error("API Error:", e);
        return { ok: false, error: "Network error. Is the backend running?" };
    }
}

export default function LoginRegistrationModal({ isOpen, onClose, onSuccess }) {
    const [activeTab, setActiveTab] = useState('register');
    const [step, setStep] = useState('form');
    const [loading, setLoading] = useState(false);
    const [ocrScanning, setOcrScanning] = useState(false);

    const [formData, setFormData] = useState({
        firstName: '',
        middleName: '',
        lastName: '',
        email: '',
        phone: '',
        password: '',
        citizenshipNo: '',
        placeOfIssue: '',
        dateOfIssue: '',
        fatherName: '',
        motherName: '',
        dob: ''
    });

    const [verificationCodes, setVerificationCodes] = useState({
        email: '',
        phone: ''
    });

    // Login State
    const [loginCredentials, setLoginCredentials] = useState({ username: '', password: '' });
    const [loginError, setLoginError] = useState('');

    const [docs, setDocs] = useState({
        citizenshipFront: null,
        citizenshipBack: null,
        nidFront: null,
        nidBack: null
    });

    if (!isOpen) return null;

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleFileChange = (e, docType) => {
        const file = e.target.files[0];
        if (file) {
            setDocs(prev => ({ ...prev, [docType]: URL.createObjectURL(file) }));
        }
    };

    const canScan = Object.values(docs).some(doc => doc !== null);

    const handleScanDocs = () => {
        if (!canScan) return;
        setOcrScanning(true);

        setTimeout(() => {
            setOcrScanning(false);
            setFormData(prev => ({
                ...prev,
                firstName: 'Ram',
                middleName: 'Bahadur',
                lastName: 'Thapa',
                citizenshipNo: '12-01-75-00123',
                placeOfIssue: 'Kathmandu',
                dateOfIssue: '2075-01-15',
                fatherName: 'Hari Bahadur Thapa',
                motherName: 'Sita Thapa',
                dob: '2050-05-10',
                email: prev.email || 'ram.thapa@example.com',
                phone: prev.phone || '9841000000'
            }));
        }, 2500);
    };

    const handleSubmitForm = async (e) => {
        e.preventDefault();
        setLoading(true);

        const fullName = [formData.firstName, formData.middleName, formData.lastName].filter(Boolean).join(' ');

        const res = await apiCall('/auth/register', 'POST', {
            email: formData.email,
            password: formData.password,
            phone: formData.phone,
            full_name: fullName
        });

        setLoading(false);

        if (res.ok) {
            setStep('verification');
        } else {
            alert(res.error || "Registration failed. Please try again.");
        }
    };

    const handleVerify = async () => {
        const code = verificationCodes.email || verificationCodes.phone;

        if (code.length < 4) {
            alert('Please enter the verification code.');
            return;
        }

        setLoading(true);

        const res = await apiCall('/auth/verify', 'POST', {
            email: formData.email,
            code: code
        });

        setLoading(false);

        if (res.ok) {
            setStep('success');
            setTimeout(() => {
                onSuccess();
            }, 1500);
        } else {
            alert(res.error || "Invalid verification code.");
        }
    };

    const handleLoginSubmit = async (e) => {
        e.preventDefault();
        setLoginError('');
        setLoading(true);

        const res = await apiCall('/auth/login', 'POST', {
            email: loginCredentials.username,
            password: loginCredentials.password
        });

        setLoading(false);

        if (res.ok) {
            setStep('success');
            setTimeout(() => {
                onSuccess();
            }, 1000);
        } else {
            setLoginError(res.error || "Invalid credentials.");
        }
    };

    const UploadZone = ({ title, docType, file }) => (
        <div className="relative group">
            <div className={`
                border-2 border-dashed rounded-xl p-4 text-center transition-all h-32 flex flex-col items-center justify-center
                ${file
                    ? 'border-emerald-500/50 bg-emerald-500/10'
                    : 'border-slate-700 hover:border-blue-500 bg-slate-800/30'
                }
            `}>
                <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => handleFileChange(e, docType)}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                />

                {file ? (
                    <>
                        <img src={file} alt={title} className="absolute inset-0 w-full h-full object-cover rounded-xl opacity-40" />
                        <div className="z-20 flex items-center gap-2 text-emerald-400 font-medium bg-slate-900/80 px-3 py-1 rounded-full">
                            <Check size={14} /> Uploaded
                        </div>
                    </>
                ) : (
                    <>
                        <Upload className="w-6 h-6 text-slate-400 mb-2 group-hover:text-blue-400 transition-colors" />
                        <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">{title}</span>
                    </>
                )}
            </div>
        </div>
    );

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="bg-slate-900 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-slate-700 shadow-2xl animate-in fade-in zoom-in duration-300 custom-scrollbar">

                {/* Header */}
                <div className="sticky top-0 z-10 bg-slate-900/95 backdrop-blur border-b border-slate-800 p-6 flex justify-between items-center">
                    <div>
                        <div className="flex items-baseline gap-3">
                            <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
                                {step === 'verification' ? 'Verify Identity' : 'Secure Access'}
                            </h2>
                            <HeaderDateWidget />
                        </div>
                        <p className="text-slate-400 text-sm mt-1">
                            {step === 'verification'
                                ? 'Enter code sent to your email (Check Console)'
                                : 'One account for everything'}
                        </p>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-slate-800 rounded-full transition-colors text-slate-400 hover:text-white">
                        <X size={24} />
                    </button>
                </div>

                <div className="p-6">
                    {step === 'success' ? (
                        <div className="text-center py-12">
                            <div className="w-20 h-20 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                                <Check className="w-10 h-10 text-emerald-400" />
                            </div>
                            <h3 className="text-2xl font-bold text-white mb-2">Login Successful!</h3>
                            <p className="text-slate-400">Welcome back to your dashboard.</p>
                        </div>
                    ) : step === 'verification' ? (
                        <div className="space-y-6">
                            <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4 mb-6">
                                <p className="text-blue-200 text-sm text-center">
                                    Verification code sent to <strong>{formData.email}</strong>
                                    <br /><span className="text-xs opacity-70">(Check the backend console for the code)</span>
                                </p>
                            </div>

                            <div className="grid md:grid-cols-2 gap-6">
                                <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700">
                                    <div className="flex items-center gap-3 mb-4 text-emerald-400">
                                        <Mail size={20} />
                                        <span className="font-semibold">Email Code</span>
                                    </div>
                                    <input
                                        type="text"
                                        placeholder="XXXXXX"
                                        maxLength={6}
                                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-center text-xl tracking-widest text-white focus:ring-2 focus:ring-emerald-500 outline-none"
                                        value={verificationCodes.email}
                                        onChange={(e) => setVerificationCodes(prev => ({ ...prev, email: e.target.value }))}
                                    />
                                </div>
                            </div>

                            <button
                                onClick={handleVerify}
                                disabled={loading}
                                className="w-full mt-6 py-4 bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 text-white font-bold rounded-xl shadow-lg transition-transform hover:scale-[1.02] flex items-center justify-center gap-2"
                            >
                                {loading ? 'Verifying...' : 'Verify & Continue'} <ArrowRight size={20} />
                            </button>
                        </div>
                    ) : (
                        <>
                            {/* Tabs */}
                            <div className="flex p-1 bg-slate-800/50 rounded-lg mb-6">
                                {['login', 'register'].map((tab) => (
                                    <button
                                        key={tab}
                                        onClick={() => setActiveTab(tab)}
                                        className={`flex-1 py-2.5 text-sm font-medium rounded-md transition-all ${activeTab === tab
                                            ? 'bg-slate-700 text-white shadow-sm'
                                            : 'text-slate-400 hover:text-slate-300'
                                            }`}
                                    >
                                        {tab === 'login' ? 'Existing User' : 'New Registration'}
                                    </button>
                                ))}
                            </div>

                            {activeTab === 'login' ? (
                                <form onSubmit={handleLoginSubmit} className="py-4 space-y-6">
                                    <div className="space-y-4">
                                        <div className="space-y-2">
                                            <label className="text-sm font-semibold text-slate-400">Email Address</label>
                                            <div className="relative">
                                                <input
                                                    type="email"
                                                    value={loginCredentials.username}
                                                    onChange={(e) => setLoginCredentials(prev => ({ ...prev, username: e.target.value }))}
                                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 pl-10 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                                    placeholder="Enter email"
                                                />
                                                <div className="absolute left-3 top-3.5 text-slate-500">
                                                    <Mail size={18} />
                                                </div>
                                            </div>
                                        </div>

                                        <div className="space-y-2">
                                            <label className="text-sm font-semibold text-slate-400">Password</label>
                                            <div className="relative">
                                                <input
                                                    type="password"
                                                    value={loginCredentials.password}
                                                    onChange={(e) => setLoginCredentials(prev => ({ ...prev, password: e.target.value }))}
                                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 pl-10 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                                    placeholder="Enter password"
                                                />
                                                <div className="absolute left-3 top-3.5 text-slate-500">
                                                    <AlertCircle size={18} />
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {loginError && (
                                        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2 text-red-400 text-sm">
                                            <AlertCircle size={16} />
                                            {loginError}
                                        </div>
                                    )}

                                    <button
                                        type="submit"
                                        disabled={loading}
                                        className="w-full py-4 bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 text-white font-bold rounded-xl shadow-lg transition-all active:scale-[0.98]"
                                    >
                                        {loading ? 'Authenticating...' : 'Secure Login'}
                                    </button>

                                    <div className="text-center">
                                        <p className="text-slate-400 text-sm">Don't have an account?</p>
                                        <button type="button" onClick={() => setActiveTab('register')} className="mt-1 text-emerald-400 hover:text-emerald-300 font-medium hover:underline">Create New Registration</button>
                                    </div>
                                </form>
                            ) : (
                                <form onSubmit={handleSubmitForm} className="space-y-6">

                                    {/* Document Upload Grid */}
                                    <div className="space-y-4">
                                        <div>
                                            <h4 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
                                                <FileText size={16} className="text-blue-400" /> Citizenship Certificate
                                            </h4>
                                            <div className="grid grid-cols-2 gap-4">
                                                <UploadZone title="Front Side" docType="citizenshipFront" file={docs.citizenshipFront} />
                                                <UploadZone title="Back Side" docType="citizenshipBack" file={docs.citizenshipBack} />
                                            </div>
                                        </div>
                                    </div>

                                    {/* Scan/Action Button */}
                                    <button
                                        type="button"
                                        onClick={handleScanDocs}
                                        disabled={!canScan || ocrScanning}
                                        className={`w-full py-3 rounded-xl border border-slate-600 font-medium transition-all flex items-center justify-center gap-2
                                    ${canScan && !ocrScanning
                                                ? 'bg-slate-800 hover:bg-slate-700 text-white border-blue-500/50'
                                                : 'bg-slate-800/50 text-slate-500 cursor-not-allowed'
                                            }
                                `}
                                    >
                                        {ocrScanning ? (
                                            <>
                                                <ScanLine className="w-5 h-5 animate-pulse" /> Scanning OCR...
                                            </>
                                        ) : (
                                            <>
                                                <ScanLine className="w-5 h-5" /> Scan & Auto-fill Form
                                            </>
                                        )}
                                    </button>

                                    {/* Form Fields */}
                                    <div className="space-y-4 pt-4 border-t border-slate-800">
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                            <input required name="firstName" value={formData.firstName} onChange={handleInputChange} className={inputClass} placeholder="First Name" />
                                            <input name="middleName" value={formData.middleName} onChange={handleInputChange} className={inputClass} placeholder="Middle Name" />
                                            <input required name="lastName" value={formData.lastName} onChange={handleInputChange} className={inputClass} placeholder="Last Name" />
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <input required type="email" name="email" value={formData.email} onChange={handleInputChange} className={inputClass} placeholder="Email Address" />
                                            <input required type="tel" name="phone" value={formData.phone} onChange={handleInputChange} className={inputClass} placeholder="Phone Number" />
                                        </div>

                                        <div>
                                            <input required type="password" name="password" value={formData.password} onChange={handleInputChange} className={inputClass} placeholder="Create a strong password" />
                                        </div>

                                        <div className="grid grid-cols-3 gap-4">
                                            <input required name="citizenshipNo" value={formData.citizenshipNo} onChange={handleInputChange} className={inputClass} placeholder="Citizenship No" />
                                            <input required name="placeOfIssue" value={formData.placeOfIssue} onChange={handleInputChange} className={inputClass} placeholder="District" />
                                            <input required type="date" name="dateOfIssue" value={formData.dateOfIssue} onChange={handleInputChange} className={inputClass} />
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <input required name="fatherName" value={formData.fatherName} onChange={handleInputChange} className={inputClass} placeholder="Father's Name" />
                                            <input required name="motherName" value={formData.motherName} onChange={handleInputChange} className={inputClass} placeholder="Mother's Name" />
                                        </div>
                                    </div>

                                    <button
                                        type="submit"
                                        disabled={loading}
                                        className="w-full py-4 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl shadow-lg transition-all"
                                    >
                                        {loading ? 'Processing...' : 'Proceed to Verification'}
                                    </button>
                                </form>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

const HeaderDateWidget = () => {
    const [status, setStatus] = React.useState(null);

    React.useEffect(() => {
        fetch('http://localhost:8002/api/calendar')
            .then(res => {
                if (!res.ok) throw new Error('API Error');
                return res.json();
            })
            .then(data => setStatus(data))
            .catch(err => {
                console.error("Calendar API Error:", err);
                setStatus({ english_date: '', nepali_date: '' }); // Fallback to avoid null
            });
    }, []);

    if (!status || !status.nepali_date) return null;

    return (
        <span className="text-[10px] bg-slate-800 border border-slate-700 rounded-full px-2 py-0.5 text-slate-300 font-medium">
            {status.english_date || ''} <span className="text-slate-500">|</span> {status.nepali_date.includes(',') ? status.nepali_date.split(',')[0] : status.nepali_date}
        </span>
    );
};
