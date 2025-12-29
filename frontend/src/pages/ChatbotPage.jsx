import React, { useState, useEffect, useRef } from 'react';
import apiClient from 'api/apiClient';
import { useDbStore } from 'stores/dbStore';
import SimpleCodeEditor from 'react-simple-code-editor';
import { highlight, languages } from 'prismjs/components/prism-core';
import 'prismjs/components/prism-sql';
import 'prismjs/themes/prism-tomorrow.css';
import { AgGridReact } from 'ag-grid-react';
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
import ChartVisualization from 'components/chat/ChartVisualization';

const CONTEXT_LIMIT = 10; // Max number of messages in a conversation

const ChatResults = ({ results, onVisualize, showChart, chartConfig }) => {
    if (!results || !results.rows || results.rows.length === 0) {
        return <p className="text-sm text-gray-400 mt-2">Query executed successfully, but returned no rows.</p>;
    }

    const columnDefs = results.columns.map(col => ({ field: col, sortable: true, filter: true }));
    const rowData = results.rows;

    return (
        <div className="mt-3">
            <div className="ag-theme-alpine-dark" style={{ height: 300, width: '100%' }}>
                <AgGridReact
                    columnDefs={columnDefs}
                    rowData={rowData}
                    domLayout='autoHeight'
                />
            </div>
            <div className="mt-3 flex space-x-2">
                <button
                    onClick={onVisualize}
                    className="px-3 py-1 text-xs rounded bg-purple-600 hover:bg-purple-700 flex items-center space-x-1"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <span>Visualize</span>
                </button>
            </div>
            {showChart && (
                <ChartVisualization results={results} chartConfig={chartConfig} />
            )}
        </div>
    );
};


const QueryConfirmation = ({ query, onExecute, onCancel }) => {
    return (
        <div className="mt-2 p-3 rounded-lg bg-gray-800 border border-gray-600">
            <p className="text-sm text-gray-300 mb-2">Generated SQL Query:</p>
            <div className="text-sm bg-gray-900 rounded-md">
                <SimpleCodeEditor
                    value={query}
                    onValueChange={() => { }}
                    highlight={code => highlight(code, languages.sql, 'sql')}
                    padding={10}
                    style={{
                        fontFamily: '"Fira code", "Fira Mono", monospace',
                        fontSize: 14,
                    }}
                    readOnly
                />
            </div>
            <div className="mt-3 flex justify-end space-x-2">
                <button
                    onClick={onCancel}
                    className="px-3 py-1 text-xs rounded bg-gray-600 hover:bg-gray-700"
                >
                    Cancel
                </button>
                <button
                    onClick={() => onExecute(query)}
                    className="px-3 py-1 text-xs rounded bg-green-600 hover:bg-green-700"
                >
                    Execute
                </button>
            </div>
        </div>
    );
};


