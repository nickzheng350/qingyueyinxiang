/**
 * Axum 文件服务器日志示例（Node.js 版本）
 *
 * 这个文件用 Node.js 模拟了 Axum 服务器的文件上传和下载日志功能
 * 用于在没有 Rust 环境的机器上测试和验证日志输出格式
 *
 * 运行方式：
 * node docs/axum_file_server_mock.js
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// 日志级别
const LogLevel = {
    DEBUG: 'DEBUG',
    INFO: 'INFO',
    ERROR: 'ERROR'
};

// 获取当前时间戳
function getTimestamp() {
    const now = new Date();
    return now.toISOString();
}

// 日志输出函数
function log(level, message) {
    console.log(`[${level}] ${getTimestamp()} - ${message}`);
}

function logInfo(message) { log(LogLevel.INFO, message); }
function logDebug(message) { log(LogLevel.DEBUG, message); }
function logError(message) { log(LogLevel.ERROR, message); }

// 文件上传处理
function handleFileUpload(req) {
    return new Promise((resolve, reject) => {
        const startTime = Date.now();
        logInfo('=== 开始处理文件上传 ===');
        logDebug('解析 multipart 表单...');

        const chunks = [];
        req.on('data', (chunk) => {
            chunks.push(chunk);
            logDebug(`接收数据块: ${chunk.length} bytes`);
        });

        req.on('end', () => {
            const data = Buffer.concat(chunks);
            const dataSize = data.length;

            logInfo(`文件读取完成，大小：${dataSize} bytes (${(dataSize / 1024).toFixed(2)} KB)`);

            // 模拟保存文件
            const filePath = path.join('/tmp', `upload_${Date.now()}.dat`);
            fs.writeFileSync(filePath, data);

            logInfo(`文件写入完成：${filePath}`);

            const elapsed = Date.now() - startTime;
            logInfo(`上传处理完成，耗时：${elapsed} ms`);

            resolve({
                status: 'success',
                filename: 'upload.dat',
                size: dataSize,
                size_kb: (dataSize / 1024).toFixed(2),
                processing_time_ms: elapsed
            });
        });

        req.on('error', (err) => {
            logError(`上传处理失败：${err.message}`);
            reject(err);
        });
    });
}

// 多文件上传处理
function handleMultipleUpload(req) {
    return new Promise((resolve, reject) => {
        const startTime = Date.now();
        logInfo('=== 开始处理多文件上传 ===');

        const chunks = [];
        let totalSize = 0;
        let fileCount = 0;

        req.on('data', (chunk) => {
            chunks.push(chunk);
            totalSize += chunk.length;
            fileCount++;
            logDebug(`接收数据块 [${fileCount}]: ${chunk.length} bytes`);
        });

        req.on('end', () => {
            const data = Buffer.concat(chunks);

            logInfo(`多文件上传完成，共 ${fileCount} 个文件，总大小 ${(totalSize / 1024).toFixed(2)} KB`);

            const elapsed = Date.now() - startTime;
            logInfo(`处理耗时：${elapsed} ms`);

            resolve({
                status: 'success',
                total_files: fileCount,
                total_size: totalSize,
                processing_time_ms: elapsed
            });
        });

        req.on('error', (err) => {
            logError(`多文件上传失败：${err.message}`);
            reject(err);
        });
    });
}

// 文件下载处理
function handleFileDownload(filename) {
    const startTime = Date.now();
    logInfo('=== 开始处理文件下载 ===');

    const filePath = path.join('/tmp', filename);
    logDebug(`请求文件路径：${filePath}`);

    if (!fs.existsSync(filePath)) {
        logError(`文件不存在：${filePath}`);
        return {
            statusCode: 404,
            error: 'File not found'
        };
    }

    const stats = fs.statSync(filePath);
    const fileSize = stats.size;

    logInfo(`文件存在，大小：${fileSize} bytes (${(fileSize / 1024).toFixed(2)} KB)`);
    logDebug('读取文件内容...');

    const data = fs.readFileSync(filePath);

    const elapsed = Date.now() - startTime;
    logInfo(`文件读取完成，耗时：${elapsed} ms`);
    logInfo('下载响应已发送');

    return {
        statusCode: 200,
        headers: {
            'Content-Disposition': `attachment; filename=${filename}`,
            'Content-Type': 'application/octet-stream',
            'Content-Length': fileSize
        },
        data: data
    };
}

// 异步下载任务
const downloadTasks = new Map();

function handleCreateDownloadTask(url, filename) {
    const startTime = Date.now();
    const taskId = crypto.randomUUID();

    logInfo('=== 创建异步下载任务 ===');
    logInfo(`任务 ID: ${taskId}`);
    logInfo(`下载 URL: ${url}`);
    logInfo(`目标文件名：${filename || 'downloaded.zip'}`);

    const task = {
        id: taskId,
        status: 'pending',
        progress: 0,
        url: url,
        filename: filename || 'downloaded.zip',
        started_at: getTimestamp()
    };

    downloadTasks.set(taskId, task);

    // 模拟异步下载
    simulateDownload(taskId);

    const elapsed = Date.now() - startTime;
    logInfo(`任务创建完成，耗时：${elapsed} ms`);

    return {
        task_id: taskId,
        status: 'started',
        filename: task.filename,
        processing_time_ms: elapsed
    };
}

function simulateDownload(taskId) {
    let progress = 0;

    const interval = setInterval(() => {
        progress += 10;

        const task = downloadTasks.get(taskId);
        if (!task) {
            clearInterval(interval);
            return;
        }

        task.progress = progress;

        if (progress % 20 === 0) {
            logInfo(`任务 [${taskId}] 进度：${progress}%`);
        }

        if (progress >= 100) {
            task.status = 'completed';
            task.completed_at = getTimestamp();
            logInfo(`任务 [${taskId}] 完成，文件路径：/tmp/${task.filename}`);
            clearInterval(interval);
        }
    }, 100);
}

function handleGetDownloadStatus(taskId) {
    logDebug(`查询任务状态：${taskId}`);

    const task = downloadTasks.get(taskId);

    if (task) {
        logInfo(`任务 [${taskId}] 状态：${task.status} (${task.progress}%)`);
        return {
            task_id: task.id,
            status: task.status,
            progress: task.progress,
            filename: task.filename,
            started_at: task.started_at,
            completed_at: task.completed_at || null
        };
    } else {
        logError(`任务不存在：${taskId}`);
        return {
            statusCode: 404,
            error: 'Task not found'
        };
    }
}

// SSE 进度推送
function handleSSEProgress(res) {
    logInfo('=== 开始 SSE 进度推送 ===');

    res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    });

    logInfo('SSE 流已建立');

    let progress = 0;

    const interval = setInterval(() => {
        progress += 10;

        if (progress > 100) {
            logInfo('SSE 推送完成');
            clearInterval(interval);
            res.end();
            return;
        }

        const event = `data: {"progress": ${progress}}\n\n`;
        res.write(event);

        if (progress % 20 === 0) {
            logInfo(`SSE 推送进度：${progress}%`);
        }
    }, 100);

    res.on('close', () => {
        clearInterval(interval);
        logInfo('SSE 连接关闭');
    });
}

// 系统状态
function handleGetStatus() {
    logDebug('获取系统状态');

    const uploadedFiles = ['file1.zip', 'file2.tar.gz'];
    const tasks = Array.from(downloadTasks.values());

    const activeTasks = tasks.filter(t => t.status !== 'completed').length;
    const completedTasks = tasks.filter(t => t.status === 'completed').length;

    logInfo(`系统状态：${uploadedFiles.length} 个上传文件，${activeTasks} 个活跃任务，${completedTasks} 个完成任务`);

    return {
        uploaded_files: uploadedFiles,
        uploaded_count: uploadedFiles.length,
        active_tasks: activeTasks,
        completed_tasks: completedTasks,
        total_tasks: tasks.length
    };
}

// 创建测试文件
function createTestFile() {
    const testFile = '/tmp/test_download.txt';
    const content = 'This is a test file for download.\n'.repeat(100);
    fs.writeFileSync(testFile, content);
    logInfo(`测试文件已创建：${testFile} (${content.length} bytes)`);
    return testFile;
}

// 主函数 - 演示所有功能
async function demonstrate() {
    console.log('==========================================');
    console.log('  Axum 文件服务器日志示例（Node.js）');
    console.log('==========================================');
    console.log('');

    // 创建测试文件
    const testFile = createTestFile();

    console.log('');
    logInfo('开始功能演示...');
    console.log('');

    // 1. 文件上传
    console.log('\n--- 1. 单文件上传演示 ---\n');
    const uploadResult = await simulateUpload('test_upload.zip', 1024 * 50);

    // 2. 多文件上传
    console.log('\n--- 2. 多文件上传演示 ---\n');
    const multiUploadResult = await simulateUpload('multi.zip', 1024 * 100);

    // 3. 文件下载
    console.log('\n--- 3. 文件下载演示 ---\n');
    const downloadResult = handleFileDownload(path.basename(testFile));

    // 4. 异步下载任务
    console.log('\n--- 4. 异步下载任务演示 ---\n');
    const taskResult = handleCreateDownloadTask('http://example.com/file.zip', 'downloaded.zip');

    // 等待下载完成
    await new Promise(resolve => setTimeout(resolve, 1500));

    // 5. 查询任务状态
    console.log('\n--- 5. 查询任务状态 ---\n');
    const statusResult = handleGetDownloadStatus(taskResult.task_id);

    // 6. 系统状态
    console.log('\n--- 6. 系统状态 ---\n');
    const sysStatus = handleGetStatus();

    // 7. SSE 进度推送
    console.log('\n--- 7. SSE 进度推送演示 ---\n');
    // SSE 演示（在实际服务器中会持续推送）

    console.log('\n==========================================');
    console.log('  演示完成！');
    console.log('==========================================\n');

    console.log('📊 性能统计：');
    console.log(`   单文件上传: ${uploadResult.processing_time_ms}ms`);
    console.log(`   多文件上传: ${multiUploadResult.processing_time_ms}ms`);
    console.log(`   文件下载: ${downloadResult.processing_time_ms || '<1'}ms`);
    console.log(`   任务创建: ${taskResult.processing_time_ms}ms`);
    console.log(`   任务完成: ${statusResult.progress === 100 ? '1.2s' : 'N/A'}`);

    console.log('\n💡 注意：');
    console.log('   这是用 Node.js 模拟的 Axum 日志输出。');
    console.log('   实际的 Axum 服务器会用 Rust 编写，性能会更好。');

    console.log('\n📖 详细文档：');
    console.log('   • Axum 文件处理: docs/Axum_File_Handling.md');
    console.log('   • Axum 示例代码: docs/axum_file_server.rs');

    // 清理测试文件
    fs.unlinkSync(testFile);
    logInfo('测试文件已清理');
}

// 模拟上传函数
function simulateUpload(filename, size) {
    const startTime = Date.now();
    logInfo('=== 开始处理文件上传 ===');
    logDebug('解析 multipart 表单...');

    logInfo(`接收到文件字段: name=file, filename=${filename}`);
    logDebug('开始读取文件数据...');

    const data = Buffer.alloc(size);
    logInfo(`文件读取完成，大小：${data.length} bytes (${(data.length / 1024).toFixed(2)} KB)`);

    logDebug(`准备写入文件：/tmp/${filename}`);
    logInfo(`文件写入完成：/tmp/${filename}`);

    const elapsed = Date.now() - startTime;
    logInfo(`上传处理完成，耗时：${elapsed} ms`);

    return {
        status: 'success',
        filename: filename,
        size: size,
        size_kb: (size / 1024).toFixed(2),
        processing_time_ms: elapsed
    };
}

// 运行演示
demonstrate().catch(console.error);
