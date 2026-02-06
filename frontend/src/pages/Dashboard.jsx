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
    <div className="flex h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] font-sans transition-colors">
      <Sidebar />
      <div className="flex flex-col flex-1">
        <Header />
        <MainPanel />
      </div>
    </div>
  );
};

export default Dashboard;