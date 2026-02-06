import React, { useState } from 'react';
import QueryConsole from 'components/query/QueryConsole';
import ResultsPanel from 'components/query/ResultsPanel';
import ChatbotPage from 'pages/ChatbotPage';

// The original view is now encapsulated in its own component
const QueryEditorView = () => {
  return (
    <div className="flex flex-col flex-1 h-full space-y-4">
      <div className="flex-1 h-1/2">
        <QueryConsole />
      </div>
      <div className="flex-1 h-1/2">
        <ResultsPanel />
      </div>
    </div>
  );
};


const MainPanel = () => {
  const [activeView, setActiveView] = useState('editor'); // 'editor' or 'chatbot'

  return (
    <main className="flex flex-col flex-1 overflow-hidden">
      {/* View Toggler */}
      <div className="px-4 pt-4 shrink-0">
        <div className="flex mb-4 border-b border-[var(--border-color)]">
          <button
            className={`px-4 py-2 text-sm font-medium transition-colors ${activeView === 'editor'
              ? 'text-[var(--text-primary)] border-b-2 border-brand-indigo'
              : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            onClick={() => setActiveView('editor')}
          >
            Query Editor
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium transition-colors ${activeView === 'chatbot'
              ? 'text-[var(--text-primary)] border-b-2 border-brand-indigo'
              : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            onClick={() => setActiveView('chatbot')}
          >
            Chatbot
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className={`flex flex-col flex-1 ${activeView === 'chatbot' ? 'overflow-hidden' : 'overflow-y-auto px-4 pb-4'}`}>
        {activeView === 'editor' ? <QueryEditorView /> : <ChatbotPage />}
      </div>
    </main>
  );
};

export default MainPanel;