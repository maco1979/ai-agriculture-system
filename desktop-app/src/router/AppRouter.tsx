import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// 懒加载组件
const Home = React.lazy(() => import('../pages/Home'));
const DataAnalysis = React.lazy(() => import('../pages/DataAnalysis'));
const PredictionModel = React.lazy(() => import('../pages/PredictionModel'));
const DecisionSuggestion = React.lazy(() => import('../pages/DecisionSuggestion'));
const SystemSettings = React.lazy(() => import('../pages/SystemSettings'));

// 加载占位组件
const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
    <div className="text-white text-2xl">加载中...</div>
  </div>
);

const AppRouter = () => {
  return (
    <Router>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/data-analysis" element={<DataAnalysis />} />
          <Route path="/prediction-model" element={<PredictionModel />} />
          <Route path="/decision-suggestion" element={<DecisionSuggestion />} />
          <Route path="/system-settings" element={<SystemSettings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </Router>
  );
};

export default AppRouter;