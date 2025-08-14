import React from 'react';
import { useDbStore } from 'stores/dbStore';
import { CubeIcon, TableCellsIcon, CircleStackIcon, MagnifyingGlassIcon, KeyIcon } from '@heroicons/react/24/outline';
import Spinner from 'components/common/Spinner';

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
  const { schema, isLoadingSchema } = useDbStore();

  return (
    <aside className="flex flex-col w-64 bg-gray-900 border-r border-gray-700">
      <div className="px-4 py-3 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-white">Schema Explorer</h2>
      </div>
      <div className="flex-1 p-4 overflow-y-auto">
        {isLoadingSchema ? (
          <div className="flex items-center justify-center h-full">
            <Spinner />
          </div>
        ) : (
          <ul className="space-y-2">
            {schema.length > 0 ? schema.map(item => (
              <li key={item.name} className="flex items-center p-2 text-sm text-gray-300 rounded-md cursor-pointer hover:bg-gray-700">
                {getIcon(item.type)}
                <span className="truncate">{item.name}</span>
              </li>
            )) : (
              <li className="text-sm text-center text-gray-500">No schema found or database not selected.</li>
            )}
          </ul>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;