const ChatbotPage = () => {
    const initialMessage = { role: 'assistant', content: 'Hello! How can I help you with your database today?' };
    const [messages, setMessages] = useState([initialMessage]);
    const [userInput, setUserInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isContextLimitReached, setIsContextLimitReached] = useState(false);
    const [visibleCharts, setVisibleCharts] = useState({});  // Track which message indices have charts visible
    const chatContainerRef = useRef(null);

    const { selectedDbId, llmProvider } = useDbStore(state => ({
        selectedDbId: state.selectedDbId,
        llmProvider: state.selectedLlmProvider,
    }));

    useEffect(() => {
        if (messages.length >= CONTEXT_LIMIT) {
            setIsContextLimitReached(true);
        }
    }, [messages]);

    useEffect(() => {
        // Scroll to the bottom of the chat container
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!userInput.trim() || !selectedDbId) return;

        // DEBUG: Check if token exists
        const token = localStorage.getItem('accessToken');
        if (!token) {
            alert("No authentication token found! You need to log in.");
            return;
        }

        const newMessages = [...messages, { role: 'user', content: userInput }];
        setMessages(newMessages);
        setUserInput('');
        setIsLoading(true);

        try {
            // Sanitize messages to only include fields expected by the backend
            const payloadMessages = newMessages.map(({ role, content, query }) => ({
                role,
                content,
                query: query || null,
            }));

            const res = await apiClient.post('/api/chatbot/message', {
                db_id: selectedDbId,
                model_provider: llmProvider,
                messages: payloadMessages,
            }, {
                timeout: 15000 // 15 second timeout to prevent endless hanging
            });

            setMessages([...newMessages, res.data]);

        } catch (error) {
            let errorMsg = 'An unexpected error occurred.';

            if (error.response) {
                if (error.response.status === 401) {
                    errorMsg = '⚠️ Auth Failed (401). Please LOG OUT and LOG IN again.';
                } else if (error.response.data?.detail) {
                    errorMsg = `Error: ${JSON.stringify(error.response.data.detail)}`;
                }
            }

            setMessages([...newMessages, { role: 'assistant', content: errorMsg }]);
            if (error.response?.data?.detail) {
                // Stringify the detail object to make it readable
                errorMsg = `Error: ${JSON.stringify(error.response.data.detail, null, 2)}`;
            }
            setMessages([...newMessages, { role: 'assistant', content: errorMsg }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleExecuteQuery = async (query) => {
        setIsLoading(true);
        try {
            const res = await apiClient.post('/api/query/execute', {
                db_id: selectedDbId,
                raw_query: query,
                model_provider: llmProvider,
            });
            const resultMessage = {
                role: 'assistant',
                content: 'Here are the results of your query.',
                results: res.data
            };
            setMessages([...messages, resultMessage]);
        } catch (error) {
            let errorMsg = 'An unexpected error occurred while executing the query.';
            if (error.response?.data?.detail) {
                errorMsg = `Error executing query: ${JSON.stringify(error.response.data.detail, null, 2)}`;
            }
            setMessages([...messages, { role: 'assistant', content: errorMsg }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleStartNewConversation = () => {
        setMessages([initialMessage]);
        setIsContextLimitReached(false);
    };

    return (
        <div className="flex flex-col p-4 bg-gray-800 text-white">
            <h1 className="text-2xl font-bold mb-4">Chatbot</h1>
            <div ref={chatContainerRef} className="flex-1 border rounded-lg p-4 bg-gray-900 overflow-y-auto space-y-4">
                {messages.map((msg, index) => (
                    <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div
                            className={`p-3 rounded-lg max-w-lg ${msg.role === 'user' ? 'bg-blue-600' : 'bg-gray-700'
                                }`}
                        >
                            <p>{msg.content}</p>
                            {msg.query && !isContextLimitReached && (
                                <QueryConfirmation
                                    query={msg.query}
                                    onExecute={handleExecuteQuery}
                                    onCancel={() => {
                                        const newMessages = [...messages, { role: 'assistant', content: 'Okay, I will not execute that query.' }];
                                        setMessages(newMessages);
                                    }}
                                />
                            )}
                            {msg.results && (
                                <ChatResults
                                    results={msg.results}
                                    onVisualize={() => setVisibleCharts(prev => ({ ...prev, [index]: !prev[index] }))}
                                    showChart={visibleCharts[index]}
                                    chartConfig={null}
                                />
                            )}
                        </div>
                    </div>
                ))}
                {isContextLimitReached && (
                    <div className="text-center p-4">
                        <p className="text-yellow-400 mb-2">Context limit reached.</p>
                        <button
                            onClick={handleStartNewConversation}
                            className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700"
                        >
                            Start New Conversation
                        </button>
                    </div>
                )}
            </div>
            <form onSubmit={handleSendMessage} className="mt-4 flex">
                <input
                    type="text"
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    placeholder={
                        isContextLimitReached
                            ? "Please start a new conversation."
                            : selectedDbId
                                ? "Ask a question about your data..."
                                : "Please select a database first."
                    }
                    className="flex-1 p-2 rounded-l-lg bg-gray-700 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={!selectedDbId || isLoading || isContextLimitReached}
                />
                <button
                    type="submit"
                    className="px-4 py-2 rounded-r-lg bg-blue-600 hover:bg-blue-700 disabled:bg-gray-500"
                    disabled={!selectedDbId || isLoading || isContextLimitReached || !userInput.trim()}
                >
                    {isLoading ? '...' : 'Send'}
                </button>
            </form>
        </div>
    );
};

export default ChatbotPage;
