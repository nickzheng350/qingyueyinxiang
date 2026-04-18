const path = require('path');
const fs = require('fs-extra');

const PROJECT_ROOT = path.resolve(__dirname, '..');

module.exports = {
  version: require('../package.json').version,
  PROJECT_ROOT,
  paths: {
    root: PROJECT_ROOT,
    src: path.join(PROJECT_ROOT, 'src'),
    config: path.join(PROJECT_ROOT, 'config'),
    prompts: path.join(PROJECT_ROOT, 'prompts'),
    ui: path.join(PROJECT_ROOT, 'ui'),
    docs: path.join(PROJECT_ROOT, 'docs'),
    mainPy: path.join(PROJECT_ROOT, 'main.py')
  },
  
  getConfig: () => {
    const configPath = path.join(PROJECT_ROOT, '.env');
    if (fs.existsSync(configPath)) {
      require('dotenv').config({ path: configPath });
    }
    return process.env;
  }
};
