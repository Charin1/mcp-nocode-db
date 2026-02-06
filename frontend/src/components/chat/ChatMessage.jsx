import React from 'react';
import { UserCircleIcon, CommandLineIcon, PencilSquareIcon, ClipboardDocumentIcon, HandThumbUpIcon, HandThumbDownIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { UserCircleIcon as UserCircleSolid, SparklesIcon } from '@heroicons/react/24/solid';
import SimpleCodeEditor from 'react-simple-code-editor';
import { highlight, languages } from 'prismjs/components/prism-core';
import 'prismjs/components/prism-sql';
import { AgGridReact } from 'ag-grid-react';
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
import ChartVisualization from './ChartVisualization';
import { useTypewriter } from '../../hooks/useTypewriter';

const ChatResults = ({ results, onVisualize, showChart, chartConfig }) => {
    // Identify if it's a JSON result (Mongo/Redis) or Table result (SQL)
    // Backend sends json_result: null for SQL queries, so we must exclude null.
    const isJsonResult = results.json_result !== undefined && results.json_result !== null;

    if (isJsonResult) {
        return (
            <div className="mt-4 bg-[var(--bg-secondary)] rounded-lg p-4 border border-[var(--border-color)] overflow-x-auto">
                <pre className="text-xs text-green-500 dark:text-green-400 font-mono">
                    {JSON.stringify(results.json_result, null, 2)}
                </pre>
            </div>
        );
    }

    if (!results || !results.rows || results.rows.length === 0) {
        return <p className="text-sm text-[var(--text-muted)] mt-2 italic">Query executed successfully, but returned no rows.</p>;
    }

    const columnDefs = results.columns.map(col => ({ field: col, sortable: true, filter: true, resizable: true }));
    const rowData = results.rows;

    return (
        <div className="mt-4 animate-fade-in-up">
            <div className="ag-theme-alpine dark:ag-theme-alpine-dark rounded-lg overflow-hidden border border-[var(--border-color)] shadow-lg" style={{ height: 350, width: '100%' }}>
                <AgGridReact
                    columnDefs={columnDefs}
                    rowData={rowData}
                    pagination={true}
                    paginationPageSize={10}
                />
            </div>
            <div className="mt-3 flex space-x-2">
                <button
                    onClick={onVisualize}
                    className="px-3 py-1.5 text-xs font-medium rounded-md bg-purple-600 hover:bg-purple-500 text-white transition-colors flex items-center space-x-1.5 shadow-sm"
                >
                    <ArrowPathIcon className="h-3.5 w-3.5" />
                    <span>Visualize Data</span>
                </button>
            </div>
            {showChart && (
                <div className="mt-4 p-4 bg-[var(--bg-tertiary)] rounded-xl border border-[var(--border-color)]">
                    <ChartVisualization results={results} chartConfig={chartConfig} />
                </div>
            )}
        </div>
    );
};

const QueryConfirmation = ({ query, onExecute, onCancel }) => {
    return (
        <div className="mt-4 mb-2 p-0 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)] overflow-hidden shadow-md">
            <div className="flex items-center justify-between px-4 py-2 bg-[var(--bg-tertiary)] border-b border-[var(--border-color)]">
                <span className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">Generated Query</span>
                <div className="flex space-x-1">
                    <div className="w-2.5 h-2.5 rounded-full bg-red-500/50"></div>
                    <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50"></div>
                    <div className="w-2.5 h-2.5 rounded-full bg-green-500/50"></div>
                </div>
            </div>
            <div className="bg-[var(--bg-tertiary)] p-1">
                <SimpleCodeEditor
                    value={query}
                    onValueChange={() => { }}
                    highlight={code => highlight(code, languages.sql, 'sql')}
                    padding={16}
                    style={{
                        fontFamily: '"Fira Code", "Fira Mono", monospace',
                        fontSize: 13,
                        backgroundColor: 'transparent',
                    }}
                    readOnly
                />
            </div>
            <div className="px-4 py-3 bg-[var(--bg-tertiary)] border-t border-[var(--border-color)] flex justify-end space-x-3">
                <button
                    onClick={onCancel}
                    className="px-4 py-1.5 text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] rounded-md transition-colors"
                >
                    Cancel
                </button>
                <button
                    onClick={() => onExecute(query)}
                    className="px-4 py-1.5 text-xs font-medium text-white bg-green-600 hover:bg-green-500 rounded-md shadow-sm transition-colors flex items-center"
                >
                    <CommandLineIcon className="w-3.5 h-3.5 mr-1.5" />
                    Run Query
                </button>
            </div>
        </div>
    );
};



const MessageContent = ({ content, isAnimated }) => {
    const { displayedText, isComplete } = useTypewriter(content, 5, isAnimated);

    return (
        <div className="text-[15px] leading-relaxed text-[var(--text-primary)]">
            <p className="whitespace-pre-wrap">
                {displayedText}
                {!isComplete && isAnimated && (
                    <span className="inline-block w-1.5 h-4 ml-0.5 align-middle bg-emerald-500 animate-pulse" />
                )}
            </p>
        </div>
    );
};

const ChatMessage = ({ message, onExecuteQuery, onVisualize, visibleCharts, chartConfig, isLast }) => {
    const isUser = message.role === 'user';
    const isAssistant = message.role === 'assistant';
    // Only animate if it's the last message and it's from the assistant
    const shouldAnimate = isAssistant && isLast;

    return (
        <div className={`group flex space-x-4 md:space-x-6 py-6 ${!isLast ? 'border-b border-[var(--border-color)]' : ''} animate-in fade-in duration-500`}>
            {/* Avatar */}
            <div className="flex-shrink-0">
                {isUser ? (
                    <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center shadow-[0_0_15px_rgba(79,70,229,0.2)]">
                        <UserCircleIcon className="w-6 h-6 text-indigo-400" />
                    </div>
                ) : (
                    <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shadow-[0_0_15px_rgba(16,185,129,0.15)] relative overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/20 to-transparent opacity-50" />
                        <SparklesIcon className="w-5 h-5 text-emerald-400 relative z-10" />
                    </div>
                )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0 space-y-2">
                {/* Header */}
                <div className="flex items-center space-x-2">
                    <h3 className={`text-sm font-semibold tracking-wide ${isUser ? 'text-indigo-400' : 'text-emerald-400'}`}>
                        {isUser ? 'You' : 'AI Assistant'}
                    </h3>
                    <span className="text-xs text-[var(--text-muted)] px-1.5 py-0.5 rounded border border-[var(--border-color)] bg-[var(--bg-tertiary)] uppercase tracking-wider font-mono">
                        {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                </div>

                {/* Body */}
                {isUser ? (
                    <div className="text-[15px] leading-relaxed text-[var(--text-primary)] font-medium bg-brand-indigo/10 dark:bg-gray-800/40 p-3 rounded-r-xl rounded-bl-xl border border-brand-indigo/20 dark:border-gray-700/50 inline-block">
                        <p className="whitespace-pre-wrap">{message.content}</p>
                    </div>
                ) : (
                    <MessageContent content={message.content} isAnimated={shouldAnimate} />
                )}

                {/* Interactive Elements (Query/Results) */}
                {message.query && (
                    <div className="mt-4 max-w-2xl">
                        <QueryConfirmation
                            query={message.query}
                            onExecute={onExecuteQuery}
                            onCancel={() => { }} // No-op for now, styled in parent
                        />
                    </div>
                )}

                {message.results && (
                    <div className="mt-4 w-full overflow-hidden">
                        <ChatResults
                            results={message.results}
                            onVisualize={onVisualize}
                            showChart={visibleCharts}
                            chartConfig={chartConfig}
                        />
                    </div>
                )}

                {/* Assistant Footer Actions */}
                {isAssistant && (
                    <div className="flex items-center space-x-2 mt-2 pt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button className="p-1.5 text-[var(--text-muted)] hover:text-[var(--text-primary)] rounded hover:bg-[var(--bg-tertiary)]" title="Copy">
                            <ClipboardDocumentIcon className="w-4 h-4" />
                        </button>
                        <button className="p-1.5 text-[var(--text-muted)] hover:text-[var(--text-primary)] rounded hover:bg-[var(--bg-tertiary)]" title="Good response">
                            <HandThumbUpIcon className="w-4 h-4" />
                        </button>
                        <button className="p-1.5 text-[var(--text-muted)] hover:text-[var(--text-primary)] rounded hover:bg-[var(--bg-tertiary)]" title="Bad response">
                            <HandThumbDownIcon className="w-4 h-4" />
                        </button>
                        <button className="flex items-center space-x-1 px-2 py-1 ml-2 text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] rounded hover:bg-[var(--bg-tertiary)]">
                            <ArrowPathIcon className="w-3 h-3" />
                            <span>Regenerate</span>
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ChatMessage;
