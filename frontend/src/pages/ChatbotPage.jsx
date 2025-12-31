import React, { useState, useEffect, useRef } from 'react';
import apiClient from 'api/apiClient';
import { useDbStore } from 'stores/dbStore';
import ChatMessage from 'components/chat/ChatMessage';
import ChatInput from 'components/chat/ChatInput';

const CONTEXT_LIMIT = 10; // Max number of messages in a conversation

const ChatbotPage = () => {
    const initialMessage = {
        role: 'assistant',
        content: 'Hello! I am your database assistant. Ask me questions about your data, or tell me what you want to find.'
    };
    const [messages, setMessages] = useState([initialMessage]);
    const [userInput, setUserInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isContextLimitReached, setIsContextLimitReached] = useState(false);
    const [visibleCharts, setVisibleCharts] = useState({});
    const chatEndRef = useRef(null);

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
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isLoading]);

    const handleSendMessage = async (e) => {
        if (e) e.preventDefault();

        if (!userInput.trim() || !selectedDbId) return;

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
                timeout: 30000
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
        } finally {
            setIsLoading(false);
        }
    };

    const handleExecuteQuery = async (query) => {
        setIsLoading(true);
        // Find the index of the message containing this query to append result after it
        // Simpler approach: just append to end of list
        try {
            const res = await apiClient.post('/api/query/execute', {
                db_id: selectedDbId,
                raw_query: query,
                model_provider: llmProvider,
            });

            // We need to associate results with a message or append a new one
            // Current flow: Append a new assistant message with results
            const resultMessage = {
                role: 'assistant',
                content: 'Query executed successfully. Here are the results:',
                results: res.data
            };
            setMessages(prev => [...prev, resultMessage]);

        } catch (error) {
            let errorMsg = 'An unexpected error occurred while executing the query.';
            if (error.response?.data?.detail) {
                errorMsg = `Error executing query: ${JSON.stringify(error.response.data.detail, null, 2)}`;
            }
            setMessages(prev => [...prev, { role: 'assistant', content: errorMsg }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleStartNewConversation = () => {
        setMessages([initialMessage]);
        setIsContextLimitReached(false);
    };

    return (
        <div className="flex flex-col h-full bg-[#0f1117] text-gray-100 font-sans relative">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto w-full">
                <div className="max-w-3xl mx-auto px-4 pt-8 pb-32">
                    {messages.map((msg, index) => (
                        <ChatMessage
                            key={index}
                            message={msg}
                            isLast={index === messages.length - 1}
                            onExecuteQuery={handleExecuteQuery}
                            onVisualize={() => setVisibleCharts(prev => ({ ...prev, [index]: !prev[index] }))}
                            visibleCharts={visibleCharts[index]}
                            chartConfig={null}
                        />
                    ))}

                    {isLoading && (
                        <div className="flex space-x-6 py-6 animate-pulse">
                            <div className="w-8 h-8 rounded-lg bg-gray-800 flex-shrink-0" />
                            <div className="space-y-3 flex-1 min-w-0">
                                <div className="h-4 bg-gray-800 rounded w-1/4"></div>
                                <div className="h-4 bg-gray-800 rounded w-3/4"></div>
                            </div>
                        </div>
                    )}

                    {isContextLimitReached && (
                        <div className="text-center p-8 border border-yellow-500/20 bg-yellow-900/10 rounded-xl mt-8">
                            <p className="text-yellow-400 mb-3 font-medium">Context limit reached.</p>
                            <button
                                onClick={handleStartNewConversation}
                                className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors"
                            >
                                Start New Chat
                            </button>
                        </div>
                    )}
                    <div ref={chatEndRef} />
                </div>
            </div>

            {/* Floating Input Area - Fixed at bottom */}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-[#0f1117] via-[#0f1117] to-transparent pt-10 px-4">
                <ChatInput
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    onSubmit={handleSendMessage}
                    isLoading={isLoading}
                    disabled={!selectedDbId || isContextLimitReached}
                    placeholder={
                        isContextLimitReached
                            ? "Start a new conversation..."
                            : selectedDbId
                                ? "Ask a question about your data..."
                                : "Select a database to start chatting..."
                    }
                />
            </div>
        </div>
    );
};

export default ChatbotPage;
