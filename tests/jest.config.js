/**
 * Jest Configuration for Frontend Tests
 * @see https://jestjs.io/docs/configuration
 */

module.exports = {
  // Test environment
  testEnvironment: 'jsdom',
  
  // Test file patterns
  testMatch: [
    '**/frontend/**/*.spec.js',
    '**/frontend/**/*.test.js'
  ],
  
  // Coverage collection
  collectCoverageFrom: [
    '../agent_ui/static/js/**/*.js',
    '!../agent_ui/static/js/vendor/**'
  ],
  
  // Coverage thresholds
  coverageThreshold: {
    global: {
      branches: 60,
      functions: 60,
      lines: 70,
      statements: 70
    }
  },
  
  // Module paths
  moduleDirectories: ['node_modules', '../agent_ui/static/js'],
  
  // Setup files
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  
  // Transform files
  transform: {
    '^.+\\.js$': 'babel-jest'
  },
  
  // Ignore patterns
  testPathIgnorePatterns: [
    '/node_modules/',
    '/e2e/'
  ],
  
  // Verbose output
  verbose: true
};
