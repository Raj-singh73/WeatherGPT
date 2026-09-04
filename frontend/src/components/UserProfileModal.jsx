import React, { useState, useEffect } from 'react';
import { 
  X, User, Mail, Phone, MapPin, Sprout, 
  Calendar, Clock, Database, LogOut, CheckCircle2, 
  AlertCircle, Loader2, Edit3, Save, RefreshCw, Shield
} from 'lucide-react';
import { api } from '../api';

const ROLES = [
  { id: 'Farmer', label: 'Farmer / Kisan' },
  { id: 'Citizen', label: 'Citizen / Commuter' },
  { id: 'Agricultural Scientist', label: 'Agricultural Scientist' },
  { id: 'Disaster Manager', label: 'Disaster Management' },
  { id: 'Researcher', label: 'Student / Researcher' }
];

const CROPS = ['Wheat', 'Rice', 'Sugarcane', 'Cotton', 'Maize', 'Pulses', 'Mustard', 'Soybean', 'Vegetables'];

export default function UserProfileModal({ 
  isOpen, 
  onClose, 
  user, 
  onUserUpdated, 
  onLogout 
}) {
  const [activeTab, setActiveTab] = useState('profile'); // 'profile' | 'database'
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState({ type: '', text: '' });

  // Edit fields
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [role, setRole] = useState('Farmer');
  const [state, setState] = useState('');
  const [district, setDistrict] = useState('');
  const [village, setVillage] = useState('');
  const [primaryCrop, setPrimaryCrop] = useState('Wheat');
  const [preferredLanguage, setPreferredLanguage] = useState('en');

  // Database audit telemetry records
  const [dbRecords, setDbRecords] = useState({ users: [], recent_logs: [], total_users: 0 });
  const [loadingDb, setLoadingDb] = useState(false);

  useEffect(() => {
    if (user) {
      setName(user.name || '');
      setPhone(user.phone || '');
      setRole(user.role || 'Farmer');
      setState(user.state || 'Uttar Pradesh');
      setDistrict(user.district || 'Lucknow');
      setVillage(user.village || '');
      setPrimaryCrop(user.primary_crop || 'Wheat');
      setPreferredLanguage(user.preferred_language || 'en');
    }
  }, [user]);

  useEffect(() => {
    if (isOpen && activeTab === 'database') {
      fetchDatabaseRecords();
    }
  }, [isOpen, activeTab]);

  const fetchDatabaseRecords = async () => {
    setLoadingDb(true);
    try {
      const data = await api.getAdminRecords();
      setDbRecords(data);
    } catch (err) {
      console.error('Failed to fetch DB telemetry records:', err);
    } finally {
      setLoadingDb(false);
    }
  };

  if (!isOpen || !user) return null;

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatusMsg({ type: '', text: '' });

    try {
      const updates = {
        name: name.trim(),
        phone: phone.trim() || null,
        role,
        state: state.trim() || null,
        district: district.trim() || null,
        village: village.trim() || null,
        primary_crop: primaryCrop,
        preferred_language: preferredLanguage
      };

      const updatedUser = await api.updateProfile(updates);
      localStorage.setItem('weathergpt_user', JSON.stringify(updatedUser));
      onUserUpdated(updatedUser);
      setIsEditing(false);
      setStatusMsg({ type: 'success', text: 'Profile & preferences saved successfully to SQLite database!' });
      setTimeout(() => setStatusMsg({ type: '', text: '' }), 3500);
    } catch (err) {
      console.error('Profile update error:', err);
      setStatusMsg({ type: 'error', text: err.response?.data?.detail || 'Failed to update profile.' });
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (isoStr) => {
    if (!isoStr) return 'N/A';
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return isoStr;
    }
  };

  const isAdmin = user?.role === 'Admin' || 
                  user?.email?.toLowerCase() === 'rajsingh700777@gmail.com' || 
                  user?.email?.toLowerCase() === 'admin@weathergpt.io' || 
                  user?.id === 1;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div 
        className="relative w-full max-w-2xl bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden max-h-[92vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="relative px-6 pt-6 pb-4 bg-gradient-to-br from-slate-900 via-sky-950 to-indigo-950 text-white flex-shrink-0">
          <button 
            onClick={onClose}
            aria-label="Close profile"
            className="absolute top-5 right-5 p-2 rounded-full text-slate-300 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>

          <div className="flex items-center space-x-4">
            <div className="h-14 w-14 rounded-2xl bg-gradient-to-tr from-sky-400 via-blue-500 to-indigo-600 flex items-center justify-center text-white text-xl font-black shadow-lg ring-2 ring-white/20">
              {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-xl font-black tracking-tight text-white">{user.name}</h2>
                <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-300 border border-sky-400/30">
                  {isAdmin ? '🛡️ Administrator' : user.role || 'Farmer'}
                </span>
              </div>
              <p className="text-xs text-slate-300 flex items-center space-x-1.5 mt-0.5">
                <Mail className="h-3 w-3 text-sky-400" />
                <span>{user.email}</span>
              </p>
            </div>
          </div>

          {/* Navigation Tabs - ONLY visible to Admin/Owner */}
          {isAdmin && (
            <div className="flex bg-white/10 p-1 rounded-xl mt-5 backdrop-blur-xs">
              <button
                onClick={() => setActiveTab('profile')}
                className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center justify-center space-x-1.5 ${
                  activeTab === 'profile' 
                    ? 'bg-white text-slate-900 shadow-sm' 
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                <User className="h-3.5 w-3.5" />
                <span>My Profile & Preferences</span>
              </button>
              <button
                onClick={() => setActiveTab('database')}
                className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center justify-center space-x-1.5 ${
                  activeTab === 'database' 
                    ? 'bg-white text-slate-900 shadow-sm' 
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                <Database className="h-3.5 w-3.5" />
                <span>Admin Database Records</span>
              </button>
            </div>
          )}
        </div>

        {/* Scrollable Content */}
        <div className="p-6 overflow-y-auto space-y-4">
          
          {statusMsg.text && (
            <div className={`flex items-center space-x-2 p-3 rounded-xl text-xs ${
              statusMsg.type === 'success' 
                ? 'bg-emerald-50 border border-emerald-200 text-emerald-700' 
                : 'bg-rose-50 border border-rose-200 text-rose-700'
            }`}>
              {statusMsg.type === 'success' ? <CheckCircle2 className="h-4 w-4 flex-shrink-0" /> : <AlertCircle className="h-4 w-4 flex-shrink-0" />}
              <span>{statusMsg.text}</span>
            </div>
          )}

          {activeTab === 'profile' ? (
            <>
              {/* Telemetry Timestamps Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="bg-slate-50 border border-slate-200 rounded-2xl p-3.5">
                  <div className="flex items-center space-x-2 text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">
                    <Calendar className="h-3.5 w-3.5 text-sky-600" />
                    <span>Account Created (Record Time)</span>
                  </div>
                  <p className="text-xs font-extrabold text-slate-900">
                    {formatDate(user.created_at)}
                  </p>
                  <p className="text-[10px] text-slate-600 mt-0.5">Stored permanently in SQLite</p>
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded-2xl p-3.5">
                  <div className="flex items-center space-x-2 text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">
                    <Clock className="h-3.5 w-3.5 text-indigo-600" />
                    <span>Last Login Timestamp</span>
                  </div>
                  <p className="text-xs font-extrabold text-slate-900">
                    {formatDate(user.last_login_at)}
                  </p>
                  <p className="text-[10px] text-slate-600 mt-0.5">Updated on session authentication</p>
                </div>
              </div>

              {/* Profile Details or Edit Form */}
              <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
                <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
                  <h3 className="text-sm font-bold text-slate-900">User Telemetry & Agro-Settings</h3>
                  <button
                    type="button"
                    onClick={() => setIsEditing(!isEditing)}
                    className="flex items-center space-x-1 text-xs font-bold text-sky-600 hover:text-sky-700 bg-sky-50 px-2.5 py-1 rounded-lg transition-colors cursor-pointer"
                  >
                    <Edit3 className="h-3.5 w-3.5" />
                    <span>{isEditing ? 'Cancel Edit' : 'Edit Profile'}</span>
                  </button>
                </div>

                {isEditing ? (
                  <form onSubmit={handleSaveProfile} className="space-y-3.5">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-bold text-slate-700 mb-1">Full Name</label>
                        <input
                          type="text"
                          required
                          value={name}
                          onChange={(e) => setName(e.target.value)}
                          className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-bold text-slate-700 mb-1">Role</label>
                        <select
                          value={role}
                          onChange={(e) => setRole(e.target.value)}
                          className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                        >
                          {ROLES.map((r) => (
                            <option key={r.id} value={r.id}>{r.label}</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-bold text-slate-700 mb-1">Phone Number</label>
                        <input
                          type="tel"
                          value={phone}
                          onChange={(e) => setPhone(e.target.value)}
                          placeholder="+91 98765 43210"
                          className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-bold text-slate-700 mb-1">Primary Crop</label>
                        <select
                          value={primaryCrop}
                          onChange={(e) => setPrimaryCrop(e.target.value)}
                          className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                        >
                          {CROPS.map((c) => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-bold text-slate-700 mb-1">Home District</label>
                        <input
                          type="text"
                          value={district}
                          onChange={(e) => setDistrict(e.target.value)}
                          className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-bold text-slate-700 mb-1">Village / Tehsil</label>
                        <input
                          type="text"
                          value={village}
                          onChange={(e) => setVillage(e.target.value)}
                          placeholder="e.g. Maharajganj"
                          className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                        />
                      </div>
                    </div>

                    <div className="pt-2 flex justify-end">
                      <button
                        type="submit"
                        disabled={loading}
                        className="px-5 py-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold rounded-xl shadow-sm transition-all flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
                      >
                        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                        <span>Save Changes to Database</span>
                      </button>
                    </div>
                  </form>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-slate-600 block mb-0.5">Home Location</span>
                      <p className="font-bold text-slate-800 flex items-center gap-1.5">
                        <MapPin className="h-3.5 w-3.5 text-sky-600" />
                        {user.district || 'Not Set'} {user.village ? `(${user.village})` : ''}, {user.state || ''}
                      </p>
                    </div>

                    <div>
                      <span className="text-slate-600 block mb-0.5">Primary Monitored Crop</span>
                      <p className="font-bold text-slate-800 flex items-center gap-1.5">
                        <Sprout className="h-3.5 w-3.5 text-emerald-600" />
                        {user.primary_crop || 'Wheat'}
                      </p>
                    </div>

                    <div>
                      <span className="text-slate-600 block mb-0.5">Phone Contact</span>
                      <p className="font-bold text-slate-800 flex items-center gap-1.5">
                        <Phone className="h-3.5 w-3.5 text-slate-400" />
                        {user.phone || 'Not provided'}
                      </p>
                    </div>

                    <div>
                      <span className="text-slate-600 block mb-0.5">Preferred Interface Language</span>
                      <p className="font-bold text-slate-800 uppercase">
                        {user.preferred_language || 'en'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            /* DATABASE TELEMETRY RECORDS TAB */
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                    <Database className="h-4 w-4 text-sky-600" />
                    <span>Persistent SQLite Database Inspector</span>
                  </h3>
                  <p className="text-[11px] text-slate-500">
                    File: <code className="bg-slate-100 px-1 py-0.5 rounded text-[10px]">backend/data/weathergpt.db</code> • Total Users: <strong>{dbRecords.total_users}</strong>
                  </p>
                </div>
                <button
                  onClick={fetchDatabaseRecords}
                  disabled={loadingDb}
                  className="flex items-center space-x-1 text-xs font-bold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 px-2.5 py-1.5 rounded-xl transition-colors cursor-pointer"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${loadingDb ? 'animate-spin' : ''}`} />
                  <span>Refresh</span>
                </button>
              </div>

              {/* Registered Accounts Table */}
              <div className="border border-slate-200 rounded-2xl overflow-hidden bg-white shadow-xs">
                <div className="bg-slate-50 px-4 py-2.5 border-b border-slate-200 font-bold text-xs text-slate-700">
                  Registered User Accounts ({dbRecords.total_users})
                </div>
                <div className="overflow-x-auto max-h-52">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-100/70 text-[10px] text-slate-500 uppercase tracking-wider">
                      <tr>
                        <th className="p-2.5">ID</th>
                        <th className="p-2.5">User</th>
                        <th className="p-2.5">Role</th>
                        <th className="p-2.5">Location</th>
                        <th className="p-2.5">Crop</th>
                        <th className="p-2.5">Created At (Record Time)</th>
                        <th className="p-2.5">Last Login</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {dbRecords.users && dbRecords.users.length > 0 ? (
                        dbRecords.users.map((u) => (
                          <tr key={u.id} className="hover:bg-slate-50/80">
                            <td className="p-2.5 font-mono text-slate-400 font-semibold">{u.id}</td>
                            <td className="p-2.5 font-bold text-slate-900">{u.name}<br/><span className="text-[10px] font-normal text-slate-400">{u.email}</span></td>
                            <td className="p-2.5"><span className="px-1.5 py-0.5 rounded bg-slate-100 text-[10px] font-semibold text-slate-700">{u.role}</span></td>
                            <td className="p-2.5 text-slate-600">{u.district}{u.village ? ` / ${u.village}` : ''}</td>
                            <td className="p-2.5 font-medium text-emerald-700">{u.primary_crop}</td>
                            <td className="p-2.5 text-[11px] text-slate-600 font-mono">{formatDate(u.created_at)}</td>
                            <td className="p-2.5 text-[11px] text-slate-600 font-mono">{formatDate(u.last_login_at)}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="7" className="p-4 text-center text-slate-400">
                            {loadingDb ? 'Loading database records...' : 'No accounts recorded yet.'}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Audit Activity Logs */}
              <div className="border border-slate-200 rounded-2xl overflow-hidden bg-white shadow-xs">
                <div className="bg-slate-50 px-4 py-2.5 border-b border-slate-200 font-bold text-xs text-slate-700">
                  Recent Telemetry & Audit Logs
                </div>
                <div className="overflow-x-auto max-h-44">
                  <div className="divide-y divide-slate-100 p-2 space-y-1">
                    {dbRecords.recent_logs && dbRecords.recent_logs.length > 0 ? (
                      dbRecords.recent_logs.map((log) => (
                        <div key={log.id} className="p-2 rounded-lg bg-slate-50/60 text-xs flex items-center justify-between gap-2">
                          <div className="flex items-center space-x-2">
                            <span className={`px-1.5 py-0.5 rounded text-[9px] font-extrabold tracking-wider uppercase ${
                              log.action === 'REGISTER' ? 'bg-emerald-100 text-emerald-800' :
                              log.action === 'LOGIN' ? 'bg-sky-100 text-sky-800' :
                              log.action === 'UPDATE_PROFILE' ? 'bg-amber-100 text-amber-800' :
                              'bg-slate-200 text-slate-800'
                            }`}>
                              {log.action}
                            </span>
                            <span className="font-semibold text-slate-800">{log.user_email || 'System'}</span>
                            <span className="text-slate-500 text-[11px] truncate max-w-[240px]">{log.details}</span>
                          </div>
                          <span className="text-[10px] text-slate-600 font-mono flex-shrink-0">
                            {formatDate(log.timestamp)}
                          </span>
                        </div>
                      ))
                    ) : (
                      <p className="p-3 text-center text-slate-400 text-xs">No activity logs recorded.</p>
                    )}
                  </div>
                </div>
              </div>

            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center space-x-1.5 text-xs text-slate-500">
            <Shield className="h-3.5 w-3.5 text-sky-600" />
            <span>SQLite ACID Engine</span>
          </div>

          <button
            type="button"
            onClick={onLogout}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-xl text-rose-600 hover:bg-rose-50 border border-rose-200 text-xs font-bold transition-all cursor-pointer shadow-xs"
          >
            <LogOut className="h-4 w-4" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </div>
  );
}
