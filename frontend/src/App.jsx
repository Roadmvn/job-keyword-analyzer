import React, { useState, useEffect } from 'react'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

function App() {
  const [stats, setStats] = useState(null)
  const [jobs, setJobs] = useState([])
  const [keywords, setKeywords] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('dashboard')
  
  // États pour la recherche
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const [correctedQuery, setCorrectedQuery] = useState('')
  
  // États pour l'analyse
  const [analysisResults, setAnalysisResults] = useState(null)
  const [userSkills, setUserSkills] = useState('')
  const [cvSuggestions, setCvSuggestions] = useState(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [statsRes, jobsRes, keywordsRes] = await Promise.all([
        axios.get(`${API_URL}/api/stats`),
        axios.get(`${API_URL}/api/jobs?limit=5`),
        axios.get(`${API_URL}/api/keywords?limit=10`)
      ])
      
      setStats(statsRes.data)
      setJobs(jobsRes.data)
      setKeywords(keywordsRes.data)
    } catch (error) {
      console.error('Erreur lors du chargement:', error)
    } finally {
      setLoading(false)
    }
  }

  const populateTestData = async () => {
    try {
      await axios.post(`${API_URL}/api/test/populate`)
      alert('✅ Données de test ajoutées!')
      fetchData()
    } catch (error) {
      alert('❌ Erreur lors de l\'ajout des données de test')
    }
  }

  // Fonctions de recherche
  const searchJobs = async (query = searchQuery) => {
    if (!query.trim()) {
      setSearchResults([])
      return
    }

    try {
      setSearchLoading(true)
      const response = await axios.get(`${API_URL}/api/search`, {
        params: { q: query, limit: 20 }
      })
      
      setSearchResults(response.data.results || [])
      setCorrectedQuery(response.data.corrected_query)
      setSuggestions(response.data.suggestions || [])
      
      if (response.data.corrected_query !== query) {
        console.log(`🔧 Requête corrigée: "${query}" → "${response.data.corrected_query}"`)
      }
    } catch (error) {
      console.error('Erreur de recherche:', error)
      setSearchResults([])
    } finally {
      setSearchLoading(false)
    }
  }

  const analyzeJobKeywords = async (jobId) => {
    try {
      const response = await axios.post(`${API_URL}/api/analyze/job/${jobId}`)
      setAnalysisResults(response.data)
      alert('✅ Analyse terminée! Consultez l\'onglet Analyse.')
    } catch (error) {
      console.error('Erreur d\'analyse:', error)
      alert('❌ Erreur lors de l\'analyse')
    }
  }

  const getCvSuggestions = async () => {
    if (!userSkills.trim()) {
      alert('Veuillez entrer vos compétences')
      return
    }

    try {
      const skillsList = userSkills.split(',').map(s => s.trim()).filter(s => s)
      const response = await axios.post(`${API_URL}/api/cv/suggestions`, {
        skills: skillsList
      })
      setCvSuggestions(response.data)
    } catch (error) {
      console.error('Erreur suggestions CV:', error)
      alert('❌ Erreur lors de la génération des suggestions')
    }
  }

  const handleSearchKeyPress = (e) => {
    if (e.key === 'Enter') {
      searchJobs()
    }
  }

  const styles = {
    container: {
      minHeight: '100vh',
      padding: '20px',
    },
    header: {
      textAlign: 'center',
      color: 'white',
      marginBottom: '30px'
    },
    card: {
      background: 'white',
      borderRadius: '12px',
      padding: '20px',
      margin: '10px',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
    },
    nav: {
      display: 'flex',
      justifyContent: 'center',
      gap: '10px',
      marginBottom: '20px'
    },
    button: {
      padding: '10px 20px',
      border: 'none',
      borderRadius: '6px',
      cursor: 'pointer',
      backgroundColor: '#4f46e5',
      color: 'white',
      fontSize: '14px'
    },
    activeButton: {
      backgroundColor: '#1e40af'
    },
    grid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
      gap: '20px',
      maxWidth: '1200px',
      margin: '0 auto'
    },
    statCard: {
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: 'white',
      textAlign: 'center'
    },
    list: {
      listStyle: 'none',
      padding: 0
    },
    listItem: {
      padding: '8px 0',
      borderBottom: '1px solid #e5e7eb'
    }
  }

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <h1>🚀 Job Keywords Analyzer</h1>
          <p>Chargement...</p>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1>🚀 Job Keywords Analyzer</h1>
        <p>Analysez les mots-clés des offres d'emploi tech</p>
      </div>

      <div style={styles.nav}>
        <button 
          style={{...styles.button, ...(activeTab === 'dashboard' ? styles.activeButton : {})}}
          onClick={() => setActiveTab('dashboard')}
        >
          📊 Dashboard
        </button>
        <button 
          style={{...styles.button, ...(activeTab === 'search' ? styles.activeButton : {})}}
          onClick={() => setActiveTab('search')}
        >
          🔍 Recherche
        </button>
        <button 
          style={{...styles.button, ...(activeTab === 'analysis' ? styles.activeButton : {})}}
          onClick={() => setActiveTab('analysis')}
        >
          🧠 Analyse NLP
        </button>
        <button 
          style={{...styles.button, ...(activeTab === 'cv' ? styles.activeButton : {})}}
          onClick={() => setActiveTab('cv')}
        >
          📄 Améliorer CV
        </button>
        <button 
          style={{...styles.button, ...(activeTab === 'jobs' ? styles.activeButton : {})}}
          onClick={() => setActiveTab('jobs')}
        >
          💼 Offres
        </button>
        <button 
          style={{...styles.button, ...(activeTab === 'keywords' ? styles.activeButton : {})}}
          onClick={() => setActiveTab('keywords')}
        >
          🏷️ Mots-clés
        </button>
        <button 
          style={styles.button}
          onClick={populateTestData}
        >
          🧪 Ajouter données test
        </button>
      </div>

      <div style={styles.grid}>
        {activeTab === 'dashboard' && (
          <>
            <div style={{...styles.card, ...styles.statCard}}>
              <h3>📊 Statistiques</h3>
              <p><strong>{stats?.total_jobs || 0}</strong> Offres d'emploi</p>
              <p><strong>{stats?.total_keywords || 0}</strong> Mots-clés</p>
              <p><strong>{stats?.total_companies || 0}</strong> Entreprises</p>
            </div>

            <div style={styles.card}>
              <h3>🏢 Top Entreprises</h3>
              <ul style={styles.list}>
                {stats?.top_companies?.map((company, index) => (
                  <li key={index} style={styles.listItem}>
                    <strong>{company.name}</strong> - {company.count} offres
                  </li>
                )) || <li>Aucune donnée</li>}
              </ul>
            </div>

            <div style={styles.card}>
              <h3>🏷️ Top Mots-clés</h3>
              <ul style={styles.list}>
                {stats?.top_keywords?.map((keyword, index) => (
                  <li key={index} style={styles.listItem}>
                    <strong>{keyword.keyword}</strong> - {keyword.frequency}x
                    <span style={{
                      marginLeft: '10px',
                      fontSize: '12px',
                      padding: '2px 6px',
                      backgroundColor: '#e5e7eb',
                      borderRadius: '4px'
                    }}>
                      {keyword.category}
                    </span>
                  </li>
                )) || <li>Aucune donnée</li>}
              </ul>
            </div>
          </>
        )}

        {activeTab === 'search' && (
          <>
            <div style={{...styles.card, gridColumn: '1 / -1'}}>
              <h3>🔍 Recherche Intelligente d'Offres</h3>
              <div style={{display: 'flex', gap: '10px', marginBottom: '20px'}}>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={handleSearchKeyPress}
                  placeholder="Rechercher des offres d'emploi (ex: python, react, développeur...)"
                  style={{
                    flex: 1,
                    padding: '12px',
                    border: '2px solid #e5e7eb',
                    borderRadius: '6px',
                    fontSize: '16px'
                  }}
                />
                <button 
                  onClick={() => searchJobs()}
                  disabled={searchLoading}
                  style={{...styles.button, padding: '12px 24px'}}
                >
                  {searchLoading ? '🔄' : '🔍'} Rechercher
                </button>
              </div>
              
              {correctedQuery && correctedQuery !== searchQuery && (
                <div style={{
                  background: '#fef3c7',
                  border: '1px solid #f59e0b',
                  borderRadius: '6px',
                  padding: '10px',
                  marginBottom: '15px'
                }}>
                  🔧 Votre recherche a été corrigée : 
                  <strong> "{searchQuery}" → "{correctedQuery}"</strong>
                </div>
              )}

              {suggestions.length > 0 && (
                <div style={{marginBottom: '15px'}}>
                  <p><strong>💡 Suggestions :</strong></p>
                  <div style={{display: 'flex', gap: '5px', flexWrap: 'wrap'}}>
                    {suggestions.map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => {
                          setSearchQuery(suggestion)
                          searchJobs(suggestion)
                        }}
                        style={{
                          padding: '5px 10px',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          background: '#f9fafb',
                          cursor: 'pointer'
                        }}
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {searchResults.length > 0 ? (
                <div>
                  <h4>📋 Résultats ({searchResults.length})</h4>
                  {searchResults.map((job) => (
                    <div key={job.job_id} style={{
                      ...styles.listItem,
                      padding: '15px',
                      border: '1px solid #e5e7eb',
                      borderRadius: '6px',
                      margin: '10px 0'
                    }}>
                      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'start'}}>
                        <div style={{flex: 1}}>
                          <h4 style={{margin: '0 0 5px 0', color: '#4f46e5'}}>
                            {job.title}
                          </h4>
                          <p style={{margin: '0 0 5px 0'}}>
                            <strong>{job.company}</strong> - {job.location}
                          </p>
                          <p style={{margin: '0 0 10px 0', color: '#6b7280', fontSize: '14px'}}>
                            {job.description}
                          </p>
                          {job.keywords && job.keywords.length > 0 && (
                            <div style={{display: 'flex', gap: '5px', flexWrap: 'wrap', marginTop: '10px'}}>
                              {job.keywords.slice(0, 5).map((keyword, idx) => (
                                <span key={idx} style={{
                                  background: '#ddd6fe',
                                  color: '#5b21b6',
                                  padding: '2px 8px',
                                  borderRadius: '12px',
                                  fontSize: '12px'
                                }}>
                                  {keyword}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                        <button
                          onClick={() => analyzeJobKeywords(job.job_id)}
                          style={{
                            ...styles.button,
                            padding: '8px 16px',
                            fontSize: '12px',
                            marginLeft: '10px'
                          }}
                        >
                          🧠 Analyser
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : searchQuery && !searchLoading ? (
                <p>❌ Aucun résultat trouvé pour "{searchQuery}"</p>
              ) : null}
            </div>
          </>
        )}

        {activeTab === 'analysis' && (
          <div style={{...styles.card, gridColumn: '1 / -1'}}>
            <h3>🧠 Analyse NLP des Offres</h3>
            {analysisResults ? (
              <div>
                <h4>✅ Analyse de l'offre #{analysisResults.job_id}</h4>
                <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px'}}>
                  <div>
                    <h5>🏷️ Mots-clés extraits ({analysisResults.analysis.total_tech_skills})</h5>
                    <div style={{maxHeight: '300px', overflowY: 'auto'}}>
                      {analysisResults.analysis.keywords.map((kw, index) => (
                        <div key={index} style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          padding: '8px',
                          border: '1px solid #e5e7eb',
                          borderRadius: '4px',
                          margin: '5px 0'
                        }}>
                          <span><strong>{kw.keyword}</strong></span>
                          <span style={{fontSize: '12px', color: '#6b7280'}}>
                            {kw.category} - {(kw.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h5>📊 Résumé par catégorie</h5>
                    {Object.entries(analysisResults.analysis.categories_summary).map(([category, keywords]) => (
                      <div key={category} style={{marginBottom: '15px'}}>
                        <h6 style={{margin: '5px 0', color: '#4f46e5'}}>{category}</h6>
                        <div style={{display: 'flex', gap: '5px', flexWrap: 'wrap'}}>
                          {keywords.map((keyword, idx) => (
                            <span key={idx} style={{
                              background: '#f3f4f6',
                              padding: '3px 8px',
                              borderRadius: '12px',
                              fontSize: '12px'
                            }}>
                              {keyword}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div style={{marginTop: '20px', padding: '15px', background: '#f9fafb', borderRadius: '6px'}}>
                  <h5>📋 Informations détectées</h5>
                  <p><strong>Niveau de séniorité :</strong> {analysisResults.analysis.seniority_level}</p>
                  <p><strong>Expérience requise :</strong> {analysisResults.analysis.experience_required || 'Non spécifiée'}</p>
                  <p><strong>Catégorie principale :</strong> {analysisResults.analysis.top_category || 'N/A'}</p>
                </div>
              </div>
            ) : (
              <div style={{textAlign: 'center', padding: '40px'}}>
                <p>🔍 Allez dans l'onglet "Recherche" et cliquez sur "🧠 Analyser" sur une offre pour voir l'analyse NLP complète.</p>
                <p style={{color: '#6b7280', fontSize: '14px'}}>
                  L'analyse extrait automatiquement les mots-clés techniques, détecte le niveau de séniorité, 
                  et identifie les compétences requises.
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'cv' && (
          <div style={{...styles.card, gridColumn: '1 / -1'}}>
            <h3>📄 Améliorer votre CV</h3>
            <div style={{marginBottom: '20px'}}>
              <label style={{display: 'block', marginBottom: '10px', fontWeight: 'bold'}}>
                🎯 Entrez vos compétences actuelles (séparées par des virgules) :
              </label>
              <textarea
                value={userSkills}
                onChange={(e) => setUserSkills(e.target.value)}
                placeholder="Ex: Python, React, Docker, SQL, Machine Learning..."
                style={{
                  width: '100%',
                  height: '100px',
                  padding: '12px',
                  border: '2px solid #e5e7eb',
                  borderRadius: '6px',
                  resize: 'vertical'
                }}
              />
              <button
                onClick={getCvSuggestions}
                style={{...styles.button, marginTop: '10px'}}
              >
                🚀 Générer suggestions
              </button>
            </div>

            {cvSuggestions && (
              <div>
                <div style={{
                  background: '#f0f9ff',
                  border: '2px solid #0ea5e9',
                  borderRadius: '8px',
                  padding: '20px',
                  marginBottom: '20px'
                }}>
                  <h4 style={{margin: '0 0 10px 0', color: '#0c4a6e'}}>
                    📊 Votre couverture du marché : {cvSuggestions.market_analysis.user_coverage}%
                  </h4>
                  <p style={{margin: 0, color: '#075985'}}>
                    Vous maîtrisez {cvSuggestions.user_skills.length} compétences sur {cvSuggestions.market_analysis.total_market_keywords} populaires sur le marché.
                  </p>
                </div>

                <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px'}}>
                  <div>
                    <h4 style={{color: '#dc2626'}}>❌ Compétences manquantes importantes</h4>
                    {cvSuggestions.suggestions.missing_skills.length > 0 ? (
                      cvSuggestions.suggestions.missing_skills.map((skill, index) => (
                        <div key={index} style={{
                          padding: '10px',
                          border: `2px solid ${skill.priority === 'HIGH' ? '#dc2626' : '#f59e0b'}`,
                          borderRadius: '6px',
                          margin: '5px 0',
                          background: skill.priority === 'HIGH' ? '#fef2f2' : '#fffbeb'
                        }}>
                          <strong>{skill.skill}</strong>
                          <span style={{
                            float: 'right',
                            background: skill.priority === 'HIGH' ? '#dc2626' : '#f59e0b',
                            color: 'white',
                            padding: '2px 8px',
                            borderRadius: '12px',
                            fontSize: '12px'
                          }}>
                            {skill.priority}
                          </span>
                          <br />
                          <small>{skill.category} - Demandé {skill.market_demand} fois</small>
                        </div>
                      ))
                    ) : (
                      <p>✅ Excellente couverture du marché !</p>
                    )}
                  </div>

                  <div>
                    <h4 style={{color: '#059669'}}>📈 Compétences à approfondir</h4>
                    {cvSuggestions.suggestions.skills_to_improve.length > 0 ? (
                      cvSuggestions.suggestions.skills_to_improve.map((skill, index) => (
                        <div key={index} style={{
                          padding: '10px',
                          border: '2px solid #059669',
                          borderRadius: '6px',
                          margin: '5px 0',
                          background: '#f0fdf4'
                        }}>
                          <strong>{skill.skill}</strong>
                          <span style={{float: 'right', color: '#059669', fontSize: '12px'}}>
                            {skill.market_frequency} offres
                          </span>
                          <br />
                          <small>{skill.suggestion}</small>
                        </div>
                      ))
                    ) : (
                      <p>👍 Vos compétences sont bien positionnées !</p>
                    )}
                  </div>
                </div>

                <div style={{
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '6px',
                  padding: '15px',
                  marginTop: '20px'
                }}>
                  <h4>💡 Recommandations personnalisées</h4>
                  {cvSuggestions.suggestions.recommendations.length > 0 ? (
                    <ul>
                      {cvSuggestions.suggestions.recommendations.map((rec, index) => (
                        <li key={index} style={{marginBottom: '8px'}}>{rec}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>🎉 Votre profil est très complet pour le marché actuel !</p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'jobs' && (
          <div style={{...styles.card, gridColumn: '1 / -1'}}>
            <h3>💼 Dernières Offres d'Emploi</h3>
            {jobs.length > 0 ? (
              <div>
                {jobs.map((job) => (
                  <div key={job.id} style={{...styles.listItem, padding: '15px 0'}}>
                    <h4 style={{margin: '0 0 5px 0', color: '#4f46e5'}}>{job.title}</h4>
                    <p style={{margin: '0 0 5px 0'}}><strong>{job.company}</strong> - {job.location}</p>
                    <p style={{margin: 0, color: '#6b7280', fontSize: '14px'}}>
                      {job.description.substring(0, 200)}...
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p>Aucune offre d'emploi. Cliquez sur "Ajouter données test" pour commencer.</p>
            )}
          </div>
        )}

        {activeTab === 'keywords' && (
          <div style={{...styles.card, gridColumn: '1 / -1'}}>
            <h3>🏷️ Tous les Mots-clés</h3>
            {keywords.length > 0 ? (
              <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '10px'}}>
                {keywords.map((keyword) => (
                  <div key={keyword.id} style={{
                    padding: '10px',
                    backgroundColor: '#f3f4f6',
                    borderRadius: '6px',
                    textAlign: 'center'
                  }}>
                    <strong>{keyword.keyword}</strong>
                    <br />
                    <small>{keyword.category} - {keyword.frequency}x</small>
                  </div>
                ))}
              </div>
            ) : (
              <p>Aucun mot-clé. Cliquez sur "Ajouter données test" pour commencer.</p>
            )}
          </div>
        )}
      </div>

      <div style={{textAlign: 'center', marginTop: '40px', color: 'white'}}>
        <p>🔗 API: <a href="http://localhost:8000/docs" target="_blank" style={{color: 'white'}}>
          http://localhost:8000/docs
        </a></p>
      </div>
    </div>
  )
}

export default App 