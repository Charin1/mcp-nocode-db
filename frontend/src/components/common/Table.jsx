import React, { useMemo } from 'react';
import { useTable, useSortBy, usePagination } from 'react-table';
import { ChevronUpIcon, ChevronDownIcon, ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/solid';

const Table = ({ columns: userColumns, data }) => {
  const columns = useMemo(() => {
    if (!data || data.length === 0) return [];
    // Create columns from the keys of the first data row
    return Object.keys(data[0]).map(key => ({
      Header: key,
      accessor: key,
    }));
  }, [data]);

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    page,
    prepareRow,
    canPreviousPage,
    canNextPage,
    pageOptions,
    pageCount,
    gotoPage,
    nextPage,
    previousPage,
    setPageSize,
    state: { pageIndex, pageSize },
  } = useTable(
    {
      columns,
      data,
      initialState: { pageIndex: 0, pageSize: 10 },
    },
    useSortBy,
    usePagination
  );

  if (!data || data.length === 0) {
    return <div className="p-4 text-center text-gray-500">No data to display.</div>;
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-grow overflow-auto">
        <table {...getTableProps()} className="min-w-full divide-y divide-gray-700">
          <thead className="bg-gray-800">
            {headerGroups.map(headerGroup => (
              <tr {...headerGroup.getHeaderGroupProps()}>
                {headerGroup.headers.map(column => (
                  <th
                    {...column.getHeaderProps(column.getSortByToggleProps())}
                    className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider"
                  >
                    <span className="flex items-center">
                      {column.render('Header')}
                      {column.isSorted ? (
                        column.isSortedDesc ? (
                          <ChevronDownIcon className="w-4 h-4 ml-2" />
                        ) : (
                          <ChevronUpIcon className="w-4 h-4 ml-2" />
                        )
                      ) : (
                        ''
                      )}
                    </span>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody {...getTableBodyProps()} className="bg-gray-900 divide-y divide-gray-800">
            {page.map(row => {
              prepareRow(row);
              return (
                <tr {...row.getRowProps()} className="hover:bg-gray-800">
                  {row.cells.map(cell => (
                    <td {...cell.getCellProps()} className="px-6 py-4 whitespace-nowrap text-sm text-gray-200">
                      {typeof cell.value === 'object' ? JSON.stringify(cell.value) : String(cell.value)}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {/* Pagination */}
      <div className="p-2 bg-gray-900 border-t border-gray-700 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button onClick={() => gotoPage(0)} disabled={!canPreviousPage} className="p-1 disabled:opacity-50">
            <ChevronLeftIcon className="w-5 h-5" />
          </button>
          <button onClick={() => previousPage()} disabled={!canPreviousPage} className="p-1 disabled:opacity-50">
            <ChevronLeftIcon className="w-4 h-4" />
          </button>
          <span className="text-sm">
            Page{' '}
            <strong>
              {pageIndex + 1} of {pageOptions.length}
            </strong>
          </span>
          <button onClick={() => nextPage()} disabled={!canNextPage} className="p-1 disabled:opacity-50">
            <ChevronRightIcon className="w-4 h-4" />
          </button>
          <button onClick={() => gotoPage(pageCount - 1)} disabled={!canNextPage} className="p-1 disabled:opacity-50">
            <ChevronRightIcon className="w-5 h-5" />
          </button>
        </div>
        <select
          value={pageSize}
          onChange={e => setPageSize(Number(e.target.value))}
          className="p-1 text-sm text-white bg-gray-800 border border-gray-600 rounded-md"
        >
          {[10, 20, 50, 100].map(size => (
            <option key={size} value={size}>
              Show {size}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};

export default Table;