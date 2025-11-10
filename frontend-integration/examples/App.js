/**
 * Example App.js showing how to integrate the Skill Extraction feature
 * This is a complete example showing routing and component usage
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import SimpleInternshipForm from './components/SimpleInternshipForm';
import CreateInternshipForm from './components/CreateInternshipForm';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        {/* Navigation */}
        <nav className="navbar">
          <div className="nav-container">
            <Link to="/" className="nav-brand">Skill Sync</Link>
            <div className="nav-links">
              <Link to="/create-simple" className="nav-link">Create Internship (Simple)</Link>
              <Link to="/create-full" className="nav-link">Create Internship (Full)</Link>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/create-simple" element={<SimpleInternshipForm />} />
            <Route path="/create-full" element={<CreateInternshipForm />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

function Home() {
  return (
    <div className="home">
      <h1>Welcome to Skill Sync</h1>
      <p>AI-powered internship matching platform</p>
      
      <div className="feature-cards">
        <div className="card">
          <h3>🔍 AI Skill Extraction</h3>
          <p>Automatically extract required and preferred skills from job descriptions</p>
          <Link to="/create-simple" className="card-link">Try it now →</Link>
        </div>
        
        <div className="card">
          <h3>⚡ Fast & Accurate</h3>
          <p>Powered by Google Gemini AI for intelligent skill categorization</p>
        </div>
        
        <div className="card">
          <h3>✏️ Easy to Edit</h3>
          <p>Review and customize extracted skills before posting</p>
        </div>
      </div>
    </div>
  );
}

export default App;
