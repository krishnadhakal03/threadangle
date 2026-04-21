import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../utils/api';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');
    try {
      await api.forgotPassword(email);
      setMessage('If this email exists you will receive a reset link shortly');
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark text-white flex items-center justify-center p-4">
      <div className="bg-card/50 backdrop-blur-xl border border-border rounded-2xl p-8 w-full max-w-md shadow-2xl relative">
        <div className="flex items-center gap-2 mb-8 justify-center">
          <div className="w-8 h-8 bg-accent rounded-lg flex items-center justify-center font-bold text-xl">⚡</div>
          <h1 className="text-2xl font-bold tracking-tight">Threadangle</h1>
        </div>
        
        <h2 className="text-xl font-semibold mb-2 text-center">Forgot Password?</h2>
        <p className="text-gray-400 text-sm text-center mb-8">Enter your email and we'll send you a reset link.</p>
        
        {message && <div className="bg-green-500/10 border border-green-500/20 text-green-500 text-sm p-4 rounded-xl mb-6 text-center">{message}</div>}
        {error && <div className="bg-red-500/10 border border-red-500/20 text-red-500 text-sm p-4 rounded-xl mb-6 text-center">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-500 uppercase mb-1 ml-1">Email Address</label>
            <input 
              type="email" 
              required
              className="w-full bg-dark/60 border border-border rounded-xl p-4 text-white focus:border-accent outline-none transition-all"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <button 
            type="submit"
            disabled={loading}
            className="w-full bg-accent hover:bg-accent/90 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-accent/20 disabled:opacity-50"
          >
            {loading ? 'Sending...' : 'Send Reset Link'}
          </button>
          <p className="text-center text-sm text-gray-500 mt-6">
            Remember your password? <Link to="/login" className="text-accent font-bold hover:underline">Sign In</Link>
          </p>
        </form>
      </div>
    </div>
  );
};

export default ForgotPassword;
