import React, { useRef, useEffect } from 'react';
import { PaperAirplaneIcon } from '@heroicons/react/24/solid';

const ChatInput = ({ value, onChange, onSubmit, isLoading, disabled, placeholder }) => {
    const textareaRef = useRef(null);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + 'px';
        }
    }, [value]);

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            onSubmit(e);
        }
    };

    return (
        <div className="w-full max-w-3xl mx-auto px-4 pb-6">
            <form
                onSubmit={onSubmit}
                className={`
                    relative flex items-end p-2 bg-[#0d1117] border border-gray-700/50 rounded-3xl shadow-xl transition-all duration-300
                    focus-within:border-indigo-500/50 focus-within:ring-2 focus-within:ring-indigo-500/20 focus-within:shadow-[0_0_20px_rgba(99,102,241,0.15)]
                    ${disabled ? 'opacity-70 cursor-not-allowed' : ''}
                `}
            >
                <textarea
                    ref={textareaRef}
                    value={value}
                    onChange={onChange}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder || "What's in your mind?"}
                    className="w-full bg-transparent text-gray-200 placeholder-gray-500 text-[15px] resize-none focus:outline-none py-3 px-4 max-h-[150px] overflow-y-auto rounded-2xl"
                    rows={1}
                    disabled={disabled}
                />
                <button
                    type="submit"
                    disabled={disabled || !value.trim()}
                    className={`
                        mb-1.5 mr-1.5 p-2 rounded-xl transition-all duration-200
                        ${!value.trim() || disabled
                            ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                            : 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/30 hover:bg-indigo-500'
                        }
                    `}
                >
                    {isLoading ? (
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                        <PaperAirplaneIcon className="w-5 h-5 -rotate-90 translate-x-[1px] -translate-y-[1px]" />
                    )}
                </button>
            </form>
            <p className="text-center text-xs text-gray-500 mt-3 font-medium">
                AI can make mistakes. Please review generated queries.
            </p>
        </div>
    );
};

export default ChatInput;
