import React, { useState, useEffect } from 'react';
import { useDbStore } from 'stores/dbStore';
import { useMcpStore } from 'stores/mcpStore';
import { CubeIcon, TableCellsIcon, CircleStackIcon, MagnifyingGlassIcon, KeyIcon, PlusIcon, TrashIcon, LinkIcon } from '@heroicons/react/24/outline';
import Spinner from 'components/common/Spinner';
import MCPConnectionModal from 'components/mcp/MCPConnectionModal';

const getIcon = (type) => {
  switch (type) {
    case 'table':
    case 'view':
      return <TableCellsIcon className="w-5 h-5 mr-3 text-blue-400" />;
    case 'collection':
      return <CircleStackIcon className="w-5 h-5 mr-3 text-green-400" />;
    case 'index':
      return <MagnifyingGlassIcon className="w-5 h-5 mr-3 text-yellow-400" />;
    case 'key':
      return <KeyIcon className="w-5 h-5 mr-3 text-red-400" />;
    default:
      return <CubeIcon className="w-5 h-5 mr-3 text-gray-400" />;
  }
};

const Sidebar = () => {
  const { schema, isLoadingSchema, scope, globalSchema, selectedDbId, databases } = useDbStore();
  const { connections, fetchConnections, deleteConnection, isLoading, activeConnectionIds, toggleActiveConnection } = useMcpStore();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [expandedDbs, setExpandedDbs] = useState({});

  useEffect(() => {
    fetchConnections();
  }, [fetchConnections]);

  const toggleDbExpand = (dbId) => {
    setExpandedDbs(prev => ({ ...prev, [dbId]: !prev[dbId] }));
  };

  const renderSchemaList = (items) => (
    <ul className="space-y-1 ml-2 border-l border-[var(--border-subtle)] pl-2">
      {items.map(item => (
        <li key={item.name} className="flex items-center px-2 py-1.5 text-sm text-[var(--text-secondary)] rounded-md cursor-pointer hover:bg-[var(--bg-tertiary)] transition-colors">
          {getIcon(item.type)}
          <span className="truncate">{item.name}</span>
        </li>
      ))}
    </ul>
  );

  return (
    <>
      <aside className="flex flex-col w-64 bg-[var(--bg-secondary)] border-r border-[var(--border-color)] h-screen transition-colors">
        {/* Database Schema Section */}
        <div className="flex-1 flex flex-col min-h-0 border-b border-[var(--border-color)]">
          <div className="px-4 py-3 border-b border-[var(--border-color)] bg-[var(--bg-tertiary)]">
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">
              {scope === 'all' ? 'All Databases' : 'Schema Explorer'}
            </h2>
          </div>
          <div className="flex-1 p-2 overflow-y-auto">
            {isLoadingSchema ? (
              <div className="flex items-center justify-center h-20">
                <Spinner />
              </div>
            ) : (
              scope === 'all' ? (
                // All Databases Tree View
                Object.keys(globalSchema).length > 0 ? (
                  <ul className="space-y-2">
                    {Object.entries(globalSchema)
                      .filter(([dbId, dbData]) => {
                        // Filter by engine of selected DB
                        const selectedDb = databases.find(d => d.id === selectedDbId);
                        const currentEngine = selectedDb?.engine;

                        if (!currentEngine) return true; // Show all if no selection/unknown
                        return dbData.engine === currentEngine;
                      })
                      .map(([dbId, dbData]) => (
                        <li key={dbId}>
                          <div
                            className="flex items-center px-2 py-2 text-sm font-medium text-[var(--text-primary)] rounded-md cursor-pointer hover:bg-[var(--bg-tertiary)] transition-colors"
                            onClick={() => toggleDbExpand(dbId)}
                          >
                            <span className="mr-2 text-[var(--text-muted)]">
                              {expandedDbs[dbId] ? '▼' : '▶'}
                            </span>
                            <span className="truncate">{dbData.name}</span>
                          </div>
                          {expandedDbs[dbId] && dbData.schema && (
                            renderSchemaList(dbData.schema)
                          )}
                        </li>
                      ))}
                  </ul>
                ) : (
                  <div className="px-2 py-4 text-xs text-center text-[var(--text-muted)]">No databases found.</div>
                )
              ) : (
                // Current DB View
                schema.length > 0 ? (
                  <ul className="space-y-1">
                    {schema.map(item => (
                      <li key={item.name} className="flex items-center px-2 py-1.5 text-sm text-[var(--text-secondary)] rounded-md cursor-pointer hover:bg-[var(--bg-tertiary)] transition-colors">
                        {getIcon(item.type)}
                        <span className="truncate">{item.name}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <li className="list-none px-2 py-4 text-xs text-center text-[var(--text-muted)]">No schema found or database not selected.</li>
                )
              )
            )}
          </div>
        </div>

        {/* MCP Connections Section */}
        <div className="flex flex-col h-1/3 bg-[var(--bg-secondary)]">
          <div className="px-4 py-3 border-t border-b border-[var(--border-color)] bg-[var(--bg-tertiary)] flex justify-between items-center">
            <h2 className="text-sm font-semibold text-[var(--text-primary)] uppercase tracking-wider">MCP Connections</h2>
            <button
              onClick={() => setIsModalOpen(true)}
              className="p-1 text-[var(--text-muted)] hover:text-[var(--text-primary)] rounded-md hover:bg-[var(--bg-elevated)]"
              title="Add Connection"
            >
              <PlusIcon className="w-4 h-4" />
            </button>
          </div>
          <div className="flex-1 p-2 overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center p-4">
                <Spinner size="sm" />
              </div>
            ) : (
              <ul className="space-y-1">
                {connections.length > 0 ? connections.map(conn => (
                  <li key={conn.id} className="group flex items-center justify-between px-2 py-2 text-sm text-[var(--text-secondary)] rounded-md hover:bg-[var(--bg-tertiary)] transition-colors">
                    <div className="flex items-center overflow-hidden cursor-pointer flex-1" onClick={() => toggleActiveConnection(conn.id)}>
                      <input
                        type="checkbox"
                        checked={activeConnectionIds.includes(conn.id)}
                        readOnly
                        className="mr-2 rounded text-brand-indigo focus:ring-brand-indigo bg-[var(--bg-tertiary)] border-[var(--border-color)] pointer-events-none"
                      />
                      <LinkIcon className={`w-4 h-4 mr-2 flex-shrink-0 ${activeConnectionIds.includes(conn.id) ? 'text-accent-emerald' : 'text-brand-purple'}`} />
                      <span className={`truncate ${activeConnectionIds.includes(conn.id) ? 'text-[var(--text-primary)]' : ''}`} title={conn.url}>{conn.name}</span>
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); deleteConnection(conn.id); }}
                      className="opacity-0 group-hover:opacity-100 p-1 text-[var(--text-muted)] hover:text-red-400 rounded transition-opacity"
                      title="Delete"
                    >
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  </li>
                )) : (
                  <li className="px-2 py-4 text-xs text-center text-[var(--text-muted)]">No MCP connections added. Click + to add one.</li>
                )}
              </ul>
            )}
          </div>
        </div>
      </aside>

      <MCPConnectionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );
};

export default Sidebar;