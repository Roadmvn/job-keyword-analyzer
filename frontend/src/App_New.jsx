/**
 * Application principale Job Keywords Analyzer - Version Refactorisée
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Composants Layout
import Header from './components/Layout/Header';

// Composants Dashboard
import Dashboard from './components/Dashboard/Dashboard';

// Composants Search
import Search from './components/Search/Search';

// Configuration API
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  // États globaux
  const [stats, setStats] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [keywords, setKeywords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // États pour la recherche
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [correctedQuery, setCorrectedQuery] = useState('');
  
  // États pour l'analyse
  const [analysisResults, setAnalysisResults] = useState(null);
  const [userSkills, setUserSkills] = useState('');
  const [cvSuggestions, setCvSuggestions] = useState(null);

  // États pour le scraping
  const [scrapingJobs, setScrapingJobs] = useState([]);
  const [scrapingLoading, setScrapingLoading] = useState(false);

  // Chargement initial des données
  useEffect(() => {
    fetchData();
  }, []);

  /**
   * Récupère les données principales de l'application
   */
  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsRes, jobsRes, keywordsRes] = await Promise.all([
        axios.get(`${API_URL}/api/stats`),
        axios.get(`${API_URL}/api/jobs?limit=5`),
        axios.get(`${API_URL}/api/keywords?limit=10`)
      ]);
      
      setStats(statsRes.data);
      setJobs(jobsRes.data);
      setKeywords(keywordsRes.data);
    } catch (error) {
      console.error('Erreur lors du chargement:', error);
      // TODO: Afficher une notification d'erreur
    } finally {
      setLoading(false);
    }
  };

  /**
   * Ajoute des données de test
   */
  const populateTestData = async () => {
    try {
      await axios.post(`${API_URL}/api/test/populate`);
      // TODO: Remplacer alert par une notification
      alert('✅ Données de test ajoutées!');
      fetchData();
    } catch (error) {
      console.error('Erreur lors de l\'ajout des données de test:', error);
      alert('❌ Erreur lors de l\'ajout des données de test');
    }
  };

  /**
   * Effectue une recherche d'offres d'emploi
   */
  const searchJobs = async (query = searchQuery) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    try {
      setSearchLoading(true);
      const response = await axios.get(`${API_URL}/api/search`, {
        params: { q: query, limit: 20 }
      });
      
      setSearchResults(response.data.results || []);
      setCorrectedQuery(response.data.corrected_query);
      setSuggestions(response.data.suggestions || []);
      
      if (response.data.corrected_query !== query) {
        console.log(`🔧 Requête corrigée: "${query}" → "${response.data.corrected_query}"`);
      }
    } catch (error) {
      console.error('Erreur de recherche:', error);
      setSearchResults([]);
      // TODO: Afficher une notification d'erreur
    } finally {
      setSearchLoading(false);
    }
  };

  /**
   * Lance l'analyse NLP d'une offre d'emploi
   */
  const analyzeJobKeywords = async (jobId) => {
    try {
      const response = await axios.post(`${API_URL}/api/analyze/job/${jobId}`);
      setAnalysisResults(response.data);
      setActiveTab('analysis'); // Basculer vers l'onglet analyse
      // TODO: Remplacer alert par une notification
      alert('✅ Analyse terminée! Consultez l\'onglet Analyse.');
    } catch (error) {
      console.error('Erreur d\'analyse:', error);
      alert('❌ Erreur lors de l\'analyse');
    }
  };

  /**
   * Génère des suggestions CV basées sur les compétences utilisateur
   */
  const getCvSuggestions = async () => {
    if (!userSkills.trim()) {
      alert('Veuillez entrer vos compétences');
      return;
    }

    try {
      const skillsList = userSkills.split(',').map(s => s.trim()).filter(s => s);
      const response = await axios.post(`${API_URL}/api/cv/suggestions`, {
        skills: skillsList
      });
      setCvSuggestions(response.data);
    } catch (error) {
      console.error('Erreur suggestions CV:', error);
      alert('❌ Erreur lors de la génération des suggestions');
    }
  };

  /**
   * Lance un job de scraping
   */
  const startScraping = async (source, searchQuery, location = 'France', maxPages = 5) => {
    try {
      setScrapingLoading(true);
      const response = await axios.post(`${API_URL}/api/scraper/start`, {
        source,
        search_query: searchQuery,
        location,
        max_pages: maxPages
      });
      
      // TODO: Remplacer alert par une notification
      alert(`✅ Scraping ${source} démarré! ID: ${response.data.job_id}`);
      
      // Actualiser la liste des jobs de scraping
      fetchScrapingJobs();
    } catch (error) {
      console.error('Erreur de scraping:', error);
      alert('❌ Erreur lors du démarrage du scraping');
    } finally {
      setScrapingLoading(false);
    }
  };

  /**
   * Récupère la liste des jobs de scraping
   */
  const fetchScrapingJobs = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/scraper/jobs`);
      setScrapingJobs(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des jobs de scraping:', error);
    }
  };

  // Chargement initial des jobs de scraping
  useEffect(() => {
    if (activeTab === 'scraping') {
      fetchScrapingJobs();
    }
  }, [activeTab]);

  /**
   * Rendu du contenu principal selon l'onglet actif
   */
  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <Dashboard
            stats={stats}
            keywords={keywords}
            jobs={jobs}
            loading={loading}
            onPopulateTestData={populateTestData}
          />
        );

      case 'search':
        return (
          <Search
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            searchResults={searchResults}
            searchLoading={searchLoading}
            suggestions={suggestions}
            correctedQuery={correctedQuery}
            onSearch={searchJobs}
            onAnalyzeJob={analyzeJobKeywords}
          />
        );

      case 'jobs':
        return (
          <div className="text-center p-8">
            <div className="text-6xl mb-4">🚧</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Page en construction
            </h3>
            <p className="text-gray-600">
              La liste complète des offres sera bientôt disponible.
            </p>
          </div>
        );

      case 'analysis':
        return (
          <div className="text-center p-8">
            <div className="text-6xl mb-4">📈</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Analyse des Données
            </h3>
            <p className="text-gray-600">
              Les outils d'analyse seront bientôt disponibles.
            </p>
            {analysisResults && (
              <div className="mt-6 p-4 bg-green-50 rounded-lg">
                <p className="text-green-800">
                  Dernière analyse disponible pour visualisation.
                </p>
              </div>
            )}
          </div>
        );

      case 'scraping':
        return (
          <div className="text-center p-8">
            <div className="text-6xl mb-4">🕷️</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Gestion du Scraping
            </h3>
            <p className="text-gray-600">
              Les outils de scraping seront bientôt disponibles.
            </p>
          </div>
        );

      default:
        return (
          <div className="text-center p-8">
            <div className="text-6xl mb-4">❓</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Page non trouvée
            </h3>
            <p className="text-gray-600">
              Retournez au dashboard.
            </p>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header avec navigation */}
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Contenu principal */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderContent()}
      </main>

      {/* Footer (optionnel) */}
      <footer className="bg-white border-t border-gray-200 py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center text-gray-500 text-sm">
            <p>© 2024 Job Keywords Analyzer - Développé avec ❤️ pour analyser le marché de l'emploi tech</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;