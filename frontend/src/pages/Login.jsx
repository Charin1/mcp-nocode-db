import React, { useState } from 'react';
import { useNavigate, Navigate, Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import { useAuth } from 'context/AuthContext';
import Spinner from 'components/common/Spinner';

const Login = () => {
  const [email, setEmail] = useState('admin@example.com'); // Pre-fill for convenience
  const [password, setPassword] = useState('password'); // Pre-fill for convenience
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (error) {
      toast.error("Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  if (isAuthenticated) {
    return <Navigate to="/" />;
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-[var(--bg-primary)] transition-colors">
      {/* Background gradient effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-transparent to-purple-500/10 pointer-events-none" />

      <div className="relative w-full max-w-md p-8 space-y-8 glass-card rounded-2xl shadow-xl">
        {/* Gradient border effect */}
        <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 -z-10 blur-xl" />

        <h2 className="text-3xl font-bold text-center text-[var(--text-primary)] tracking-tight">
          MCP No-Code DB
        </h2>
        <form className="space-y-6" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="email" className="text-sm font-medium text-[var(--text-secondary)]">Email address</label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 mt-1 text-[var(--text-primary)] bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-lg focus:ring-2 focus:ring-brand-indigo focus:border-brand-indigo transition-all"
            />
          </div>
          <div>
            <label htmlFor="password" className="text-sm font-medium text-[var(--text-secondary)]">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 mt-1 text-[var(--text-primary)] bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-lg focus:ring-2 focus:ring-brand-indigo focus:border-brand-indigo transition-all"
            />
          </div>
          <div>
            <button
              type="submit"
              disabled={loading}
              className="w-full px-4 py-3 font-semibold text-white bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg hover:from-indigo-500 hover:to-purple-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-indigo disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center transition-all shadow-lg shadow-indigo-500/25"
            >
              {loading ? <Spinner size={20} /> : 'Sign in'}
            </button>
          </div>
        </form>
        <div className="text-center text-[var(--text-secondary)]">
          Don't have an account?{' '}
          <Link to="/signup" className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
            Sign up
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Login;