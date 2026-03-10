import { useState } from 'react';
import { Layout } from './components/Layout';
import { DashboardView } from './components/DashboardView';
import { ProjectionsView } from './components/ProjectionsView';

function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'projections'>('dashboard');

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {activeTab === 'dashboard' ? <DashboardView /> : <ProjectionsView />}
    </Layout>
  );
}

export default App;
