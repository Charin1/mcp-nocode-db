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
    <main className="flex flex-col flex-1 p-4 overflow-hidden">
      {/* View Toggler */}
      <div className="flex mb-4 border-b border-gray-600">
        <button
          className={`px-4 py-2 text-sm font-medium ${
            activeView === 'editor'
              ? 'text-white border-b-2 border-blue-500'
              : 'text-gray-400 hover:text-white'
          }`}
          onClick={() => setActiveView('editor')}
        >
          Query Editor
        </button>
        <button
          className={`px-4 py-2 text-sm font-medium ${
            activeView === 'chatbot'
              ? 'text-white border-b-2 border-blue-500'
              : 'text-gray-400 hover:text-white'
          }`}
          onClick={() => setActiveView('chatbot')}
        >
          Chatbot
        </button>
      </div>

      {/* Content Area */}
      <div className="flex flex-col flex-1 h-full">
        {activeView === 'editor' ? <QueryEditorView /> : <ChatbotPage />}
      </div>
    </main>
  );
};

export default MainPanel;