import React, { useState } from 'react';
import { Dialog } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useMcpStore } from 'stores/mcpStore';

const MCPConnectionModal = ({ isOpen, onClose }) => {
    const { addConnection } = useMcpStore();
    const [name, setName] = useState('');
    const [url, setUrl] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        const success = await addConnection({ name, url });
        setIsSubmitting(false);
        if (success) {
            setName('');
            setUrl('');
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
