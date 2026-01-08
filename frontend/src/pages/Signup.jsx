import React, { useState } from 'react';
import { useNavigate, Navigate, Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import { useAuth } from 'context/AuthContext';
import apiClient from 'api/apiClient';
import Spinner from 'components/common/Spinner';

const Signup = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const { isAuthenticated, login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (password !== confirmPassword) {
            toast.error("Passwords do not match");
            return;
        }

        setLoading(true);
        try {
            // Register the user
            await apiClient.post('/auth/register', {
                email,
                password,
            });

            toast.success("Registration successful! Logging you in...");

            // Auto login after registration
            await login(email, password);
            navigate('/');
        } catch (error) {
            if (error.response && error.response.status === 409) {
                toast.error("Email already registered. Please login.");
            } else {
                toast.error("Registration failed. Please try again.");
            }
        } finally {
            setLoading(false);
        }
    };

    if (isAuthenticated) {
        return <Navigate to="/" />;
    }

    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-900">
            <div className="w-full max-w-md p-8 space-y-8 bg-gray-800 rounded-lg shadow-lg">
                <h2 className="text-3xl font-bold text-center text-white">
                    Create Account
                </h2>
                <form className="space-y-6" onSubmit={handleSubmit}>
                    <div>
                        <label htmlFor="email" className="text-sm font-medium text-gray-400">Email address</label>
                        <input
                            id="email"
                            name="email"
                            type="email"
                            autoComplete="email"
                            required
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full px-3 py-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-md focus:ring-brand-blue focus:border-brand-blue"
                        />
                    </div>
                    <div>
                        <label htmlFor="password" className="text-sm font-medium text-gray-400">Password</label>
                        <input
                            id="password"
                            name="password"
                            type="password"
                            autoComplete="new-password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-3 py-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-md focus:ring-brand-blue focus:border-brand-blue"
                        />
                    </div>
                    <div>
                        <label htmlFor="confirmPassword" className="text-sm font-medium text-gray-400">Confirm Password</label>
                        <input
                            id="confirmPassword"
                            name="confirmPassword"
                            type="password"
                            autoComplete="new-password"
                            required
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            className="w-full px-3 py-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-md focus:ring-brand-blue focus:border-brand-blue"
                        />
                    </div>
                    <div>
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full px-4 py-2 font-semibold text-white bg-brand-blue rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-blue disabled:bg-gray-500 flex justify-center items-center"
                        >
                            {loading ? <Spinner size={20} /> : 'Sign up'}
                        </button>
                    </div>
                </form>
                <div className="text-center text-gray-400">
                    Already have an account?{' '}
                    <Link to="/login" className="text-brand-blue hover:text-blue-400">
                        Sign in
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default Signup;
