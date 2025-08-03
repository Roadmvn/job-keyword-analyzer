/**
 * Composant de formulaire de connexion
 */
import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

const LoginForm = ({ onSwitchToRegister }) => {
  const { login, isLoading, error, clearError } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Effacer les erreurs quand l'utilisateur commence à taper
    if (error) {
      clearError();
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.username || !formData.password) {
      return;
    }

    const result = await login(formData);
    if (!result.success) {
      console.error('Erreur de connexion:', result.error);
    }
  };

  return (
    <div className="min-h-screen gradient-bg flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Éléments décoratifs animés */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-white/10 rounded-full blur-3xl animate-float"></div>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-white/5 rounded-full blur-3xl animate-float" style={{animationDelay: '2s'}}></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-white/5 rounded-full blur-3xl animate-pulse-slow"></div>
      </div>

      <div className="max-w-md w-full space-y-8 relative z-10">
        {/* En-tête moderne */}
        <div className="text-center animate-bounce-in">
          <div className="flex justify-center mb-6">
            <div className="relative">
              <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-glow animate-pulse-slow">
                <span className="text-4xl">🚀</span>
              </div>
              <div className="absolute -top-1 -right-1 w-6 h-6 bg-green-400 rounded-full border-4 border-white animate-pulse"></div>
            </div>
          </div>
          <h1 className="text-4xl font-bold text-white mb-2 text-shadow">
            Job Keywords Analyzer
          </h1>
          <p className="text-blue-100 text-lg font-medium">
            Découvrez les tendances du marché de l'emploi
          </p>
          <p className="text-blue-200/80 text-sm mt-1">
            Connectez-vous pour accéder au dashboard
          </p>
        </div>

        {/* Formulaire de connexion moderne */}
        <div className="auth-card animate-slide-up">
          <form className="space-y-6" onSubmit={handleSubmit}>
          {/* Messages d'erreur modernes */}
          {error && (
            <div className="bg-red-50/90 backdrop-blur-sm border border-red-200 rounded-xl p-4 animate-slide-up">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                    <span className="text-red-500 text-sm">⚠️</span>
                  </div>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-semibold text-red-800 mb-1">
                    Erreur de connexion
                  </h3>
                  <p className="text-sm text-red-700">
                    {error}
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-4">
            {/* Email/Username moderne */}
            <div className="group">
              <label htmlFor="username" className="block text-sm font-semibold text-gray-700 mb-2">
                Email ou nom d'utilisateur
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <div className="w-5 h-5 text-gray-400 group-focus-within:text-blue-500 transition-colors">
                    👤
                  </div>
                </div>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  value={formData.username}
                  onChange={handleInputChange}
                  className="input-field pl-12 py-4 text-lg font-medium placeholder-gray-400 focus:placeholder-gray-300 transition-all duration-200"
                  placeholder="votre-email@exemple.com"
                />
              </div>
            </div>

            {/* Mot de passe moderne */}
            <div className="group">
              <label htmlFor="password" className="block text-sm font-semibold text-gray-700 mb-2">
                Mot de passe
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <div className="w-5 h-5 text-gray-400 group-focus-within:text-blue-500 transition-colors">
                    🔒
                  </div>
                </div>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={formData.password}
                  onChange={handleInputChange}
                  className="input-field pl-12 pr-12 py-4 text-lg font-medium placeholder-gray-400 focus:placeholder-gray-300 transition-all duration-200"
                  placeholder="Votre mot de passe"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-4 flex items-center hover:scale-110 transition-transform duration-200"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  <span className="text-gray-400 hover:text-gray-600 text-lg">
                    {showPassword ? '👁️' : '🙈'}
                  </span>
                </button>
              </div>
            </div>
          </div>

          {/* Options de connexion */}
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                id="remember-me"
                name="remember-me"
                type="checkbox"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
                Se souvenir de moi
              </label>
            </div>

            <div className="text-sm">
              <a href="#" className="font-medium text-blue-600 hover:text-blue-500">
                Mot de passe oublié ?
              </a>
            </div>
          </div>

          {/* Bouton de connexion moderne */}
          <div>
            <button
              type="submit"
              disabled={isLoading || !formData.username || !formData.password}
              className="btn-primary w-full py-4 text-lg font-semibold rounded-xl shadow-lg hover:shadow-xl hover:scale-[1.02] transform transition-all duration-200 relative overflow-hidden group"
            >
              {/* Effet de brillance au hover */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -skew-x-12 group-hover:animate-[shimmer_1.5s_ease-out] opacity-0 group-hover:opacity-100"></div>
              
              {isLoading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-3"></div>
                  <span>Connexion en cours...</span>
                </div>
              ) : (
                <div className="flex items-center justify-center">
                  <span className="mr-3 text-xl">🚀</span>
                  <span>Se connecter</span>
                </div>
              )}
            </button>
          </div>

          {/* Lien vers inscription */}
          <div className="text-center">
            <p className="text-sm text-gray-600">
              Pas encore de compte ?{' '}
              <button
                type="button"
                onClick={onSwitchToRegister}
                className="font-medium text-blue-600 hover:text-blue-500 transition-colors duration-200"
              >
                Créer un compte
              </button>
            </p>
          </div>
          </form>

          {/* OAuth moderne */}
          <div className="mt-8">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-white text-gray-500 font-medium">Ou connectez-vous avec</span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-4">
              <button className="btn-secondary py-3 text-sm font-semibold rounded-xl hover:scale-[1.02] transform transition-all duration-200">
                <span className="mr-2 text-lg">🇬</span>
                Google
              </button>
              <button className="btn-secondary py-3 text-sm font-semibold rounded-xl hover:scale-[1.02] transform transition-all duration-200">
                <span className="mr-2 text-lg">💼</span>
                LinkedIn
              </button>
            </div>
          </div>
        </div>

        {/* Footer moderne */}
        <div className="text-center mt-8">
          <p className="text-xs text-white/80">
            En vous connectant, vous acceptez nos{' '}
            <a href="#" className="text-blue-200 hover:text-white underline">
              conditions d'utilisation
            </a>{' '}
            et notre{' '}
            <a href="#" className="text-blue-200 hover:text-white underline">
              politique de confidentialité
            </a>
          </p>
        </div>
      </div>
    </div>


  );
};

export default LoginForm;