import React, { useState } from 'react';
import { Dialog } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useMcpStore } from 'stores/mcpStore';

const MCPConnectionModal = ({ isOpen, onClose }) => {
    const { addConnection } = useMcpStore();
    const [name, setName] = useState('');

    // SSE State
    const [url, setUrl] = useState('');

    // Stdio State
    const [connectionType, setConnectionType] = useState('sse'); // 'sse' or 'stdio'
    const [command, setCommand] = useState('');
    const [args, setArgs] = useState('');
    const [env, setEnv] = useState('');

    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);

        let payload = { name, connection_type: connectionType, configuration: {} };

        if (connectionType === 'sse') {
            payload.url = url; // For backward compatibility
            payload.configuration = { url };
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

        const success = await addConnection(payload);
        setIsSubmitting(false);
        if (success) {
            setName('');
            setUrl('');
            setCommand('');
            setArgs('');
            setEnv('');
            onClose();
        }
    };

    return (
        <Dialog open={isOpen} onClose={onClose} className="relative z-50">
            <div className="fixed inset-0 bg-black/30" aria-hidden="true" />

            <div className="fixed inset-0 flex items-center justify-center p-4">
                <Dialog.Panel className="w-full max-w-md p-6 bg-gray-800 rounded-lg shadow-xl border border-gray-700">
                    <div className="flex items-center justify-between mb-4">
                        <Dialog.Title className="text-lg font-medium text-white">
                            Add MCP Connection
                        </Dialog.Title>
                        <button onClick={onClose} className="text-gray-400 hover:text-gray-200">
                            <XMarkIcon className="w-6 h-6" />
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-300">Name</label>
                            <input
                                type="text"
                                required
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="w-full px-3 py-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="e.g. Local Server"
                            />
                        </div>
                        {/* Connection Type Selector */}
                        <div>
                            <label className="block text-sm font-medium text-gray-300">Connection Type</label>
                            <div className="flex mt-1 space-x-4">
                                <label className="inline-flex items-center">
                                    <input
                                        type="radio"
                                        className="form-radio text-blue-600"
                                        name="connectionType"
                                        value="sse"
                                        checked={connectionType === 'sse'}
                                        onChange={() => setConnectionType('sse')}
                                    />
                                    <span className="ml-2 text-white">SSE (Remote URL)</span>
                                </label>
                                <label className="inline-flex items-center">
                                    <input
                                        type="radio"
                                        className="form-radio text-blue-600"
                                        name="connectionType"
                                        value="stdio"
                                        checked={connectionType === 'stdio'}
                                        onChange={() => setConnectionType('stdio')}
                                    />
                                    <span className="ml-2 text-white">Stdio (Local Process)</span>
                                </label>
                            </div>
                        </div>

                        {connectionType === 'sse' && (
                            <div>
                                <label className="block text-sm font-medium text-gray-300">SSE URL</label>
                                <input
                                    type="url"
                                    required
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                    className="w-full px-3 py-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="http://localhost:8000/api/mcp/sse"
                                />
                                <p className="mt-1 text-xs text-gray-500">The Server-Sent Events endpoint of the MCP server.</p>
                            </div>
                        )}

                        {connectionType === 'stdio' && (
                            <>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300">Command</label>
                                    <input
                                        type="text"
                                        required
                                        value={command}
                                        onChange={(e) => setCommand(e.target.value)}
                                        className="w-full px-3 py-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="e.g. npx, python, uvx"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300">Arguments (Space separated or JSON array)</label>
                                    <input
                                        type="text"
                                        value={args}
                                        onChange={(e) => setArgs(e.target.value)}
                                        className="w-full px-3 py-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder='-y @modelcontextprotocol/server-memory'
                                    />
                                    <p className="mt-1 text-xs text-gray-500">Arguments to pass to the command.</p>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300">Environment Variables (JSON)</label>
                                    <textarea
                                        value={env}
                                        onChange={(e) => setEnv(e.target.value)}
                                        className="w-full px-3 py-2 mt-1 text-white bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 h-20"
                                        placeholder='{"KEY": "VALUE"}'
                                    />
                                </div>
                            </>
                        )}

                        <div className="flex justify-end pt-4">
                            <button
                                type="button"
                                onClick={onClose}
                                className="px-4 py-2 mr-2 text-sm font-medium text-gray-300 bg-gray-700 rounded-md hover:bg-gray-600 focus:outline-none"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-500 focus:outline-none disabled:opacity-50"
                            >
                                {isSubmitting ? 'Adding...' : 'Add Connection'}
                            </button>
                        </div>
                    </form>
                </Dialog.Panel>
            </div>
        </Dialog>
    );
};

export default MCPConnectionModal;
