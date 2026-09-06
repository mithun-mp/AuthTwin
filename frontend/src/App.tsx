import React, { useState } from 'react';
import { Layout } from './components/Layout';
import { Overview } from './pages/Overview';
import { Traffic } from './pages/Traffic';
import { Identities } from './pages/Identities';
import { Sessions } from './pages/Sessions';
import { OpenAPI } from './pages/OpenAPI';
import { Dependencies } from './pages/Dependencies';
import { Workflows } from './pages/Workflows';
import { ShadowWorkflows } from './pages/ShadowWorkflows';
import { TargetSandbox } from './pages/TargetSandbox';
import { LogEntry } from './components/TerminalConsole';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [logs, setLogs] = useState<LogEntry[]>([
    {
      id: '1',
      timestamp: new Date().toLocaleTimeString(),
      type: 'SECURITY',
      module: 'DWA-SSA',
      message: 'AuthTwin Security Workstation v1.0 initialized under Credential Isolation Policy.'
    },
    {
      id: '2',
      timestamp: new Date().toLocaleTimeString(),
      type: 'INFO',
      module: 'MILESTONE_1',
      message: 'Workflow State Graph Engine ready. Shadow Workflow construction set to MODEL ONLY.'
    }
  ]);

  const handleLogEvent = (type: 'INFO' | 'SUCCESS' | 'WARN' | 'SECURITY', module: string, message: string) => {
    const newEntry: LogEntry = {
      id: String(Date.now()),
      timestamp: new Date().toLocaleTimeString(),
      type,
      module,
      message
    };
    setLogs(prev => [newEntry, ...prev.slice(0, 49)]);
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'overview': return <Overview onLogEvent={handleLogEvent} />;
      case 'sandbox': return <TargetSandbox onLogEvent={handleLogEvent} onNavigateToWorkflows={() => setActiveTab('workflows')} />;
      case 'traffic': return <Traffic />;
      case 'identities': return <Identities />;
      case 'sessions': return <Sessions />;
      case 'openapi': return <OpenAPI />;
      case 'dependencies': return <Dependencies />;
      case 'workflows': return <Workflows />;
      case 'shadow': return <ShadowWorkflows />;
      default: return <Overview onLogEvent={handleLogEvent} />;
    }
  };

  return (
    <Layout activeTab={activeTab} setActiveTab={setActiveTab} logs={logs}>
      {renderContent()}
    </Layout>
  );
};

export default App;
