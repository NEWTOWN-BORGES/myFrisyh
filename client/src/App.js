import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import HomePage from './pages/HomePage';
import CourseDetailPage from './pages/CourseDetailPage';

/**
 * Componente principal da aplicação.
 * Configura o roteamento para as diferentes páginas.
 */
function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>PlayLista</h1>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/course/:courseId" element={<CourseDetailPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
