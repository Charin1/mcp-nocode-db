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

const ChatResults = ({ results, onVisualize, showChart, chartConfig }) => {
    // Identify if it's a JSON result (Mongo/Redis) or Table result (SQL)
    // Backend sends json_result: null for SQL queries, so we must exclude null.
    const isJsonResult = results.json_result !== undefined && results.json_result !== null;

    if (isJsonResult) {
        return (
            <div className="mt-4 bg-gray-900 rounded-lg p-4 border border-gray-700 overflow-x-auto">
                <pre className="text-xs text-green-400 font-mono">
                    {JSON.stringify(results.json_result, null, 2)}
                </pre>
            </div>
        );
    }

    if (!results || !results.rows || results.rows.length === 0) {
        return <p className="text-sm text-gray-400 mt-2 italic">Query executed successfully, but returned no rows.</p>;
    }

    const columnDefs = results.columns.map(col => ({ field: col, sortable: true, filter: true, resizable: true }));
    const rowData = results.rows;

    return (
        <div className="mt-4 animate-fade-in-up">
            <div className="ag-theme-alpine-dark rounded-lg overflow-hidden border border-gray-700 shadow-lg" style={{ height: 350, width: '100%' }}>
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
                <div className="mt-4 p-4 bg-gray-900/50 rounded-xl border border-gray-700">
                    <ChartVisualization results={results} chartConfig={chartConfig} />
                </div>
            )}
        </div>
    );
};

const QueryConfirmation = ({ query, onExecute, onCancel }) => {
    return (
        <div className="mt-4 mb-2 p-0 rounded-xl bg-gray-900 border border-gray-700 overflow-hidden shadow-md">
            <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
                <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Generated Query</span>
                <div className="flex space-x-1">
                    <div className="w-2.5 h-2.5 rounded-full bg-red-500/50"></div>
                    <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50"></div>
                    <div className="w-2.5 h-2.5 rounded-full bg-green-500/50"></div>
                </div>
            </div>
            <div className="bg-[#0d1117] p-1">
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
            <div className="px-4 py-3 bg-gray-800 border-t border-gray-700 flex justify-end space-x-3">
                <button
                    onClick={onCancel}
                    className="px-4 py-1.5 text-xs font-medium text-gray-300 hover:text-white hover:bg-gray-700 rounded-md transition-colors"
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

const ChatMessage = ({ message, onExecuteQuery, onVisualize, visibleCharts, chartConfig, isLast }) => {
    const isUser = message.role === 'user';
    const isAssistant = message.role === 'assistant';

    return (
        <div className={`group flex space-x-4 md:space-x-6 py-6 ${!isLast ? 'border-b border-gray-800/50' : ''}`}>
            {/* Avatar */}
            <div className="flex-shrink-0">
                {isUser ? (
                    <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-900/20">
                        {/* Placeholder for user avatar if available, else icon */}
                        <UserCircleSolid className="w-6 h-6 text-white" />
                    </div>
                ) : (
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-900/20">
                        <SparklesIcon className="w-5 h-5 text-white" />
                    </div>
                )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0 space-y-1">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-200">
                        {isUser ? 'You' : 'No-Code DB AI'}
                    </h3>
                    {isUser && (
                        <button className="opacity-0 group-hover:opacity-100 p-1 text-gray-500 hover:text-gray-300 transition-opacity">
                            <PencilSquareIcon className="w-4 h-4" />
                        </button>
                    )}
                </div>

                {/* Body */}
                <div className={`text-[15px] leading-relaxed ${isUser ? 'text-gray-100 font-medium' : 'text-gray-300'}`}>
                    <p className="whitespace-pre-wrap">{message.content}</p>
                </div>

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
                        <button className="p-1.5 text-gray-500 hover:text-gray-300 rounded hover:bg-gray-800" title="Copy">
                            <ClipboardDocumentIcon className="w-4 h-4" />
                        </button>
                        <button className="p-1.5 text-gray-500 hover:text-gray-300 rounded hover:bg-gray-800" title="Good response">
                            <HandThumbUpIcon className="w-4 h-4" />
                        </button>
                        <button className="p-1.5 text-gray-500 hover:text-gray-300 rounded hover:bg-gray-800" title="Bad response">
                            <HandThumbDownIcon className="w-4 h-4" />
                        </button>
                        <button className="flex items-center space-x-1 px-2 py-1 ml-2 text-xs text-gray-500 hover:text-gray-300 rounded hover:bg-gray-800">
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
