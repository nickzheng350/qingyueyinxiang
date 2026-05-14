#!/usr/bin/env node

const { program } = require('commander');
const chalk = require('chalk');
const path = require('path');
const fs = require('fs-extra');
const { spawn } = require('cross-spawn');
const which = require('which');
const ora = require('ora');

const packageJson = require('../package.json');

const PROJECT_ROOT = path.resolve(__dirname, '..');

program
  .name('清悦印象')
  .description('清悦印象 AI - 九头蛇生成式工作流平台')
  .version(packageJson.version);

program
  .command('install')
  .description('一键安装所有依赖并配置项目')
  .action(async () => {
    console.log(chalk.cyan.bold('\n🚀 清悦印象 AI 一键安装\n'));
    
    try {
      await fullInstall();
      console.log(chalk.green.bold('\n✨ 安装完成！\n'));
      console.log(chalk.blue('快速开始:'));
      console.log(chalk.gray('  1. 检查环境: 清悦印象 check'));
      console.log(chalk.gray('  2. 启动 API: 清悦印象 api'));
      console.log(chalk.gray('  3. 启动 UI: 清悦印象 ui'));
      console.log();
    } catch (error) {
      console.error(chalk.red('\n✗ 安装失败:'), error.message);
      process.exit(1);
    }
  });

program
  .command('check')
  .description('检查环境和依赖')
  .action(async () => {
    console.log(chalk.cyan.bold('\n🔍 环境检查\n'));
    try {
      await checkEnvironment();
      console.log(chalk.green('\n✓ 环境检查通过！\n'));
    } catch (error) {
      console.error(chalk.red('\n✗ 环境检查失败:'), error.message);
      process.exit(1);
    }
  });

program
  .command('api')
  .description('启动 API 服务')
  .option('--port <port>', 'API 服务端口', '8000')
  .option('--host <host>', '绑定主机地址', '0.0.0.0')
  .option('--reload', '启用热重载')
  .action(async (options) => {
    console.log(chalk.cyan.bold('\n🚀 清悦印象 AI API 服务启动中...\n'));
    
    try {
      await ensureEnvironment();
      await startApiService(options);
    } catch (error) {
      console.error(chalk.red('\n✗ 启动失败:'), error.message);
      process.exit(1);
    }
  });

program
  .command('ui')
  .description('启动 UI 服务')
  .option('--port <port>', 'UI 服务端口', '3000')
  .option('--host <host>', '绑定主机地址', '0.0.0.0')
  .option('--api-url <url>', 'API 服务地址', 'http://localhost:8000')
  .action(async (options) => {
    console.log(chalk.cyan.bold('\n🚀 清悦印象 AI UI 服务启动中...\n'));
    
    try {
      await startUiService(options);
    } catch (error) {
      console.error(chalk.red('\n✗ 启动失败:'), error.message);
      process.exit(1);
    }
  });

program
  .command('dev')
  .description('开发模式启动（API + UI 热重载）')
  .option('--api-port <port>', 'API 服务端口', '8000')
  .option('--ui-port <port>', 'UI 服务端口', '3000')
  .action(async (options) => {
    console.log(chalk.cyan.bold('\n🔧 清悦印象 AI 开发模式启动中...\n'));
    
    try {
      await ensureEnvironment();
      console.log(chalk.yellow('⚠ 注意: 同时启动 API 和 UI 服务需要两个终端'));
      console.log(chalk.blue('\n建议:'));
      console.log(chalk.gray('  终端 1: 清悦印象 api --reload'));
      console.log(chalk.gray('  终端 2: 清悦印象 ui'));
      console.log();
      
      const inquirer = require('inquirer');
      const answer = await inquirer.prompt([{
        type: 'list',
        name: 'choice',
        message: '选择启动方式:',
        choices: [
          { name: '仅启动 API 服务', value: 'api' },
          { name: '仅启动 UI 服务', value: 'ui' },
          { name: '取消', value: 'cancel' }
        ]
      }]);
      
      if (answer.choice === 'api') {
        await startApiService({ ...options, reload: true });
      } else if (answer.choice === 'ui') {
        await startUiService(options);
      }
    } catch (error) {
      console.error(chalk.red('\n✗ 启动失败:'), error.message);
      process.exit(1);
    }
  });

