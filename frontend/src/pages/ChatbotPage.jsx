import React, { useState, useEffect, useRef } from 'react';
import apiClient from 'api/apiClient';
import { useDbStore } from 'stores/dbStore';
import { useMcpStore } from 'stores/mcpStore';
import ChatMessage from 'components/chat/ChatMessage';
import ChatInput from 'components/chat/ChatInput';
import SessionList from 'components/chat/SessionList';
import { Bars3Icon, SparklesIcon } from '@heroicons/react/24/outline';
import { autoDetectChartConfig, transformResultsToChartData } from '../utils/chartUtils';

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
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
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
        // Guard against event object being passed as projectId
        if (projectId && projectId.nativeEvent) {
            projectId = null;
        }

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
            const errorDetail = error.response?.data?.detail || error.message;
            alert(`Failed to create new chat session: ${errorDetail}`);
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
            // Construct query params
            const params = new URLSearchParams();
            params.append('model_provider', llmProvider || 'gemini');

            // Add active MCP IDs
            const activeMcpIds = useMcpStore.getState().activeConnectionIds;
            if (activeMcpIds.length > 0) {
                // Pass as comma-separated string or multiple params? Backend handles both via custom logic I wrote
                // but let's send as multiple keys 'active_mcp_ids' is standard for FastAPI List[str] if using axios paramsSerializer
                // But here we are constructing URL manually-ish.
                // My backend logic: ids_to_fetch.extend(id_val.split(",")) handles comma separated.
                params.append('active_mcp_ids', activeMcpIds.join(','));
            }

            const res = await apiClient.post(
                `/api/chatbot/sessions/${activeSessionId}/message?${params.toString()}`,
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

    const handleExecuteQuery = async (query, messageId, index) => {
        setIsLoading(true);
        try {
            const res = await apiClient.post('/api/query/execute', {
                db_id: selectedDbId,
                raw_query: query,
                model_provider: llmProvider,
            });

            const results = res.data;

            // Update Backend if we have an ID
            console.log("DEBUG handleExecuteQuery - messageId:", messageId, "currentSessionId:", currentSessionId);
            if (messageId && currentSessionId) {
                try {
                    console.log("DEBUG PATCH call:", `/api/chatbot/sessions/${currentSessionId}/messages/${messageId}`, { results: results });
                    await apiClient.patch(`/api/chatbot/sessions/${currentSessionId}/messages/${messageId}`, {
                        results: results
                    });
                    console.log("DEBUG PATCH success");
                } catch (e) {
                    console.error("Failed to persist results:", e);
                }
            } else {
                console.warn("DEBUG: Skipping PATCH - missing messageId or currentSessionId");
            }

            // Update Local State (In-place update of the message)
            setMessages(prev => {
                const newMsgs = [...prev];
                if (index !== undefined && newMsgs[index]) {
                    newMsgs[index] = {
                        ...newMsgs[index],
                        results: results
                    };
                }
                return newMsgs;
            });

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

    const handleVisualize = async (index, message) => {
        // Toggle Visibility
        setVisibleCharts(prev => ({ ...prev, [index]: !prev[index] }));

        // Check if config already exists or results are missing
        if ((message.chartConfig || message.chart_config) || !message.results) return;

        // Generate Config
        const data = transformResultsToChartData(message.results);
        const config = autoDetectChartConfig(data, message.results.columns);

        if (config) {
            // Persist to Backend
            if (message.id && currentSessionId) {
                try {
                    await apiClient.patch(`/api/chatbot/sessions/${currentSessionId}/messages/${message.id}`, {
                        chart_config: config
                    });
                } catch (e) {
                    console.error("Failed to persist chart config:", e);
                }
            }

            // Update Local State
            setMessages(prev => {
                const newMsgs = [...prev];
                newMsgs[index] = { ...newMsgs[index], chartConfig: config };
                return newMsgs;
            });
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
                    <div className="max-w-4xl mx-auto px-4 pt-6 pb-40">
                        {messages.map((msg, index) => (
                            <ChatMessage
                                key={index}
                                message={msg}
                                isLast={index === messages.length - 1}
                                onExecuteQuery={(query) => handleExecuteQuery(query, msg.id, index)}
                                onVisualize={() => handleVisualize(index, msg)}
                                visibleCharts={visibleCharts[index]}
                                chartConfig={msg.chartConfig || msg.chart_config}
                            />
                        ))}

                        {isLoading && (
                            <div className="py-6 flex space-x-4 md:space-x-6 animate-in fade-in duration-300">
                                <div className="flex-shrink-0">
                                    <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center relative">
                                        <div className="absolute inset-0 bg-emerald-500/20 animate-pulse rounded-lg" />
                                        <SparklesIcon className="w-5 h-5 text-emerald-400 relative z-10" />
                                    </div>
                                </div>
                                <div className="flex items-center space-x-1 h-8">
                                    <span className="text-sm text-emerald-500/80 font-mono tracking-wider">THINKING</span>
                                    <span className="w-1 h-1 bg-emerald-500 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                                    <span className="w-1 h-1 bg-emerald-500 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                                    <span className="w-1 h-1 bg-emerald-500 rounded-full animate-bounce"></span>
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
