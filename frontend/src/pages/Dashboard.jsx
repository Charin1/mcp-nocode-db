import Header from 'components/layout/Header';
import Sidebar from 'components/layout/Sidebar';
import MainPanel from 'components/layout/MainPanel';
import { useDbStore } from 'stores/dbStore';
import { useEffect } from 'react';

const Dashboard = () => {
  const fetchAppConfig = useDbStore(state => state.fetchAppConfig);

  useEffect(() => {
    fetchAppConfig();
  }, [fetchAppConfig]);

  return (
    <div className="flex h-screen bg-gray-800 text-gray-200 font-sans">
      <Sidebar />
      <div className="flex flex-col flex-1">
        <Header />
        <MainPanel />
      </div>
    </div>
  );
};

export default Dashboard;