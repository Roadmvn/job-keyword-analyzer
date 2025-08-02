module.exports = {
  // ===================================
  // CONFIGURATION GÉNÉRALE
  // ===================================
  printWidth: 80,
  tabWidth: 2,
  useTabs: false,
  semi: true,
  singleQuote: true,
  quoteProps: 'as-needed',
  
  // ===================================
  // JSX
  // ===================================
  jsxSingleQuote: true,
  jsxBracketSameLine: false,
  
  // ===================================
  // ARRAYS & OBJECTS
  // ===================================
  trailingComma: 'es5',
  bracketSpacing: true,
  bracketSameLine: false,
  
  // ===================================
  // FONCTIONS
  // ===================================
  arrowParens: 'avoid',
  
  // ===================================
  // FORMATAGE
  // ===================================
  endOfLine: 'lf',
  embeddedLanguageFormatting: 'auto',
  singleAttributePerLine: false,
  
  // ===================================
  // OVERRIDES PAR TYPE DE FICHIER
  // ===================================
  overrides: [
    {
      files: '*.json',
      options: {
        printWidth: 120,
        tabWidth: 2
      }
    },
    {
      files: '*.md',
      options: {
        printWidth: 100,
        proseWrap: 'always'
      }
    },
    {
      files: '*.{css,scss,less}',
      options: {
        singleQuote: false,
        tabWidth: 2
      }
    },
    {
      files: '*.{yaml,yml}',
      options: {
        tabWidth: 2,
        singleQuote: false
      }
    }
  ]
};