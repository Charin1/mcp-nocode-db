import React, { useRef, useEffect } from 'react';
import { PaperAirplaneIcon, MicrophoneIcon, StopIcon } from '@heroicons/react/24/solid';
import { useVoiceRecorder } from 'hooks/useVoiceRecorder';

const ChatInput = ({ value, onChange, onSubmit, isLoading, disabled, placeholder }) => {
    const textareaRef = useRef(null);

    // Voice recorder hook - appends transcribed text to input
    const handleTranscription = (text) => {
        const newValue = value ? `${value} ${text}` : text;
        onChange({ target: { value: newValue } });
    };

    const { isRecording, isTranscribing, error, startRecording, stopRecording } = useVoiceRecorder(handleTranscription);

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

    const handleVoiceClick = () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
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
                    ${isRecording ? 'border-red-500/50 ring-2 ring-red-500/20' : ''}
                `}
            >
                <textarea
                    ref={textareaRef}
                    value={value}
                    onChange={onChange}
                    onKeyDown={handleKeyDown}
                    placeholder={isRecording ? "Recording..." : (placeholder || "What's in your mind?")}
                    className="w-full bg-transparent text-gray-200 placeholder-gray-500 text-[15px] resize-none focus:outline-none py-3 px-4 max-h-[150px] overflow-y-auto rounded-2xl"
                    rows={1}
                    disabled={disabled || isRecording}
                />

                {/* Voice Recording Button */}
                <button
                    type="button"
                    onClick={handleVoiceClick}
                    disabled={disabled || isTranscribing}
                    title={isRecording ? "Stop recording" : "Start voice input"}
                    className={`
                        mb-1.5 mr-1 p-2 rounded-xl transition-all duration-200
                        ${isRecording
                            ? 'bg-red-600 text-white animate-pulse shadow-lg shadow-red-500/30'
                            : isTranscribing
                                ? 'bg-amber-600 text-white'
                                : 'bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white'
                        }
                        ${disabled ? 'cursor-not-allowed opacity-50' : ''}
                    `}
                >
                    {isTranscribing ? (
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : isRecording ? (
                        <StopIcon className="w-5 h-5" />
                    ) : (
                        <MicrophoneIcon className="w-5 h-5" />
                    )}
                </button>

                {/* Send Button */}
                <button
                    type="submit"
                    disabled={disabled || !value.trim() || isRecording}
                    className={`
                        mb-1.5 mr-1.5 p-2 rounded-xl transition-all duration-200
                        ${!value.trim() || disabled || isRecording
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
            {error && (
                <p className="text-center text-xs text-red-400 mt-2">{error}</p>
            )}
            <p className="text-center text-xs text-gray-500 mt-3 font-medium">
                {isRecording ? "🎙️ Listening... Click stop when done." : "AI can make mistakes. Please review generated queries."}
            </p>
        </div>
    );
};

export default ChatInput;

