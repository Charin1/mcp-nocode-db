import React, { useState, useEffect } from 'react';
import { Dialog } from '@headlessui/react';
import { XMarkIcon, DocumentTextIcon, CpuChipIcon } from '@heroicons/react/24/outline';

const ProjectModal = ({ isOpen, onClose, project, onSave }) => {
    const [name, setName] = useState('');
    const [systemPrompt, setSystemPrompt] = useState('');
    const [knowledgeText, setKnowledgeText] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        if (project) {
            setName(project.name || '');
            setSystemPrompt(project.system_prompt || '');
            setKnowledgeText(project.knowledge_text || '');
        } else {
            setName('');
            setSystemPrompt('');
            setKnowledgeText('');
        }
    }, [project, isOpen]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        try {
            await onSave({
                id: project?.id,
                name: name,
                system_prompt: systemPrompt,
                knowledge_text: knowledgeText
            });
            onClose();
        } catch (error) {
            console.error("Failed to save project settings", error);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <Dialog open={isOpen} onClose={onClose} className="relative z-50">
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" aria-hidden="true" />
            <div className="fixed inset-0 flex items-center justify-center p-4">
                <Dialog.Panel className="w-full max-w-2xl bg-[var(--bg-secondary)] rounded-xl shadow-2xl border border-[var(--border-color)] overflow-hidden flex flex-col max-h-[90vh]">
                    
                    {/* Header */}
                    <div className="px-6 py-4 border-b border-[var(--border-color)] flex items-center justify-between bg-[var(--bg-tertiary)]">
                        <div>
                            <Dialog.Title className="text-xl font-bold text-[var(--text-primary)]">
                                {project ? 'Edit Project Settings' : 'Create New Project'}
                            </Dialog.Title>
                            <p className="text-sm text-[var(--text-muted)] mt-1">
                                Customize the AI's behavior and provide reference knowledge.
                            </p>
                        </div>
                        <button onClick={onClose} className="p-2 rounded-full hover:bg-[var(--bg-elevated)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
                            <XMarkIcon className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Content */}
                    <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
                        
                        {/* Name Field */}
                        <div>
                            <label className="block text-sm font-semibold text-[var(--text-secondary)] mb-2">Project Name</label>
                            <input
                                type="text"
                                required
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="w-full px-4 py-2.5 bg-[var(--bg-primary)] border border-[var(--border-color)] text-[var(--text-primary)] rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-indigo transition-shadow font-medium"
                                placeholder="e.g. Finance Analytics Q3"
                            />
                        </div>

                        {/* System Prompt Field */}
                        <div className="bg-[var(--bg-tertiary)] rounded-xl p-5 border border-[var(--border-subtle)]">
                            <div className="flex items-center mb-3">
                                <div className="p-1.5 bg-brand-purple/20 text-brand-purple rounded-md mr-3">
                                    <CpuChipIcon className="w-5 h-5" />
                                </div>
                                <div>
                                    <label className="block text-sm font-semibold text-[var(--text-primary)]">System Prompt</label>
                                    <p className="text-xs text-[var(--text-muted)]">Instructions that guide how the AI behaves for all chats in this project.</p>
                                </div>
                            </div>
                            <textarea
                                value={systemPrompt}
                                onChange={(e) => setSystemPrompt(e.target.value)}
                                className="w-full h-32 px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-purple transition-shadow resize-none font-mono"
                                placeholder="e.g. Always respond as a strict financial auditor. Only provide tables, no pleasantries."
                            />
                        </div>

                        {/* Knowledge Text Field */}
                        <div className="bg-[var(--bg-tertiary)] rounded-xl p-5 border border-[var(--border-subtle)]">
                            <div className="flex items-center mb-3">
                                <div className="p-1.5 bg-brand-indigo/20 text-brand-indigo rounded-md mr-3">
                                    <DocumentTextIcon className="w-5 h-5" />
                                </div>
                                <div>
                                    <label className="block text-sm font-semibold text-[var(--text-primary)]">Knowledge Document (Text)</label>
                                    <p className="text-xs text-[var(--text-muted)]">Raw text context that the AI can reference when answering questions.</p>
                                </div>
                            </div>
                            <textarea
                                value={knowledgeText}
                                onChange={(e) => setKnowledgeText(e.target.value)}
                                className="w-full h-48 px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-indigo transition-shadow resize-none"
                                placeholder="Paste relevant guidelines, definitions, or documentation here..."
                            />
                        </div>

                    </form>

                    {/* Footer */}
                    <div className="px-6 py-4 border-t border-[var(--border-color)] bg-[var(--bg-tertiary)] flex justify-end space-x-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-5 py-2.5 text-sm font-medium text-[var(--text-secondary)] bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg hover:bg-[var(--bg-elevated)] transition-colors focus:outline-none"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={isSubmitting || !name.trim()}
                            className="px-5 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-brand-indigo to-brand-purple rounded-lg hover:opacity-90 transition-opacity focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
                        >
                            {isSubmitting ? 'Saving...' : 'Save Project'}
                        </button>
                    </div>

                </Dialog.Panel>
            </div>
        </Dialog>
    );
};

export default ProjectModal;
