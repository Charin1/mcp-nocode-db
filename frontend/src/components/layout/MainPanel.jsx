import React from 'react';
import QueryConsole from 'components/query/QueryConsole';
import ResultsPanel from 'components/query/ResultsPanel';

const MainPanel = () => {
  return (
    <main className="flex flex-col flex-1 p-4 overflow-hidden">
      <div className="flex flex-col flex-1 h-full space-y-4">
        {/* Top half: Query Console */}
        <div className="flex-1 h-1/2">
          <QueryConsole />
        </div>
        {/* Bottom half: Results Panel */}
        <div className="flex-1 h-1/2">
          <ResultsPanel />
        </div>
      </div>
    </main>
  );
};

export default MainPanel;