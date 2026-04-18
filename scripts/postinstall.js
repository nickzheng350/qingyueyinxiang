#!/usr/bin/env node

const chalk = require('chalk');

console.log(chalk.cyan.bold('\n✨ HydraFlow AI 安装成功！\n'));
console.log(chalk.green('快速开始:'));
console.log();
console.log(chalk.blue('  1. 一键安装所有依赖:'));
console.log(chalk.gray('     hydraflow install'));
console.log();
console.log(chalk.blue('  2. 检查环境:'));
console.log(chalk.gray('     hydraflow check'));
console.log();
console.log(chalk.blue('  3. 启动 API 服务:'));
console.log(chalk.gray('     hydraflow api'));
console.log();
console.log(chalk.blue('  4. 启动 UI 服务 (另一个终端):'));
console.log(chalk.gray('     hydraflow ui'));
console.log();
console.log(chalk.yellow('📖 详细文档:'));
console.log(chalk.gray('  查看 docs/00-快速开始指南.md 了解完整使用说明'));
console.log();
