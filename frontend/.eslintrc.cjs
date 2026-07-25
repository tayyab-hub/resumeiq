/* eslint-env node */
module.exports = {
  root: true,
  env: { browser: true, es2022: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
    'plugin:jsx-a11y/recommended',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  plugins: ['@typescript-eslint', 'react-refresh', 'jsx-a11y'],
  ignorePatterns: ['dist', 'node_modules', '*.cjs'],
  rules: {
    'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/no-explicit-any': 'error',

    // XSS defence as a build failure rather than a code-review convention.
    // Resume and job-description text is rendered as text, never as HTML.
    // This is a syntax rule rather than react/no-danger, so it needs no extra
    // plugin and carries a message that explains the reason.
    'no-restricted-syntax': [
      'error',
      {
        selector: 'JSXAttribute[name.name="dangerouslySetInnerHTML"]',
        message:
          'dangerouslySetInnerHTML is banned. User-supplied resume and job text must be rendered as text.',
      },
    ],

    // Tokens must never reach web storage: anything there is readable by an
    // injected script. See src/services/tokenStore.ts.
    'no-restricted-properties': [
      'error',
      {
        object: 'localStorage',
        property: 'setItem',
        message: 'Do not store tokens or personal data in localStorage.',
      },
      {
        object: 'sessionStorage',
        property: 'setItem',
        message: 'Do not store tokens or personal data in sessionStorage.',
      },
    ],

    'no-console': ['error', { allow: ['warn', 'error'] }],
  },
  overrides: [
    {
      files: ['tests/**/*.{ts,tsx}'],
      env: { node: true },
      rules: { '@typescript-eslint/no-non-null-assertion': 'off' },
    },
  ],
};
