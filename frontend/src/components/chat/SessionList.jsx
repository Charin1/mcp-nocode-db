import React, { useState, useRef, useEffect } from 'react';
import { PlusIcon, ChatBubbleLeftIcon, EllipsisHorizontalIcon, TrashIcon, PencilIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';

const SessionList = ({ sessions, currentSessionId, onSelectSession, onNewSession, onDeleteSession, onRenameSession, onSearch, isLoading }) => {
    const [dropdownOpenId, setDropdownOpenId] = useState(null);
    const [editingSessionId, setEditingSessionId] = useState(null);
    const [editTitle, setEditTitle] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const dropdownRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setDropdownOpenId(null);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const toggleDropdown = (e, sessionId) => {
        e.stopPropagation();
        setDropdownOpenId(dropdownOpenId === sessionId ? null : sessionId);
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

    const handleEditCancel = (e) => {
        e.stopPropagation();
        setEditingSessionId(null);
    };

    const handleDelete = (sessionId, e) => {
        e.stopPropagation();
        if (window.confirm("Are you sure you want to delete this chat?")) {
            onDeleteSession(sessionId);
        }
        setDropdownOpenId(null);
    };

    const handleSearch = (e) => {
        const query = e.target.value;
        setSearchQuery(query);
        onSearch(query);
    }

    return (
        <div className="flex flex-col h-full bg-[#161b22] border-r border-gray-800 w-72 flex-shrink-0">
            {/* Header / New Chat Button */}
            <div className="p-4 border-b border-gray-800 space-y-3">
                <button
                    onClick={onNewSession}
                    disabled={isLoading}
                    className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium text-sm"
                >
                    <PlusIcon className="w-5 h-5" />
                    <span>New Chat</span>
                </button>

                <div className="relative">
                    <MagnifyingGlassIcon className="w-4 h-4 text-gray-500 absolute left-3 top-2.5" />
                    <input
                        type="text"
                        placeholder="Search chats..."
                        value={searchQuery}
                        onChange={handleSearch}
                        className="w-full bg-[#0d1117] border border-gray-700 text-gray-300 text-sm rounded-lg pl-9 pr-3 py-2 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors placeholder-gray-600"
                    />
                </div>
            </div>

            {/* Session List */}
            <div className="flex-1 overflow-y-auto py-2 custom-scrollbar">
                {sessions.length === 0 ? (
                    <div className="text-center text-gray-500 text-sm mt-8 px-4">
                        {searchQuery ? "No chats found." : "No history yet."}
                    </div>
                ) : (
                    <div className="space-y-1 px-2">
                        {sessions.map((session) => (
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
                                            onBlur={handleEditSave} // Save on click away
                                            autoFocus
                                            className="w-full bg-[#0d1117] text-white text-sm px-2 py-1 rounded border border-indigo-500 focus:outline-none"
                                            onClick={(e) => e.stopPropagation()}
                                        />
                                    </form>
                                ) : (
                                    <button
                                        onClick={() => onSelectSession(session.id)}
                                        className="flex-1 flex items-center space-x-3 px-3 py-3 text-left w-full overflow-hidden"
                                    >
                                        <ChatBubbleLeftIcon className="w-4 h-4 flex-shrink-0" />
                                        <span className="truncate text-sm">{session.title || 'Untitled Chat'}</span>
                                    </button>
                                )}

                                {/* Hover Menu Trigger - Visible on hover or when dropdown open */}
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
                                                className="absolute right-2 top-8 w-32 bg-[#1c2128] border border-gray-700 rounded-lg shadow-xl z-50 py-1 overflow-hidden"
                                            >
                                                <button
                                                    onClick={(e) => handleEditStart(session, e)}
                                                    className="w-full text-left px-4 py-2 text-xs text-gray-300 hover:bg-indigo-600 hover:text-white flex items-center space-x-2"
                                                >
                                                    <PencilIcon className="w-3 h-3" />
                                                    <span>Rename</span>
                                                </button>
                                                <button
                                                    onClick={(e) => handleDelete(session.id, e)}
                                                    className="w-full text-left px-4 py-2 text-xs text-red-400 hover:bg-red-900/30 hover:text-red-300 flex items-center space-x-2"
                                                >
                                                    <TrashIcon className="w-3 h-3" />
                                                    <span>Delete</span>
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-gray-800 text-[10px] text-gray-600 text-center font-mono">
                {sessions.length} Conversations stored
            </div>
        </div>
    );
};

export default SessionList;
