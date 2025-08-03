/**
 * Composant de formulaire d'inscription
 */
import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

const RegisterForm = ({ onSwitchToLogin }) => {
  const { register, isLoading, error, clearError } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
    terms_accepted: false
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Effacer les erreurs quand l'utilisateur commence à taper
    if (error) {
      clearError();
    }
  };

  const validateForm = () => {
    if (!formData.email || !formData.password || !formData.first_name || !formData.last_name) {
      return "Veuillez remplir tous les champs obligatoires";
    }
    
    if (formData.password !== formData.password_confirm) {
      return "Les mots de passe ne correspondent pas";
    }
    
    if (formData.password.length < 8) {
      return "Le mot de passe doit contenir au moins 8 caractères";
    }
    
    if (!formData.terms_accepted) {
      return "Vous devez accepter les conditions d'utilisation";
    }
    
    // Validation email simple
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      return "Veuillez entrer un email valide";
    }
    
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const validationError = validateForm();
    if (validationError) {
      clearError();
      // Ici on pourrait afficher l'erreur de validation
      return;
    }

    // Préparer les données pour l'API
    const registrationData = {
      email: formData.email,
      password: formData.password,
      first_name: formData.first_name,
      last_name: formData.last_name
    };

    const result = await register(registrationData);
    if (!result.success) {
      console.error('Erreur d\'inscription:', result.error);
    }
  };

  const getPasswordStrength = () => {
    const password = formData.password;
    if (!password) return '';
    
    let strength = 0;
    let feedback = [];
    
    if (password.length >= 8) strength++;
    else feedback.push('8+ caractères');
    
    if (/[A-Z]/.test(password)) strength++;
    else feedback.push('majuscule');
    
    if (/[a-z]/.test(password)) strength++;
    else feedback.push('minuscule');
    
    if (/\d/.test(password)) strength++;
    else feedback.push('chiffre');
    
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    else feedback.push('caractère spécial');
    
    const strengthLevels = ['Très faible', 'Faible', 'Moyen', 'Fort', 'Très fort'];
    const colors = ['text-red-500', 'text-orange-500', 'text-yellow-500', 'text-green-500', 'text-green-600'];
    
    return {
      level: strengthLevels[strength] || 'Très faible',
      color: colors[strength] || 'text-red-500',
      feedback: feedback.join(', ')
    };
  };

  const passwordStrength = getPasswordStrength();

  return (
    <div className="min-h-screen gradient-bg flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Éléments décoratifs animés */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-white/10 rounded-full blur-3xl animate-float"></div>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-white/5 rounded-full blur-3xl animate-float" style={{animationDelay: '3s'}}></div>
        <div className="absolute top-1/3 left-1/4 w-48 h-48 bg-white/5 rounded-full blur-3xl animate-pulse-slow"></div>
      </div>

      <div className="max-w-md w-full space-y-8 relative z-10">
        {/* En-tête moderne */}
        <div className="text-center animate-bounce-in">
          <div className="flex justify-center mb-6">
            <div className="relative">
              <div className="w-20 h-20 bg-gradient-to-r from-green-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-glow animate-pulse-slow">
                <span className="text-4xl">🚀</span>
              </div>
              <div className="absolute -top-1 -right-1 w-6 h-6 bg-yellow-400 rounded-full border-4 border-white animate-bounce"></div>
            </div>
          </div>
          <h1 className="text-4xl font-bold text-white mb-2 text-shadow">
            Rejoignez-nous !
          </h1>
          <p className="text-blue-100 text-lg font-medium">
            Créez votre compte Job Keywords Analyzer
          </p>
          <p className="text-blue-200/80 text-sm mt-1">
            Accédez aux analyses avancées du marché de l'emploi
          </p>
        </div>

        {/* Formulaire d'inscription moderne */}
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
                    Erreur d'inscription
                  </h3>
                  <p className="text-sm text-red-700">
                    {error}
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-4">
            {/* Nom et Prénom */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="first_name" className="block text-sm font-semibold text-gray-700 mb-2">
                  Prénom *
                </label>
                <input
                  id="first_name"
                  name="first_name"
                  type="text"
                  required
                  value={formData.first_name}
                  onChange={handleInputChange}
                  className="input-field py-3 text-base font-medium"
                  placeholder="Jean"
                />
              </div>
              <div>
                <label htmlFor="last_name" className="block text-sm font-semibold text-gray-700 mb-2">
                  Nom *
                </label>
                <input
                  id="last_name"
                  name="last_name"
                  type="text"
                  required
                  value={formData.last_name}
                  onChange={handleInputChange}
                  className="input-field py-3 text-base font-medium"
                  placeholder="Dupont"
                />
              </div>
            </div>

            {/* Email moderne */}
            <div className="group">
              <label htmlFor="email" className="block text-sm font-semibold text-gray-700 mb-2">
                Adresse email *
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <div className="w-5 h-5 text-gray-400 group-focus-within:text-blue-500 transition-colors">
                    📧
                  </div>
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={handleInputChange}
                  className="input-field pl-12 py-4 text-lg font-medium"
                  placeholder="jean.dupont@exemple.com"
                />
              </div>
            </div>

            {/* Mot de passe */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Mot de passe *
              </label>
              <div className="mt-1 relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={formData.password}
                  onChange={handleInputChange}
                  className="appearance-none relative block w-full px-3 py-2 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                  placeholder="Mot de passe sécurisé"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  <span className="text-gray-400">
                    {showPassword ? '👁️' : '🙈'}
                  </span>
                </button>
              </div>
              {formData.password && (
                <div className="mt-1 text-xs">
                  <span className={passwordStrength.color}>
                    Force: {passwordStrength.level}
                  </span>
                  {passwordStrength.feedback && (
                    <span className="text-gray-500 ml-2">
                      ({passwordStrength.feedback})
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Confirmation mot de passe */}
            <div>
              <label htmlFor="password_confirm" className="block text-sm font-medium text-gray-700">
                Confirmer le mot de passe *
              </label>
              <div className="mt-1 relative">
                <input
                  id="password_confirm"
                  name="password_confirm"
                  type={showPasswordConfirm ? "text" : "password"}
                  required
                  value={formData.password_confirm}
                  onChange={handleInputChange}
                  className={`appearance-none relative block w-full px-3 py-2 pr-10 border placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm ${
                    formData.password_confirm && formData.password !== formData.password_confirm
                      ? 'border-red-300 bg-red-50'
                      : 'border-gray-300'
                  }`}
                  placeholder="Confirmer le mot de passe"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPasswordConfirm(!showPasswordConfirm)}
                >
                  <span className="text-gray-400">
                    {showPasswordConfirm ? '👁️' : '🙈'}
                  </span>
                </button>
              </div>
              {formData.password_confirm && formData.password !== formData.password_confirm && (
                <p className="mt-1 text-xs text-red-600">
                  Les mots de passe ne correspondent pas
                </p>
              )}
            </div>
          </div>

          {/* Conditions d'utilisation */}
          <div className="flex items-center">
            <input
              id="terms_accepted"
              name="terms_accepted"
              type="checkbox"
              required
              checked={formData.terms_accepted}
              onChange={handleInputChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="terms_accepted" className="ml-2 block text-sm text-gray-900">
              J'accepte les{' '}
              <a href="#" className="text-blue-600 hover:text-blue-500">
                conditions d'utilisation
              </a>{' '}
              et la{' '}
              <a href="#" className="text-blue-600 hover:text-blue-500">
                politique de confidentialité
              </a>
            </label>
          </div>

          {/* Bouton d'inscription moderne */}
          <div>
            <button
              type="submit"
              disabled={isLoading || validateForm() !== null}
              className="btn-primary w-full py-4 text-lg font-semibold rounded-xl shadow-lg hover:shadow-xl hover:scale-[1.02] transform transition-all duration-200 relative overflow-hidden group bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700"
            >
              {/* Effet de brillance au hover */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -skew-x-12 group-hover:animate-[shimmer_1.5s_ease-out] opacity-0 group-hover:opacity-100"></div>
              
              {isLoading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-3"></div>
                  <span>Création en cours...</span>
                </div>
              ) : (
                <div className="flex items-center justify-center">
                  <span className="mr-3 text-xl">✨</span>
                  <span>Créer mon compte</span>
                </div>
              )}
            </button>
          </div>

          {/* Lien vers connexion */}
          <div className="text-center">
            <p className="text-sm text-gray-600">
              Déjà un compte ?{' '}
              <button
                type="button"
                onClick={onSwitchToLogin}
                className="font-semibold text-blue-600 hover:text-blue-500 transition-colors duration-200 underline"
              >
                Se connecter
              </button>
            </p>
          </div>
        </form>
        </div>

        {/* Footer moderne */}
        <div className="text-center mt-8">
          <p className="text-xs text-white/80">
            En créant un compte, vous acceptez nos{' '}
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

export default RegisterForm;