program
  .command('install-python')
  .description('安装 Python 依赖')
  .action(async () => {
    console.log(chalk.cyan.bold('\n🐍 安装 Python 依赖...\n'));
    
    try {
      await installPythonDependencies();
      console.log(chalk.green('\n✓ Python 依赖安装完成！\n'));
    } catch (error) {
      console.error(chalk.red('\n✗ 安装失败:'), error.message);
      process.exit(1);
    }
  });

program
  .command('install-deps')
  .description('安装所有依赖（Node.js + Python）')
  .action(async () => {
    console.log(chalk.cyan.bold('\n📦 安装所有依赖...\n'));
    
    try {
      await installNodeDependencies();
      await installPythonDependencies();
      console.log(chalk.green('\n✓ 所有依赖安装完成！\n'));
    } catch (error) {
      console.error(chalk.red('\n✗ 安装失败:'), error.message);
      process.exit(1);
    }
  });

program.parse(process.argv);

if (!process.argv.slice(2).length) {
  program.outputHelp();
}

async function fullInstall() {
  const spinner = ora('检查环境...').start();
  
  try {
    await checkNode();
    spinner.succeed('Node.js 检查通过');
    
    spinner.start('检查 Python...');
    await checkPython();
    spinner.succeed('Python 检查通过');
    
    spinner.start('创建必要目录...');
    await createDirectories();
    spinner.succeed('目录创建完成');
    
    spinner.start('创建环境配置文件...');
    await createEnvFile();
    spinner.succeed('环境配置完成');
    
    spinner.start('安装 Node.js 依赖...');
    await installNodeDependencies();
    spinner.succeed('Node.js 依赖安装完成');
    
    spinner.start('安装 Python 依赖...');
    await installPythonDependencies();
    spinner.succeed('Python 依赖安装完成');
    
  } catch (error) {
    spinner.fail('安装失败');
    throw error;
  }
}

async function ensureEnvironment() {
  try {
    await checkNode();
    await checkPython();
    await createDirectories();
    await createEnvFile();
  } catch (error) {
    console.log(chalk.yellow('\n⚠  环境不完整，请先运行: 清悦印象 install\n'));
    throw error;
  }
}

async function checkEnvironment() {
  console.log(chalk.blue('检查 Node.js...'));
  const nodeVersion = process.version;
  console.log(chalk.green(`  ✓ Node.js: ${nodeVersion}`));
  
  console.log(chalk.blue('\n检查 Python...'));
  const python = await findPython();
  if (python) {
    const result = await runCommand(python, ['--version'], { capture: true });
    console.log(chalk.green(`  ✓ Python: ${result.stdout.trim()}`));
  } else {
    console.log(chalk.yellow('  ⚠ Python 未找到'));
  }
  
  console.log(chalk.blue('\n检查项目文件...'));
  const requiredFiles = [
    'main.py',
    'requirements.txt',
    'package.json'
  ];
  
  for (const file of requiredFiles) {
    const filePath = path.join(PROJECT_ROOT, file);
    if (fs.existsSync(filePath)) {
      console.log(chalk.green(`  ✓ ${file}`));
    } else {
      console.log(chalk.red(`  ✗ ${file} (缺失)`));
    }
  }
  
  console.log(chalk.blue('\n检查目录...'));
  const requiredDirs = ['src', 'config', 'prompts', 'skills'];
  for (const dir of requiredDirs) {
    const dirPath = path.join(PROJECT_ROOT, dir);
    if (fs.existsSync(dirPath)) {
      console.log(chalk.green(`  ✓ ${dir}/`));
    } else {
      console.log(chalk.red(`  ✗ ${dir}/ (缺失)`));
    }
  }
}

async function checkNode() {
  const nodeVersion = process.version;
  const major = parseInt(nodeVersion.slice(1).split('.')[0]);
  
  if (major < 16) {
    throw new Error(`Node.js 版本过低: ${nodeVersion}, 需要 16.0+`);
  }
}

async function checkPython() {
  const python = await findPython();
  if (!python) {
    throw new Error('未找到 Python，请先安装 Python 3.10+');
  }
  
  try {
    const result = await runCommand(python, ['--version'], { capture: true });
    const versionMatch = result.stdout.match(/Python (\d+)\.(\d+)/);
    if (versionMatch) {
      const major = parseInt(versionMatch[1]);
      const minor = parseInt(versionMatch[2]);
      if (major < 3 || (major === 3 && minor < 10)) {
        throw new Error(`Python 版本过低: ${result.stdout.trim()}, 需要 3.10+`);
      }
    }
  } catch (error) {
    throw new Error('Python 检查失败: ' + error.message);
  }
}

