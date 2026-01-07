import React, { useState } from 'react';
import { PlusIcon, ChatBubbleLeftIcon } from '@heroicons/react/24/outline'; // Using 24 outline for sidebar items

const SessionList = ({ sessions, currentSessionId, onSelectSession, onNewSession, isLoading }) => {
    return (
        <div className="flex flex-col h-full bg-[#161b22] border-r border-gray-800 w-64 flex-shrink-0">
            {/* Header / New Chat Button */}
            <div className="p-4 border-b border-gray-800">
                <button
                    onClick={onNewSession}
                    disabled={isLoading}
                    className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium text-sm"
                >
                    <PlusIcon className="w-5 h-5" />
                    <span>New Chat</span>
                </button>
            </div>

            {/* Session List */}
            <div className="flex-1 overflow-y-auto py-2">
                {sessions.length === 0 ? (
                    <div className="text-center text-gray-500 text-sm mt-8 px-4">
                        No history yet. Start a new conversation!
                    </div>
                ) : (
                    <div className="space-y-1 px-2">
                        {sessions.map((session) => (
                            <button
                                key={session.id}
                                onClick={() => onSelectSession(session.id)}
                                className={`w-full flex items-center space-x-3 px-3 py-3 rounded-lg text-left transition-colors text-sm ${currentSessionId === session.id
                                        ? 'bg-gray-800 text-white'
                                        : 'text-gray-400 hover:bg-gray-800/50 hover:text-gray-200'
                                    }`}
                            >
                                <ChatBubbleLeftIcon className="w-4 h-4 flex-shrink-0" />
                                <span className="truncate">{session.title || 'Untitled Chat'}</span>
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* Simple User Info or Footer (Optional) */}
            <div className="p-4 border-t border-gray-800 text-xs text-gray-500 text-center">
                Chat History
            </div>
        </div>
    );
};

export default SessionList;
