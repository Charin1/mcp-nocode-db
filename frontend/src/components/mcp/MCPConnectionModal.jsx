import React, { useState, useEffect } from 'react';
import { Dialog } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useMcpStore } from 'stores/mcpStore';

const MCPConnectionModal = ({ isOpen, onClose, editingConnection }) => {
    const { addConnection, updateConnection } = useMcpStore();
    const [name, setName] = useState('');

    // SSE State
    const [url, setUrl] = useState('');

    // Stdio State
    const [connectionType, setConnectionType] = useState('sse'); // 'sse' or 'stdio'
    const [command, setCommand] = useState('');
    const [args, setArgs] = useState('');
    const [env, setEnv] = useState('');
    const [headers, setHeaders] = useState('');

    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        if (editingConnection) {
            setName(editingConnection.name || '');
            setConnectionType(editingConnection.connection_type || 'sse');
            
            const config = editingConnection.configuration || {};
            if (editingConnection.connection_type === 'sse') {
                setUrl(config.url || editingConnection.url || '');
                setHeaders(editingConnection.headers ? JSON.stringify(editingConnection.headers, null, 2) : '');
                setCommand('');
                setArgs('');
                setEnv('');
            } else {
                setCommand(config.command || '');
                const rawArgs = config.args || [];
                if (Array.isArray(rawArgs)) {
                    setArgs(JSON.stringify(rawArgs));
                } else {
                    setArgs(rawArgs);
                }
                setEnv(config.env ? JSON.stringify(config.env, null, 2) : '');
                setUrl('');
                setHeaders('');
            }
        } else {
            setName('');
            setUrl('');
            setConnectionType('sse');
            setCommand('');
            setArgs('');
            setEnv('');
            setHeaders('');
        }
    }, [editingConnection, isOpen]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);

        let payload = { name, connection_type: connectionType, configuration: {}, headers: {} };

        if (connectionType === 'sse') {
            payload.url = url; // For backward compatibility
            payload.configuration = { url };
            
            // Parse headers
            if (headers.trim()) {
                try {
                    payload.headers = JSON.parse(headers);
                } catch (e) {
                    alert("Invalid JSON for headers");
                    setIsSubmitting(false);
                    return;
                }
            }
        } else {
            // Parse args
            let parsedArgs = [];
            if (args.trim()) {
                if (args.trim().startsWith('[')) {
                    try {
                        parsedArgs = JSON.parse(args);
                    } catch (e) {
                        alert("Invalid JSON for arguments");
                        setIsSubmitting(false);
                        return;
                    }
                } else {
                    parsedArgs = args.split(' ').filter(a => a);
                }
            }

            // Parse env
            let parsedEnv = {};
            if (env.trim()) {
                try {
                    parsedEnv = JSON.parse(env);
                } catch (e) {
                    alert("Invalid JSON for environment variables");
                    setIsSubmitting(false);
                    return;
                }
            }

            payload.configuration = {
                command,
                args: parsedArgs,
                env: parsedEnv
            };
        }

        const success = editingConnection
            ? await updateConnection(editingConnection.id, payload)
            : await addConnection(payload);
            
        setIsSubmitting(false);
        if (success) {
            setName('');
            setUrl('');
            setCommand('');
            setArgs('');
            setEnv('');
            setHeaders('');
            onClose();
        }
    };

    return (
        <Dialog open={isOpen} onClose={onClose} className="relative z-50">
            <div className="fixed inset-0 bg-black/30" aria-hidden="true" />

            <div className="fixed inset-0 flex items-center justify-center p-4">
                <Dialog.Panel className="w-full max-w-md p-6 bg-[var(--bg-secondary)] rounded-lg shadow-xl border border-[var(--border-color)]">
                    <div className="flex items-center justify-between mb-4">
                        <Dialog.Title className="text-lg font-medium text-[var(--text-primary)]">
                            {editingConnection ? 'Edit MCP Connection' : 'Add MCP Connection'}
                        </Dialog.Title>
                        <button onClick={onClose} className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
                            <XMarkIcon className="w-6 h-6" />
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-[var(--text-secondary)]">Name</label>
                            <input
                                type="text"
                                required
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="w-full px-3 py-2 mt-1 text-[var(--text-primary)] bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-md focus:outline-none focus:ring-2 focus:ring-brand-indigo transition-colors"
                                placeholder="e.g. Local Server"
                            />
                        </div>
                        {/* Connection Type Selector */}
                        <div>
                            <label className="block text-sm font-medium text-[var(--text-secondary)]">Connection Type</label>
                            <div className="flex mt-1 space-x-4">
                                <label className="inline-flex items-center cursor-pointer">
                                    <input
                                        type="radio"
                                        className="form-radio text-brand-indigo bg-[var(--bg-tertiary)] border-[var(--border-color)] focus:ring-brand-indigo"
                                        name="connectionType"
                                        value="sse"
                                        checked={connectionType === 'sse'}
                                        onChange={() => setConnectionType('sse')}
                                    />
                                    <span className="ml-2 text-[var(--text-primary)]">SSE (Remote URL)</span>
                                </label>
                                <label className="inline-flex items-center cursor-pointer">
                                    <input
                                        type="radio"
                                        className="form-radio text-brand-indigo bg-[var(--bg-tertiary)] border-[var(--border-color)] focus:ring-brand-indigo"
                                        name="connectionType"
                                        value="stdio"
                                        checked={connectionType === 'stdio'}
                                        onChange={() => setConnectionType('stdio')}
                                    />
                                    <span className="ml-2 text-[var(--text-primary)]">Stdio (Local Process)</span>
                                </label>
                            </div>
                        </div>

                        {connectionType === 'sse' && (
                            <>
                                <div>
                                    <label className="block text-sm font-medium text-[var(--text-secondary)]">SSE URL</label>
                                    <input
                                        type="url"
                                        required
                                        value={url}
                                        onChange={(e) => setUrl(e.target.value)}
                                        className="w-full px-3 py-2 mt-1 text-[var(--text-primary)] bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-md focus:outline-none focus:ring-2 focus:ring-brand-indigo transition-colors"
                                        placeholder="http://localhost:8000/api/mcp/sse"
                                    />
                                    <p className="mt-1 text-xs text-[var(--text-muted)]">The Server-Sent Events endpoint of the MCP server.</p>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-[var(--text-secondary)]">Custom HTTP Headers (JSON)</label>
                                    <textarea
                                        value={headers}
                                        onChange={(e) => setHeaders(e.target.value)}
                                        className="w-full px-3 py-2 mt-1 text-[var(--text-primary)] bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-md focus:outline-none focus:ring-2 focus:ring-brand-indigo transition-colors h-20 font-mono text-sm"
                                        placeholder='{"Authorization": "Bearer TOKEN"}'
                                    />
                                    <p className="mt-1 text-xs text-[var(--text-muted)]">Optional headers for authentication (e.g., Zoe, Claude API keys).</p>
                                </div>
                            </>
                        )}

                        {connectionType === 'stdio' && (
                            <>
                                <div>
                                    <label className="block text-sm font-medium text-[var(--text-secondary)]">Command</label>
                                    <input
                                        type="text"
                                        required
                                        value={command}
                                        onChange={(e) => setCommand(e.target.value)}
                                        className="w-full px-3 py-2 mt-1 text-[var(--text-primary)] bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-md focus:outline-none focus:ring-2 focus:ring-brand-indigo transition-colors"
                                        placeholder="e.g. npx, python, uvx"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-[var(--text-secondary)]">Arguments (Space separated or JSON array)</label>
                                    <input
                                        type="text"
                                        value={args}
                                        onChange={(e) => setArgs(e.target.value)}
                                        className="w-full px-3 py-2 mt-1 text-[var(--text-primary)] bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-md focus:outline-none focus:ring-2 focus:ring-brand-indigo transition-colors"
                                        placeholder='-y @modelcontextprotocol/server-memory'
                                    />
                                    <p className="mt-1 text-xs text-[var(--text-muted)]">Arguments to pass to the command.</p>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-[var(--text-secondary)]">Environment Variables (JSON)</label>
                                    <textarea
                                        value={env}
                                        onChange={(e) => setEnv(e.target.value)}
                                        className="w-full px-3 py-2 mt-1 text-[var(--text-primary)] bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-md focus:outline-none focus:ring-2 focus:ring-brand-indigo transition-colors h-20 font-mono text-sm"
                                        placeholder='{"KEY": "VALUE"}'
                                    />
                                </div>
                            </>
                        )}

                        <div className="flex justify-end pt-4 space-x-3">
                            <button
                                type="button"
                                onClick={onClose}
                                className="px-4 py-2 text-sm font-medium text-[var(--text-secondary)] bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-md hover:bg-[var(--bg-elevated)] transition-colors focus:outline-none"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="px-4 py-2 text-sm font-medium text-white bg-brand-indigo rounded-md hover:bg-opacity-90 transition-colors focus:outline-none disabled:opacity-50"
                            >
                                {isSubmitting 
                                    ? (editingConnection ? 'Saving...' : 'Adding...') 
                                    : (editingConnection ? 'Save Connection' : 'Add Connection')}
                            </button>
                        </div>
                    </form>
                </Dialog.Panel>
            </div>
        </Dialog>
    );
};

export default MCPConnectionModal;
