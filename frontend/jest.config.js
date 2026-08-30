/** @type {import('jest').Config} */
const config = {
  testEnvironment: 'jsdom',
  modulePathIgnorePatterns: ['<rootDir>/.next/'],
};

module.exports = config;
