import React, { createContext, useState, useEffect, useContext } from 'react';
import apiClient from 'api/apiClient';

// Create the context
const AuthContext = createContext(null);

// Create and export the custom hook to consume the context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Create and export the Provider component
export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkSession = async () => {
    try {
      const response = await apiClient.get('/api/me');
      setUser(response.data);
      setIsAuthenticated(true);
    } catch (error) {
      // If 401 or network error, assume not authenticated
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      console.error("Logout failed", error);
    }
    setUser(null);
    setIsAuthenticated(false);
  };

  useEffect(() => {
    checkSession();

    // Listen for the custom logout event from the API client (e.g. on 401 token expiry)
    const handleLogout = () => {
      setUser(null);
      setIsAuthenticated(false);
    };
    window.addEventListener('logout', handleLogout);
    return () => window.removeEventListener('logout', handleLogout);
  }, []);

  const login = async (email, password) => {
    // The backend sets the httponly cookie upon successful login
    await apiClient.post('/auth/token', new URLSearchParams({
      username: email,
      password: password,
    }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });

    // After login, fetch user details to confirm session and get user info
    await checkSession();
  };

  const value = { isAuthenticated, user, login, logout, loading };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};