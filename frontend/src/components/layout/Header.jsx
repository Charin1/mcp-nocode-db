import React from 'react';
import { useDbStore } from 'stores/dbStore';
import { useAuth } from 'context/AuthContext'; // <-- THIS IS THE CORRECTED LINE
import { UserCircleIcon, ArrowLeftOnRectangleIcon } from '@heroicons/react/24/solid';

const Header = () => {
  const { databases, llmProviders, selectedDbId, selectedLlmProvider, setSelectedDbId, setSelectedLlmProvider } = useDbStore();
  const { user, logout } = useAuth();

  return (
    <header className="flex items-center justify-between p-4 bg-gray-900 border-b border-gray-700">
      <div className="flex items-center space-x-4">
        {/* Database Selector */}
        <div>
          <label htmlFor="db-selector" className="text-xs font-medium text-gray-400">DATABASE</label>
          <select
            id="db-selector"
            value={selectedDbId || ''}
            onChange={(e) => setSelectedDbId(e.target.value)}
            className="w-48 p-2 text-sm text-white bg-gray-800 border border-gray-600 rounded-md focus:ring-brand-blue focus:border-brand-blue"
          >
            {databases.map(db => (
              <option key={db.id} value={db.id}>{db.name}</option>
            ))}
          </select>
        </div>

        {/* LLM Provider Selector */}
        <div>
          <label htmlFor="llm-selector" className="text-xs font-medium text-gray-400">AI MODEL</label>
          <select
            id="llm-selector"
            value={selectedLlmProvider || ''}
            onChange={(e) => setSelectedLlmProvider(e.target.value)}
            className="w-48 p-2 text-sm text-white bg-gray-800 border border-gray-600 rounded-md focus:ring-brand-blue focus:border-brand-blue"
          >
            {llmProviders.map(provider => (
              <option key={provider} value={provider}>{provider.charAt(0).toUpperCase() + provider.slice(1)}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <UserCircleIcon className="w-6 h-6 text-gray-400" />
          <span className="text-sm font-medium text-white">{user?.email}</span>
          <span className="px-2 py-1 text-xs font-semibold text-purple-200 bg-purple-600 rounded-full">{user?.role}</span>
        </div>
        <button onClick={logout} className="p-2 text-gray-400 rounded-md hover:bg-gray-700 hover:text-white">
          <ArrowLeftOnRectangleIcon className="w-6 h-6" />
        </button>
      </div>
    </header>
  );
};

export default Header;