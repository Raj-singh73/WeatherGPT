import React, { useState } from 'react';
import { 
  X, Mail, Lock, User, Phone, MapPin, Sprout, 
  Eye, EyeOff, Loader2, CheckCircle2, AlertCircle, Sparkles, ShieldCheck, KeyRound
} from 'lucide-react';
import { api } from '../api';

const ROLES = [
  { id: 'Farmer', label: 'Farmer / Kisan', icon: '🌾' },
  { id: 'Citizen', label: 'Citizen / Commuter', icon: '🚶' },
  { id: 'Agricultural Scientist', label: 'Agricultural Scientist / KVK', icon: '🔬' },
  { id: 'Disaster Manager', label: 'Disaster Management / SDMA', icon: '🚨' },
  { id: 'Researcher', label: 'Student / Climate Researcher', icon: '🎓' }
];

const CROPS = ['Wheat', 'Rice', 'Sugarcane', 'Cotton', 'Maize', 'Pulses', 'Mustard', 'Soybean', 'Vegetables'];

export default function AuthModal({ 
  isOpen, 
  onClose, 
  onAuthSuccess, 
  currentLocation = 'Lucknow',
  language = 'en'
}) {
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'register' | 'reset'
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Form states
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Farmer');
  const [phone, setPhone] = useState('');
  const [state, setState] = useState('Uttar Pradesh');
  const [district, setDistrict] = useState(currentLocation || 'Lucknow');
  const [village, setVillage] = useState('');
  const [primaryCrop, setPrimaryCrop] = useState('Wheat');
  const [preferredLanguage, setPreferredLanguage] = useState(language || 'en');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');
    setLoading(true);

    try {
      if (authMode === 'register') {
        if (!name.trim()) throw new Error('Please enter your full name.');
        if (!email.trim() || !email.includes('@')) throw new Error('Please provide a valid email address.');
        if (password.length < 6) throw new Error('Password must be at least 6 characters.');

        const payload = {
          name: name.trim(),
          email: email.trim().toLowerCase(),
          password,
          role,
          phone: phone.trim() || null,
          state,
          district,
          village: village.trim() || null,
          primary_crop: primaryCrop,
          preferred_language: preferredLanguage
        };

        const res = await api.register(payload);
        localStorage.setItem('weathergpt_token', res.token);
        localStorage.setItem('weathergpt_user', JSON.stringify(res.user));
        setSuccessMsg('Account registered successfully! Recording profile in database...');
        setTimeout(() => {
          onAuthSuccess(res.user);
          onClose();
        }, 800);
      } else if (authMode === 'login') {
        if (!email.trim() || !password) throw new Error('Please enter both email and password.');
        const res = await api.login({
          email: email.trim().toLowerCase(),
          password
        });
        localStorage.setItem('weathergpt_token', res.token);
        localStorage.setItem('weathergpt_user', JSON.stringify(res.user));
        setSuccessMsg(`Welcome back, ${res.user.name}!`);
        setTimeout(() => {
          onAuthSuccess(res.user);
          onClose();
        }, 800);
      } else if (authMode === 'reset') {
        if (!email.trim() || !email.includes('@')) throw new Error('Please enter your registered email address.');
        if (password.length < 6) throw new Error('New password must be at least 6 characters.');

        const res = await api.resetPassword({
          email: email.trim().toLowerCase(),
          new_password: password
        });
        setSuccessMsg(res.message || 'Password reset successfully! Switching to Sign In...');
        setTimeout(() => {
          setAuthMode('login');
          setSuccessMsg('You can now log in with your new password.');
        }, 1200);
      }
    } catch (err) {
      console.error('Auth error:', err);
      const msg = err.response?.data?.detail || err.message || 'Authentication failed. Please try again.';
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div 
        className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden max-h-[92vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header with gradient branding */}
        <div className="relative px-6 pt-6 pb-4 bg-gradient-to-br from-slate-900 via-sky-950 to-blue-900 text-white flex-shrink-0">
          <button 
            onClick={onClose}
            aria-label="Close modal"
            className="absolute top-5 right-5 p-2 rounded-full text-slate-300 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
          
          <div className="flex items-center space-x-2.5">
            <div className="h-10 w-10 rounded-2xl bg-gradient-to-tr from-sky-400 to-indigo-500 flex items-center justify-center text-white shadow-md">
              {authMode === 'reset' ? <KeyRound className="h-5 w-5" /> : <Sparkles className="h-5 w-5" />}
            </div>
            <div>
              <h2 className="text-xl font-black tracking-tight text-white">
                {authMode === 'register' && 'Create WeatherGPT Account'}
                {authMode === 'login' && 'Sign In to WeatherGPT'}
                {authMode === 'reset' && 'Reset Your Password'}
              </h2>
              <p className="text-xs text-sky-200/80">
                {authMode === 'register' && 'Record your profile and location in our climate database'}
                {authMode === 'login' && 'Access your saved location preferences and agro-advisories'}
                {authMode === 'reset' && 'Enter your registered email and choose a new password'}
              </p>
            </div>
          </div>

          {/* Mode Switch Tabs */}
          <div className="flex bg-white/10 p-1 rounded-xl mt-4 backdrop-blur-xs">
            <button
              type="button"
              onClick={() => { setAuthMode('login'); setErrorMsg(''); setSuccessMsg(''); }}
              className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-all ${
                authMode === 'login' 
                  ? 'bg-white text-slate-900 shadow-sm' 
                  : 'text-slate-300 hover:text-white'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setAuthMode('register'); setErrorMsg(''); setSuccessMsg(''); }}
              className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-all ${
                authMode === 'register' 
                  ? 'bg-white text-slate-900 shadow-sm' 
                  : 'text-slate-300 hover:text-white'
              }`}
            >
              Create Account
            </button>
          </div>
        </div>

        {/* Scrollable Form Content */}
        <div className="p-6 overflow-y-auto space-y-4">
          
          {/* Alerts */}
          {errorMsg && (
            <div className="flex items-center space-x-2 p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {successMsg && (
            <div className="flex items-center space-x-2 p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl text-xs">
              <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            
            {/* Registration specific fields */}
            {authMode === 'register' && (
              <>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Full Name <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                    <input
                      type="text"
                      required
                      placeholder="e.g. Ramesh Kumar"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                    />
                  </div>
                </div>

                {/* Role / Persona */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    User Persona / Role <span className="text-rose-500">*</span>
                  </label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                  >
                    {ROLES.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.icon} {r.label}
                      </option>
                    ))}
                  </select>
                </div>
              </>
            )}

            {/* Email Address */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Email Address <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="email"
                  required
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-bold text-slate-700">
                  {authMode === 'reset' ? 'New Password' : 'Password'} <span className="text-rose-500">*</span>
                </label>
                {authMode === 'login' && (
                  <button
                    type="button"
                    onClick={() => { setAuthMode('reset'); setErrorMsg(''); setSuccessMsg(''); }}
                    className="text-[11px] font-semibold text-sky-600 hover:text-sky-800 cursor-pointer"
                  >
                    Forgot Password?
                  </button>
                )}
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  placeholder="Minimum 6 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-10 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Additional Registration Fields */}
            {authMode === 'register' && (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Phone Number (Optional)
                    </label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                      <input
                        type="tel"
                        placeholder="+91 98765 43210"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Primary Crop
                    </label>
                    <div className="relative">
                      <Sprout className="absolute left-3 top-2.5 h-4 w-4 text-emerald-600" />
                      <select
                        value={primaryCrop}
                        onChange={(e) => setPrimaryCrop(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                      >
                        {CROPS.map((c) => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Home District
                    </label>
                    <div className="relative">
                      <MapPin className="absolute left-3 top-2.5 h-4 w-4 text-sky-600" />
                      <input
                        type="text"
                        placeholder="e.g. Lucknow"
                        value={district}
                        onChange={(e) => setDistrict(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Village / Tehsil (Optional)
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Maharajganj"
                      value={village}
                      onChange={(e) => setVillage(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                    />
                  </div>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-start space-x-2 text-[11px] text-slate-600">
                  <ShieldCheck className="h-4 w-4 text-sky-600 flex-shrink-0 mt-0.5" />
                  <span>
                    Your registration time, chosen district, and advisory telemetry are securely stored in our persistent climate database to deliver personalized weather risk alerts.
                  </span>
                </div>
              </>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-sky-600 via-blue-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white text-xs font-bold shadow-md shadow-sky-500/20 transition-all flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : authMode === 'register' ? (
                <span>Register & Save Profile in Database</span>
              ) : authMode === 'reset' ? (
                <span>Reset Password & Update Database</span>
              ) : (
                <span>Sign In to Account</span>
              )}
            </button>
          </form>

          {/* Bottom Switch Note */}
          <div className="text-center pt-2 text-xs text-slate-500">
            {authMode === 'register' && (
              <p>
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => { setAuthMode('login'); setErrorMsg(''); }}
                  className="font-bold text-sky-600 hover:underline"
                >
                  Sign In here
                </button>
              </p>
            )}
            {authMode === 'login' && (
              <p>
                Don't have an account yet?{' '}
                <button
                  type="button"
                  onClick={() => { setAuthMode('register'); setErrorMsg(''); }}
                  className="font-bold text-sky-600 hover:underline"
                >
                  Create one now
                </button>
              </p>
            )}
            {authMode === 'reset' && (
              <p>
                Remembered your password?{' '}
                <button
                  type="button"
                  onClick={() => { setAuthMode('login'); setErrorMsg(''); }}
                  className="font-bold text-sky-600 hover:underline"
                >
                  Back to Sign In
                </button>
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
