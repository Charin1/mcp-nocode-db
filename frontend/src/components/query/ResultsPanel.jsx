import React from 'react';
import { useDbStore } from 'stores/dbStore';
import Spinner from 'components/common/Spinner';
import Table from 'components/common/Table';
import JsonViewer from 'components/common/JsonViewer';

const ResultsPanel = () => {
  const { queryResult, isQuerying } = useDbStore();

  const renderContent = () => {
    if (isQuerying) {
      return (
        <div className="flex items-center justify-center h-full">
          <Spinner />
          <span className="ml-4 text-lg">Executing query...</span>
        </div>
      );
    }

    if (!queryResult) {
      return (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-500">Query results will appear here.</p>
        </div>
      );
    }

    if (queryResult.error) {
      return (
        <div className="p-4 text-red-400 bg-red-900/20 rounded-md overflow-auto">
          <h3 className="font-bold">Execution Error</h3>
          <pre className="mt-2 text-sm whitespace-pre-wrap">{queryResult.error}</pre>
        </div>
      );
    }

    if (queryResult.rows) {
      return <Table columns={queryResult.columns} data={queryResult.rows} />;
    }

    if (queryResult.json_result) {
      return <JsonViewer data={queryResult.json_result} />;
    }

    return (
      <div className="p-4 text-green-400 bg-green-900/20 rounded-md">
        <h3 className="font-bold">Success</h3>
        <p>{queryResult.message || `Rows affected: ${queryResult.rows_affected}`}</p>
      </div>
    );
  };

  return (
    <div className="h-full bg-gray-900 border border-gray-700 rounded-lg overflow-auto">
      {renderContent()}
    </div>
  );
};

export default ResultsPanel;