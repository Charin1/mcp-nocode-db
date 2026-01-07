import React, { useState, useEffect, useRef } from 'react';
import apiClient from 'api/apiClient';
import { useDbStore } from 'stores/dbStore';
import ChatMessage from 'components/chat/ChatMessage';
import ChatInput from 'components/chat/ChatInput';
import SessionList from 'components/chat/SessionList';
import { Bars3Icon } from '@heroicons/react/24/outline';

const ChatbotPage = () => {
    const defaultMessage = {
        role: 'assistant',
        content: 'Hello! I am your database assistant. Ask me questions about your data, or tell me what you want to find.'
    };

    // State
    // State
    const [messages, setMessages] = useState([defaultMessage]);
    const [sessions, setSessions] = useState([]);
    const [projects, setProjects] = useState([]);
    const [currentSessionId, setCurrentSessionId] = useState(null);
    const [userInput, setUserInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [visibleCharts, setVisibleCharts] = useState({});
    const [isSidebarOpen, setIsSidebarOpen] = useState(true); // Mobile/Toggle state if needed

    // Refs & Store
    const chatEndRef = useRef(null);
    const { selectedDbId, llmProvider } = useDbStore(state => ({
        selectedDbId: state.selectedDbId,
        llmProvider: state.selectedLlmProvider,
    }));

    // --- Effects ---

    // Load sessions and projects on mount
    useEffect(() => {
        fetchSessions();
        fetchProjects();
    }, []);

    // Scroll to bottom when messages change
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isLoading]);

    // --- API Interactions ---

    const fetchProjects = async () => {
        try {
            const res = await apiClient.get('/api/chatbot/projects');
            setProjects(res.data);
        } catch (error) {
            console.error("Failed to load projects:", error);
        }
    };

    const fetchSessions = async (query = '') => {
        try {
            const endpoint = query
                ? `/api/chatbot/sessions?q=${encodeURIComponent(query)}`
                : '/api/chatbot/sessions';
            const res = await apiClient.get(endpoint);
            setSessions(res.data);
        } catch (error) {
            console.error("Failed to load sessions:", error);
        }
    };

    const handleSearch = (query) => {
        fetchSessions(query);
    }

    const handleCreateProject = async (name) => {
        try {
            const res = await apiClient.post('/api/chatbot/projects', { name });
            setProjects([res.data, ...projects]);
        } catch (error) {
            console.error("Failed to create project:", error);
            alert("Failed to create project.");
        }
    };

    const handleDeleteProject = async (projectId) => {
        if (!window.confirm("Delete this project and all its chats?")) return;
        try {
            await apiClient.delete(`/api/chatbot/projects/${projectId}`);
            setProjects(projects.filter(p => p.id !== projectId));
            // Also remove sessions that belonged to this project from local state
            // (Assuming backend cascades delete, or we need to refresh sessions)
            fetchSessions();
        } catch (error) {
            console.error("Failed to delete project:", error);
            alert("Failed to delete project.");
        }
    };

    const handleNewSession = async (projectId = null) => {
        if (!selectedDbId) {
            alert("Please select a database first.");
            return;
        }

        try {
            setIsLoading(true);
            const res = await apiClient.post('/api/chatbot/sessions', {
                db_id: selectedDbId,
                title: `New Chat`,
                project_id: projectId
            });

            const newSession = res.data;
            setSessions([newSession, ...sessions]);
            setCurrentSessionId(newSession.id);
            setMessages([defaultMessage]);
        } catch (error) {
            console.error("Error creating session:", error);
            alert("Failed to create new chat session.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleRenameSession = async (sessionId, newTitle) => {
        try {
            await apiClient.put(`/api/chatbot/sessions/${sessionId}`, { title: newTitle });
            setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, title: newTitle } : s));
        } catch (error) {
            console.error("Failed to rename session:", error);
            alert("Failed to rename chat.");
        }
    };

    const handleMoveSessionToProject = async (sessionId, projectId) => {
        try {
            await apiClient.put(`/api/chatbot/sessions/${sessionId}`, { project_id: projectId });
            setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, project_id: projectId } : s));
        } catch (error) {
            console.error("Failed to move session:", error);
            alert("Failed to move chat.");
        }
    };

    const handleDeleteSession = async (sessionId) => {
        try {
            await apiClient.delete(`/api/chatbot/sessions/${sessionId}`);
            const newSessions = sessions.filter(s => s.id !== sessionId);
            setSessions(newSessions);

            if (sessionId === currentSessionId) {
                if (newSessions.length > 0) {
                    handleSelectSession(newSessions[0].id);
                } else {
                    setCurrentSessionId(null);
                    setMessages([defaultMessage]);
                }
            }
        } catch (error) {
            console.error("Failed to delete session:", error);
            alert("Failed to delete chat.");
        }
    };

    const handleSelectSession = async (sessionId) => {
        if (sessionId === currentSessionId) return;

        try {
            setIsLoading(true);
            const res = await apiClient.get(`/api/chatbot/sessions/${sessionId}`);

            setCurrentSessionId(sessionId);

            // Transform DB messages to UI format if needed (ChatMessage component expects specific shape)
            // DB message: { role, content, query, chart_config, ... }
            // UI message: { role, content, query, chartConfig, ... }
            const loadedMessages = res.data.messages.map(msg => ({
                ...msg,
                chartConfig: msg.chart_config // Map snake_case to camelCase if needed by component
            }));

            if (loadedMessages.length === 0) {
                setMessages([defaultMessage]);
            } else {
                setMessages(loadedMessages);
            }

        } catch (error) {
            console.error("Error loading session:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSendMessage = async (e) => {
        if (e) e.preventDefault();
        if (!userInput.trim()) return;

        // If no active session, create one first?
        // Better UX: Auto-create session on first message if none selected
        let activeSessionId = currentSessionId;

        if (!activeSessionId) {
            if (!selectedDbId) {
                alert("Please select a database to start chatting.");
                return;
            }
            // Auto-create logic
            try {
                setIsLoading(true);
                const res = await apiClient.post('/api/chatbot/sessions', {
                    db_id: selectedDbId,
                    title: userInput.trim().substring(0, 30) + (userInput.length > 30 ? '...' : ''),
                });
                const newSession = res.data;
                setSessions([newSession, ...sessions]);
                setCurrentSessionId(newSession.id);
                activeSessionId = newSession.id;
            } catch (error) {
                console.error("Failed to auto-create session:", error);
                alert("Failed to start conversation.");
                setIsLoading(false);
                return;
            }
        }

        const newMessages = [...messages, { role: 'user', content: userInput }];
        setMessages(newMessages);
        setUserInput('');
        setIsLoading(true);

        try {
            // Note: We use query param for model_provider as finalized in backend
            const res = await apiClient.post(
                `/api/chatbot/sessions/${activeSessionId}/message?model_provider=${llmProvider || 'gemini'}`,
                {
                    role: 'user',
                    content: userInput
                }
            );

            // Backend returns list of NEW messages (assistant response)
            const botResponses = res.data.map(msg => ({
                ...msg,
                chartConfig: msg.chart_config
            }));

            setMessages(prev => [...prev, ...botResponses]);

        } catch (error) {
            let errorMsg = 'An unexpected error occurred.';
            if (error.response?.data?.detail) {
                errorMsg = `Error: ${JSON.stringify(error.response.data.detail)}`;
            }
            // Append temporary error message (not persisted in DB in this flow, but good for UI)
            setMessages(prev => [...prev, { role: 'assistant', content: errorMsg }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleExecuteQuery = async (query) => {
        // This is strictly for manual execution of a generated SQL. 
        // It doesn't go through the chat "session" flow necessarily, or it should?
        // If we want to record the results in the chat history, we should probably have an endpoint for it.
        // For now, let's keep the existing "append local result" behavior for simplicity,
        // as the "Execute" button is usually for "Preview" purposes.

        setIsLoading(true);
        try {
            const res = await apiClient.post('/api/query/execute', {
                db_id: selectedDbId,
                raw_query: query,
                model_provider: llmProvider,
            });

            const resultMessage = {
                role: 'assistant',
                content: 'Query executed successfully. Here are the results:',
                results: res.data
            };

            // We append this locally. If we refresh, this "Result" message might disappear 
            // unless we persist "Tool Outputs" in DB. 
            // Current DB schema has `chart_config` and `query` but not arbitrary result sets.
            // For MVP persistence, we might accept losing large result table data on refresh, 
            // but keeping the query + generated charts.

            setMessages(prev => [...prev, resultMessage]);

        } catch (error) {
            let errorMsg = `Error executing query.`;
            if (error.response?.data?.detail) {
                errorMsg = `Error: ${JSON.stringify(error.response.data.detail)}`;
            }
            setMessages(prev => [...prev, { role: 'assistant', content: errorMsg }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex h-full bg-[#0f1117] text-gray-100 font-sans overflow-hidden">
            {/* Sidebar (Session List) */}
            <div className={`${isSidebarOpen ? 'block' : 'hidden'} md:block h-full`}>
                <SessionList
                    sessions={sessions}
                    projects={projects}
                    currentSessionId={currentSessionId}
                    onSelectSession={handleSelectSession}
                    onNewSession={handleNewSession}
                    onSearch={handleSearch}
                    onRenameSession={handleRenameSession}
                    onDeleteSession={handleDeleteSession}
                    onCreateProject={handleCreateProject}
                    onDeleteProject={handleDeleteProject}
                    onMoveSession={handleMoveSessionToProject}
                    isLoading={isLoading}
                />
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col relative h-full min-w-0">
                {/* Mobile Header / Toggle */}
                <div className="md:hidden p-4 border-b border-gray-800 flex items-center">
                    <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="text-gray-400">
                        <Bars3Icon className="w-6 h-6" />
                    </button>
                    <span className="ml-4 font-semibold">Chat</span>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto w-full scroll-smooth">
                    <div className="max-w-4xl mx-auto px-4 pt-6 pb-32">
                        {messages.map((msg, index) => (
                            <ChatMessage
                                key={index}
                                message={msg}
                                isLast={index === messages.length - 1}
                                onExecuteQuery={handleExecuteQuery}
                                onVisualize={() => setVisibleCharts(prev => ({ ...prev, [index]: !prev[index] }))}
                                visibleCharts={visibleCharts[index]}
                                chartConfig={msg.chartConfig || msg.chart_config}
                            />
                        ))}

                        {isLoading && (
                            <div className="py-6 flex justify-start animate-pulse">
                                <div className="bg-gray-800/50 rounded-lg p-4 max-w-[80%] space-y-2">
                                    <div className="h-2 bg-gray-700 rounded w-24"></div>
                                    <div className="h-2 bg-gray-700 rounded w-48"></div>
                                </div>
                            </div>
                        )}
                        <div ref={chatEndRef} />
                    </div>
                </div>

                {/* Input Area */}
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-[#0f1117] via-[#0f1117] to-transparent pt-10 px-4 pb-4">
                    <div className="max-w-4xl mx-auto">
                        <ChatInput
                            value={userInput}
                            onChange={(e) => setUserInput(e.target.value)}
                            onSubmit={handleSendMessage}
                            isLoading={isLoading}
                            disabled={!selectedDbId && !currentSessionId} // Can't chat if no DB selected AND no active session
                            placeholder={
                                !selectedDbId
                                    ? "Select a database to start..."
                                    : "Ask a question about your data..."
                            }
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChatbotPage;