async function findPython() {
  const candidates = ['python3', 'python', 'py'];
  
  for (const cmd of candidates) {
    try {
      const cmdPath = await which(cmd, { nothrow: true });
      if (cmdPath) {
        const result = await runCommand(cmd, ['--version'], { capture: true, throwOnError: true });
        if (result.stdout && result.stdout.includes('Python 3.')) {
          return cmd;
        }
      }
    } catch {
      continue;
    }
  }
  
  return null;
}

async function createDirectories() {
  const dirs = ['models', 'outputs', 'config', 'data'];
  for (const dir of dirs) {
    const dirPath = path.join(PROJECT_ROOT, dir);
    await fs.ensureDir(dirPath);
  }
}

async function createEnvFile() {
  const envExample = path.join(PROJECT_ROOT, '.env.example');
  const env = path.join(PROJECT_ROOT, '.env');
  
  if (fs.existsSync(envExample) && !fs.existsSync(env)) {
    await fs.copy(envExample, env);
  }
}

async function installNodeDependencies() {
  const packageJsonPath = path.join(PROJECT_ROOT, 'package.json');
  if (!fs.existsSync(packageJsonPath)) {
    throw new Error('package.json 文件不存在');
  }
  
  await runCommand('npm', ['install'], {
    cwd: PROJECT_ROOT
  });
}

async function installPythonDependencies() {
  const python = await findPython();
  if (!python) {
    throw new Error('未找到 Python，请先安装 Python 3.10+');
  }
  
  const requirementsPath = path.join(PROJECT_ROOT, 'requirements.txt');
  if (!fs.existsSync(requirementsPath)) {
    throw new Error('requirements.txt 文件不存在');
  }
  
  await runCommand(python, ['-m', 'pip', 'install', '-r', requirementsPath], {
    cwd: PROJECT_ROOT
  });
}

async function startApiService(options) {
  const python = await findPython();
  const args = ['main.py', 'api'];
  
  if (options.port) args.push('--port', options.port);
  if (options.host) args.push('--host', options.host);
  if (options.reload) args.push('--reload');
  
  console.log(chalk.green('✓ API 服务已启动'));
  console.log(chalk.gray(`  访问: http://${options.host || 'localhost'}:${options.port || '8000'}`));
  console.log(chalk.gray(`  文档: http://${options.host || 'localhost'}:${options.port || '8000'}/docs`));
  console.log();
  
  await runCommand(python, args, {
    cwd: PROJECT_ROOT,
    stdio: 'inherit'
  });
}

async function startUiService(options) {
  process.env.UI_PORT = options.port;
  process.env.UI_HOST = options.host;
  process.env.API_URL = options.apiUrl;
  
  const serverPath = path.join(PROJECT_ROOT, 'ui', 'server.js');
  
  console.log(chalk.green('✓ UI 服务已启动'));
  console.log(chalk.gray(`  访问: http://${options.host || 'localhost'}:${options.port || '3000'}`));
  console.log(chalk.gray(`  API: ${options.apiUrl}`));
  console.log();
  
  await runCommand('node', [serverPath], {
    cwd: PROJECT_ROOT,
    stdio: 'inherit'
  });
}

function runCommand(cmd, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, args, {
      cwd: options.cwd || PROJECT_ROOT,
      stdio: options.stdio || (options.capture ? 'pipe' : 'inherit'),
      shell: process.platform === 'win32'
    });
    
    let stdout = '';
    let stderr = '';
    
    if (options.capture) {
      child.stdout?.on('data', (data) => {
        stdout += data.toString();
      });
      
      child.stderr?.on('data', (data) => {
        stderr += data.toString();
      });
    }
    
    child.on('close', (code) => {
      if (code !== 0 && options.throwOnError !== false) {
        const error = new Error(`命令执行失败: ${cmd} ${args.join(' ')}`);
        error.code = code;
        error.stdout = stdout;
        error.stderr = stderr;
        reject(error);
      } else {
        resolve({ code, stdout, stderr });
      }
    });
    
    child.on('error', reject);
  });
}
