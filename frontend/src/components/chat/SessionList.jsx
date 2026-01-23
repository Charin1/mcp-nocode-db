import React, { useState, useRef, useEffect } from 'react';
import {
    PlusIcon,
    ChatBubbleLeftIcon,
    EllipsisHorizontalIcon,
    TrashIcon,
    PencilIcon,
    MagnifyingGlassIcon,
    FolderIcon,
    FolderPlusIcon,
    ChevronDownIcon,
    ChevronRightIcon,
    ArrowRightOnRectangleIcon
} from '@heroicons/react/24/outline';

const SessionList = ({
    sessions,
    projects = [], // [{id, name, ...}]
    currentSessionId,
    onSelectSession,
    onNewSession,
    onDeleteSession,
    onRenameSession,
    onSearch,
    onCreateProject,
    onDeleteProject,
    onMoveSession,
    isLoading
}) => {
    const [dropdownOpenId, setDropdownOpenId] = useState(null);
    const [editingSessionId, setEditingSessionId] = useState(null);
    const [editTitle, setEditTitle] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [expandedProjects, setExpandedProjects] = useState(new Set());
    const [movingSessionId, setMovingSessionId] = useState(null); // ID of session being moved

    // Derived state for filtered sessions
    const filteredSessions = sessions.filter(s =>
        (s.title || '').toLowerCase().includes(searchQuery.toLowerCase())
    );

    const dropdownRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setDropdownOpenId(null);
                setMovingSessionId(null);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Auto-expand project if current session is inside it
    useEffect(() => {
        if (currentSessionId && projects.length > 0) {
            const currentSession = sessions.find(s => s.id === currentSessionId);
            if (currentSession && currentSession.project_id) {
                setExpandedProjects(prev => {
                    const next = new Set(prev);
                    next.add(currentSession.project_id);
                    return next;
                });
            }
        }
    }, [currentSessionId, sessions, projects]);


    const toggleDropdown = (e, sessionId) => {
        e.stopPropagation();
        if (dropdownOpenId === sessionId) {
            setDropdownOpenId(null);
            setMovingSessionId(null); // Reset move state
        } else {
            setDropdownOpenId(sessionId);
            setMovingSessionId(null);
        }
    };

    const toggleProject = (projectId) => {
        setExpandedProjects(prev => {
            const next = new Set(prev);
            if (next.has(projectId)) {
                next.delete(projectId);
            } else {
                next.add(projectId);
            }
            return next;
        });
    };

    const handleCreateProjectClick = () => {
        const name = window.prompt("Enter folder name:");
        if (name && name.trim()) {
            onCreateProject(name.trim());
        }
    };

    const handleProjectDelete = (projectId, e) => {
        e.stopPropagation();
        onDeleteProject(projectId);
    };

    const handleEditStart = (session, e) => {
        e.stopPropagation();
        setEditingSessionId(session.id);
        setEditTitle(session.title || '');
        setDropdownOpenId(null);
    };

    const handleEditSave = async (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (editTitle.trim()) {
            await onRenameSession(editingSessionId, editTitle.trim());
        }
        setEditingSessionId(null);
    };

    const handleDelete = (sessionId, e) => {
        e.stopPropagation();
        if (window.confirm("Are you sure you want to delete this chat?")) {
            onDeleteSession(sessionId);
        }
        setDropdownOpenId(null);
    };

    const handleMoveStart = (e) => {
        e.stopPropagation();
        setMovingSessionId(dropdownOpenId);
    };

    const handleMoveToProject = (e, projectId) => {
        e.stopPropagation();
        onMoveSession(movingSessionId, projectId);
        setDropdownOpenId(null);
        setMovingSessionId(null);
        // Auto expand target project
        if (projectId) {
            setExpandedProjects(prev => new Set(prev).add(projectId));
        }
    };

    const handleSearch = (e) => {
        const query = e.target.value;
        setSearchQuery(query);
        onSearch(query);
    }

    // Organizing Data
    const groupedSessions = []; // Array of { project: Project, sessions: [] }
    const ungroupedSessions = [];

    // Map projects
    projects.forEach(p => {
        groupedSessions.push({
            project: p,
            sessions: filteredSessions.filter(s => s.project_id === p.id)
        });
    });

    // Get ungrouped
    filteredSessions.forEach(s => {
        if (!s.project_id) {
            ungroupedSessions.push(s);
        }
    });


    const renderSessionItem = (session) => (
        <div
            key={session.id}
            className={`group relative flex items-center justify-between rounded-lg transition-colors ${currentSessionId === session.id
                ? 'bg-gray-800/80 text-white'
                : 'text-gray-400 hover:bg-gray-800/40 hover:text-gray-200'
                }`}
        >
            {editingSessionId === session.id ? (
                <form onSubmit={handleEditSave} className="flex-1 flex items-center p-2">
                    <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onBlur={handleEditSave}
                        autoFocus
                        className="w-full bg-[#0d1117] text-white text-sm px-2 py-1 rounded border border-indigo-500 focus:outline-none"
                        onClick={(e) => e.stopPropagation()}
                    />
                </form>
            ) : (
                <button
                    onClick={() => onSelectSession(session.id)}
                    className="flex-1 flex items-center space-x-3 px-3 py-2 text-left w-full overflow-hidden"
                >
                    <ChatBubbleLeftIcon className="w-4 h-4 flex-shrink-0" />
                    <span className="truncate text-sm">{session.title || 'Untitled Chat'}</span>
                </button>
            )}

            {/* Hover Menu Trigger */}
            {!editingSessionId && (
                <div className={`px-2 ${dropdownOpenId === session.id ? 'block' : 'hidden group-hover:block'}`}>
                    <button
                        onClick={(e) => toggleDropdown(e, session.id)}
                        className="p-1 rounded-md hover:bg-gray-700 text-gray-500 hover:text-gray-300 transition-colors"
                    >
                        <EllipsisHorizontalIcon className="w-5 h-5" />
                    </button>

                    {/* Dropdown Menu */}
                    {dropdownOpenId === session.id && (
                        <div
                            ref={dropdownRef}
                            className="absolute right-0 top-8 w-48 bg-[#1c2128] border border-gray-700 rounded-lg shadow-xl z-50 py-1 overflow-hidden"
                        >
                            {movingSessionId === session.id ? (
                                // Move Mode
                                <>
                                    <div className="px-3 py-2 text-xs font-semibold text-gray-400 border-b border-gray-700">
                                        Move to...
                                    </div>
                                    <div className="max-h-48 overflow-y-auto">
                                        <button
                                            onClick={(e) => handleMoveToProject(e, null)}
                                            className="w-full text-left px-4 py-2 text-xs text-gray-300 hover:bg-indigo-600 hover:text-white flex items-center space-x-2"
                                        >
                                            <span>No Folder</span>
                                            {session.project_id === null && <span className="text-indigo-400 ml-auto text-[10px]">(Current)</span>}
                                        </button>
                                        {projects.map(p => (
                                            <button
                                                key={p.id}
                                                onClick={(e) => handleMoveToProject(e, p.id)}
                                                className="w-full text-left px-4 py-2 text-xs text-gray-300 hover:bg-indigo-600 hover:text-white flex items-center space-x-2 truncate"
                                            >
                                                <FolderIcon className="w-3 h-3 flex-shrink-0" />
                                                <span className="truncate">{p.name}</span>
                                                {session.project_id === p.id && <span className="text-indigo-400 ml-auto text-[10px]">(Current)</span>}
                                            </button>
                                        ))}
                                    </div>
                                    <div className="border-t border-gray-700 mt-1">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); setMovingSessionId(null); }}
                                            className="w-full text-left px-4 py-2 text-xs text-gray-400 hover:text-white"
                                        >
                                            Cancel
                                        </button>
                                    </div>
                                </>
                            ) : (
                                // Normal Mode
                                <>
                                    <button
                                        onClick={(e) => handleEditStart(session, e)}
                                        className="w-full text-left px-4 py-2 text-xs text-gray-300 hover:bg-indigo-600 hover:text-white flex items-center space-x-2"
                                    >
                                        <PencilIcon className="w-3 h-3" />
                                        <span>Rename</span>
                                    </button>
                                    <button
                                        onClick={handleMoveStart}
                                        className="w-full text-left px-4 py-2 text-xs text-gray-300 hover:bg-indigo-600 hover:text-white flex items-center space-x-2"
                                    >
                                        <ArrowRightOnRectangleIcon className="w-3 h-3" />
                                        <span>Move to Folder</span>
                                    </button>
                                    <div className="border-t border-gray-700 my-1"></div>
                                    <button
                                        onClick={(e) => handleDelete(session.id, e)}
                                        className="w-full text-left px-4 py-2 text-xs text-red-400 hover:bg-red-900/30 hover:text-red-300 flex items-center space-x-2"
                                    >
                                        <TrashIcon className="w-3 h-3" />
                                        <span>Delete</span>
                                    </button>
                                </>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );

    return (
        <div className="flex flex-col h-full bg-[#161b22] border-r border-gray-800 w-72 flex-shrink-0">
            {/* Header: New Chat & Search */}
            <div className="p-4 border-b border-gray-800 space-y-3">
                <div className="flex space-x-2">
                    <button
                        onClick={() => onNewSession()}
                        disabled={isLoading}
                        className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg transition-colors font-medium text-xs"
                    >
                        <PlusIcon className="w-4 h-4" />
                        <span>New Chat</span>
                    </button>
                    <button
                        onClick={handleCreateProjectClick}
                        className="flex items-center justify-center px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                        title="New Folder"
                    >
                        <FolderPlusIcon className="w-4 h-4" />
                    </button>
                </div>

                <div className="relative">
                    <MagnifyingGlassIcon className="w-4 h-4 text-gray-500 absolute left-3 top-2.5" />
                    <input
                        type="text"
                        placeholder="Search..."
                        value={searchQuery}
                        onChange={handleSearch}
                        className="w-full bg-[#0d1117] border border-gray-700 text-gray-300 text-sm rounded-lg pl-9 pr-3 py-2 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors placeholder-gray-600"
                    />
                </div>
            </div>

            {/* Lists */}
            <div className="flex-1 overflow-y-auto py-2 custom-scrollbar px-2 space-y-4">

                {/* Projects */}
                {groupedSessions.length > 0 && (
                    <div className="space-y-1">
                        {groupedSessions.map(({ project, sessions }) => (
                            <div key={project.id} className="space-y-1">
                                <div
                                    className="group flex items-center justify-between px-2 py-1.5 text-xs font-semibold text-gray-400 hover:text-white cursor-pointer rounded hover:bg-gray-800/50"
                                    onClick={() => toggleProject(project.id)}
                                >
                                    <div className="flex items-center space-x-2 overflow-hidden">
                                        {expandedProjects.has(project.id)
                                            ? <ChevronDownIcon className="w-3 h-3" />
                                            : <ChevronRightIcon className="w-3 h-3" />
                                        }
                                        <FolderIcon className="w-3 h-3 text-indigo-400" />
                                        <span className="truncate uppercase tracking-wider">{project.name}</span>
                                        <span className="text-gray-600 text-[10px] ml-1">({sessions.length})</span>
                                    </div>
                                    <button
                                        onClick={(e) => handleProjectDelete(project.id, e)}
                                        className="hidden group-hover:block p-1 hover:bg-red-900/50 text-gray-600 hover:text-red-400 rounded"
                                    >
                                        <TrashIcon className="w-3 h-3" />
                                    </button>
                                </div>

                                {expandedProjects.has(project.id) && (
                                    <div className="ml-2 pl-2 border-l border-gray-800 space-y-0.5">
                                        {sessions.map(renderSessionItem)}
                                        {sessions.length === 0 && (
                                            <div className="text-[10px] text-gray-600 px-3 py-1 italic">Empty folder</div>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {/* Ungrouped Sessions */}
                <div className="space-y-1">
                    {/* Divider if we have projects */}
                    {groupedSessions.length > 0 && ungroupedSessions.length > 0 && (
                        <div className="px-2 py-2 text-[10px] font-bold text-gray-500 uppercase tracking-widest">
                            Unsorted Checks
                        </div>
                    )}

                    {ungroupedSessions.map(renderSessionItem)}

                    {sessions.length === 0 && (
                        <div className="text-center text-gray-500 text-sm mt-8 px-4">
                            {searchQuery ? "No chats found." : "No history yet."}
                        </div>
                    )}
                </div>

            </div>

            {/* Footer */}
            <div className="p-3 border-t border-gray-800 text-[10px] text-gray-600 text-center font-mono">
                {sessions.length} Conversations • {projects.length} Folders
            </div>
        </div>
    );
};

export default SessionList;

