import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../utils/api';

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');
  
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isValid, setIsValid] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const verifyToken = async () => {
      if (!token) {
        setIsValid(false);
        return;
      }
      try {
        const res = await api.verifyResetToken(token);
        setIsValid(res.valid);
      } catch (err) {
        setIsValid(false);
      }
    };
    verifyToken();
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await api.resetPassword(token, newPassword);
      setMessage('Password reset successfully. Redirecting to login...');
      setTimeout(() => navigate('/'), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  if (isValid === null) return <div className="min-h-screen bg-dark text-white flex items-center justify-center">Verifying token...</div>;
  
  if (isValid === false) return (
    <div className="min-h-screen bg-dark text-white flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl p-8 max-w-md text-center">
        <h2 className="text-xl font-bold text-red-500 mb-4 text-center">Invalid or Expired Link</h2>
        <p className="text-gray-400 mb-6 text-center">This password reset link is invalid or has expired. Please request a new one.</p>
        <Link to="/forgot-password" className="inline-block bg-accent hover:bg-accent/90 text-white font-semibold py-3 px-8 rounded-lg shadow-lg shadow-accent/20">Request New Link</Link>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-dark text-white flex items-center justify-center p-4">
      <div className="bg-card/50 backdrop-blur-xl border border-border rounded-2xl p-8 w-full max-w-md shadow-2xl relative">
        <h2 className="text-xl font-semibold mb-6 text-center">Set New Password</h2>
        
        {message && <div className="bg-green-500/10 border border-green-500/20 text-green-500 text-sm p-4 rounded-xl mb-6 text-center">{message}</div>}
        {error && <div className="bg-red-500/10 border border-red-500/20 text-red-500 text-sm p-4 rounded-xl mb-6 text-center">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-500 uppercase mb-1 ml-1">New Password</label>
            <input 
              type="password" 
              required
              minLength={8}
              className="w-full bg-dark/60 border border-border rounded-xl p-4 text-white focus:border-accent outline-none"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-500 uppercase mb-1 ml-1">Confirm New Password</label>
            <input 
              type="password" 
              required
              className="w-full bg-dark/60 border border-border rounded-xl p-4 text-white focus:border-accent outline-none"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </div>
          <button 
            type="submit"
            disabled={loading}
            className="w-full bg-accent hover:bg-accent/90 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-accent/20 disabled:opacity-50"
          >
            {loading ? 'Resetting...' : 'Update Password'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ResetPassword;
