import React from 'react';
import { useDbStore } from 'stores/dbStore';
import { useAuth } from 'context/AuthContext';
import { useTheme } from 'context/ThemeContext';
import { UserCircleIcon, ArrowLeftOnRectangleIcon, SunIcon, MoonIcon } from '@heroicons/react/24/solid';

const Header = () => {
  const { databases, llmProviders, selectedDbId, selectedLlmProvider, setSelectedDbId, setSelectedLlmProvider, scope, setScope } = useDbStore();
  const { user, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();

  return (
    <header className="flex items-center justify-between p-4 bg-[var(--bg-secondary)] border-b border-[var(--border-color)] transition-colors">
      <div className="flex items-center space-x-4">
        {/* Scope Selector */}
        <div>
          <label htmlFor="scope-selector" className="text-xs font-medium text-[var(--text-muted)]">SCOPE</label>
          <select
            id="scope-selector"
            value={scope}
            onChange={(e) => setScope(e.target.value)}
            className="w-32 p-2 text-sm text-[var(--text-primary)] bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-md focus:ring-brand-indigo focus:border-brand-indigo transition-colors"
          >
            <option value="current">Current DB</option>
            <option value="all">All Databases</option>
          </select>
        </div>

        {/* Database Selector */}
        <div>
          <label htmlFor="db-selector" className="text-xs font-medium text-[var(--text-muted)]">DATABASE</label>
          <select
            id="db-selector"
            value={selectedDbId || ''}
            onChange={(e) => setSelectedDbId(e.target.value)}
            className="w-48 p-2 text-sm text-[var(--text-primary)] bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-md focus:ring-brand-indigo focus:border-brand-indigo transition-colors"
          >
            {databases.map(db => (
              <option key={db.id} value={db.id}>{db.name}</option>
            ))}
          </select>
        </div>

        {/* LLM Provider Selector */}
        <div>
          <label htmlFor="llm-selector" className="text-xs font-medium text-[var(--text-muted)]">AI MODEL</label>
          <select
            id="llm-selector"
            value={selectedLlmProvider || ''}
            onChange={(e) => setSelectedLlmProvider(e.target.value)}
            className="w-48 p-2 text-sm text-[var(--text-primary)] bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-md focus:ring-brand-indigo focus:border-brand-indigo transition-colors"
          >
            {llmProviders.map(provider => (
              <option key={provider} value={provider}>{provider.charAt(0).toUpperCase() + provider.slice(1)}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] hover:bg-[var(--bg-elevated)] transition-all duration-200 group"
          title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        >
          {isDark ? (
            <SunIcon className="w-5 h-5 text-amber-400 group-hover:text-amber-300 transition-colors" />
          ) : (
            <MoonIcon className="w-5 h-5 text-indigo-500 group-hover:text-indigo-400 transition-colors" />
          )}
        </button>

        <div className="flex items-center space-x-2">
          <UserCircleIcon className="w-6 h-6 text-[var(--text-muted)]" />
          <span className="text-sm font-medium text-[var(--text-primary)]">{user?.email}</span>
          <span className="px-2 py-1 text-xs font-semibold text-purple-200 bg-purple-600 rounded-full">{user?.role}</span>
        </div>
        <button onClick={logout} className="p-2 text-[var(--text-muted)] rounded-md hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)] transition-colors">
          <ArrowLeftOnRectangleIcon className="w-6 h-6" />
        </button>
      </div>
    </header>
  );
};

export default Header;