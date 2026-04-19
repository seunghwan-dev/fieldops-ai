import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider } from './contexts/AppContext';
import Navbar from './components/layout/Navbar';
import KnowledgePage from './pages/KnowledgePage';
import SearchPage from './pages/SearchPage';
import FusionPage from './pages/FusionPage';

function App() {
  return (
    <AppProvider>
      <BrowserRouter basename={import.meta.env.BASE_URL}>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
          <Navbar />
          <main className="max-w-7xl mx-auto px-4 py-6">
            <Routes>
              <Route path="/knowledge" element={<KnowledgePage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/fusion" element={<FusionPage />} />
              <Route path="*" element={<Navigate to="/knowledge" replace />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </AppProvider>
  );
}

export default App;
