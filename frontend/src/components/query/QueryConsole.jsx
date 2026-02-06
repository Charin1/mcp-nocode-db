import React, { useState, useEffect } from 'react';
import { useDbStore } from 'stores/dbStore';
import Editor from 'react-simple-code-editor';
import { highlight, languages } from 'prismjs/components/prism-core';
import 'prismjs/components/prism-sql';
import 'prismjs/components/prism-json';
import 'prismjs/themes/prism-tomorrow.css';
import Spinner from 'components/common/Spinner';
import { PaperAirplaneIcon, SparklesIcon } from '@heroicons/react/24/solid';

const QueryConsole = () => {
  const [activeTab, setActiveTab] = useState('nl'); // 'nl' or 'raw'
  const [nlQuery, setNlQuery] = useState('');
  const [rawQuery, setRawQuery] = useState('');

  const {
    generateQuery,
    isGenerating,
    generatedQuery,
    executeQuery,
    isQuerying,
  } = useDbStore();

  useEffect(() => {
    if (generatedQuery && generatedQuery.raw_query) {
      setRawQuery(generatedQuery.raw_query);
      setActiveTab('raw'); // Switch to raw query tab after generation
    }
  }, [generatedQuery]);

  const handleGenerate = () => {
    if (!nlQuery.trim()) return;
    generateQuery(nlQuery);
  };

  const handleExecute = () => {
    if (!rawQuery.trim()) return;
    executeQuery(rawQuery, nlQuery);
  };

  const getLanguage = () => {
    // A simple heuristic, can be improved by checking db engine
    try {
      JSON.parse(rawQuery);
      return 'json';
    } catch (e) {
      return 'sql';
    }
  };

  return (
    <div className="flex flex-col h-full bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg transition-colors">
      {/* Tabs */}
      <div className="flex border-b border-[var(--border-color)]">
        <button
          onClick={() => setActiveTab('nl')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${activeTab === 'nl' ? 'text-[var(--text-primary)] bg-[var(--bg-tertiary)]' : 'text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)]'}`}
        >
          Natural Language
        </button>
        <button
          onClick={() => setActiveTab('raw')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${activeTab === 'raw' ? 'text-[var(--text-primary)] bg-[var(--bg-tertiary)]' : 'text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)]'}`}
        >
          Raw Query
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 p-2 overflow-auto">
        {activeTab === 'nl' && (
          <textarea
            value={nlQuery}
            onChange={(e) => setNlQuery(e.target.value)}
            placeholder="e.g., Show me the top 5 customers by total order amount"
            className="w-full h-full p-2 text-base text-[var(--text-primary)] bg-transparent border-0 rounded-md resize-none focus:ring-0 font-mono placeholder:text-[var(--text-muted)]"
          />
        )}
        {activeTab === 'raw' && (
          <Editor
            value={rawQuery}
            onValueChange={code => setRawQuery(code)}
            highlight={code => highlight(code, languages[getLanguage()], getLanguage())}
            padding={10}
            className="font-mono text-base"
            style={{
              minHeight: '100%',
              backgroundColor: 'var(--bg-secondary)',
              color: 'var(--text-primary)',
            }}
          />
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end p-2 border-t border-[var(--border-color)] space-x-2">
        {activeTab === 'nl' && (
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="px-4 py-2 font-semibold text-white bg-gradient-to-r from-purple-600 to-indigo-600 rounded-md hover:from-purple-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center transition-all"
          >
            {isGenerating ? <Spinner size={20} /> : <SparklesIcon className="w-5 h-5 mr-2" />}
            Generate Query
          </button>
        )}
        {activeTab === 'raw' && (
          <button
            onClick={handleExecute}
            disabled={isQuerying}
            className="px-4 py-2 font-semibold text-white bg-brand-indigo rounded-md hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center transition-all"
          >
            {isQuerying ? <Spinner size={20} /> : <PaperAirplaneIcon className="w-5 h-5 mr-2" />}
            Execute
          </button>
        )}
      </div>
    </div>
  );
};

export default QueryConsole;