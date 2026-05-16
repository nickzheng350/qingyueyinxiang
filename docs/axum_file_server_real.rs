//! Axum 文件服务器 - 带详细日志输出
//! 
//! 功能：
//! - 文件上传（单文件/多文件）
//! - 文件下载
//! - 异步下载任务
//! - SSE 进度推送
//! - 详细日志输出

use axum::{
    extract::{Multipart, Path},
    http::{header, StatusCode},
    response::{IntoResponse, Json, Sse},
    routing::{get, post},
    Router,
};
use chrono::{Local, SecondsFormat};
use futures::Stream;
use serde::{Deserialize, Serialize};
use std::{
    collections::{HashMap, VecDeque},
    sync::{Arc, Mutex},
    time::{Duration, Instant},
};
use tokio::time::interval;
use tokio_stream::wrappers::IntervalStream;
use uuid::Uuid;

// 日志级别
#[derive(Debug, Clone, PartialEq, Eq)]
enum LogLevel {
    INFO,
    DEBUG,
    ERROR,
}

impl std::fmt::Display for LogLevel {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            LogLevel::INFO => write!(f, "INFO"),
            LogLevel::DEBUG => write!(f, "DEBUG"),
            LogLevel::ERROR => write!(f, "ERROR"),
        }
    }
}

// 日志宏
macro_rules! log_info {
    ($($arg:tt)*) => {
        log(LogLevel::INFO, &format!($($arg)*));
    };
}

macro_rules! log_debug {
    ($($arg:tt)*) => {
        log(LogLevel::DEBUG, &format!($($arg)*));
    };
}

macro_rules! log_error {
    ($($arg:tt)*) => {
        log(LogLevel::ERROR, &format!($($arg)*));
    };
}

fn log(level: LogLevel, message: &str) {
    let timestamp = Local::now().to_rfc3339_opts(SecondsFormat::Secs, true);
    match level {
        LogLevel::ERROR => eprintln!("[{}] {} - {}", level, timestamp, message),
        _ => println!("[{}] {} - {}", level, timestamp, message),
    }
}

// 任务状态
#[derive(Debug, Clone, Serialize)]
enum TaskStatus {
    Pending,
    InProgress(u32),
    Completed,
    Failed(String),
}

// 下载任务
#[derive(Debug, Clone, Serialize)]
struct DownloadTask {
    id: String,
    url: String,
    filename: String,
    status: TaskStatus,
    created_at: String,
    completed_at: Option<String>,
}

// 应用状态
struct AppState {
    tasks: Mutex<HashMap<String, DownloadTask>>,
    uploaded_files: Mutex<VecDeque<String>>,
}

// 上传响应
#[derive(Debug, Serialize)]
struct UploadResponse {
    status: String,
    filename: String,
    size: usize,
    size_kb: String,
    path: String,
    processing_time_ms: i64,
    timestamp: String,
}

// 任务响应
#[derive(Debug, Serialize)]
struct TaskResponse {
    id: String,
    status: String,
    progress: u32,
    message: String,
}

// 系统状态响应
#[derive(Debug, Serialize)]
struct SystemStatusResponse {
    uploaded_files: usize,
    active_tasks: usize,
    completed_tasks: usize,
}

// 文件上传 - 详细日志版本
async fn upload_file(
    multipart: Multipart,
    state: Arc<AppState>,
) -> impl IntoResponse {
    log_info!("=== 开始处理文件上传 ===");
    let start_time = Instant::now();

    log_debug!("解析 multipart 表单...");

    let mut response = Vec::new();

    while let Some(field) = multipart.next_field().await.unwrap() {
        let name = field.name().unwrap_or("unknown").to_string();
        let filename = field.file_name().unwrap_or("unknown").to_string();

        log_info!("接收到文件字段: name={}, filename={}", name, filename);
        log_debug!("开始读取文件数据...");

        let data = field.bytes().await.unwrap();
        let data_size = data.len();

        log_info!("文件读取完成，大小：{} bytes ({:.2} KB)", 
            data_size, data_size as f64 / 1024.0);

        // 模拟写入文件（实际项目中应写入真实路径）
        let file_path = format!("/tmp/{}", filename);
        log_debug!("准备写入文件：{}", file_path);
        
        tokio::fs::write(&file_path, &data).await.unwrap();
        log_info!("文件写入完成：{}", file_path);

        // 记录上传的文件
        state.uploaded_files.lock().unwrap().push_back(filename.clone());

        let elapsed = start_time.elapsed().as_millis() as i64;

        response.push(UploadResponse {
            status: "success".to_string(),
            filename,
            size: data_size,
            size_kb: format!("{:.2}", data_size as f64 / 1024.0),
            path: file_path,
            processing_time_ms: elapsed,
            timestamp: Local::now().to_rfc3339_opts(SecondsFormat::Secs, true),
        });
    }

    let elapsed = start_time.elapsed().as_millis() as i64;
    log_info!("上传处理完成，耗时：{} ms", elapsed);

    if response.is_empty() {
        log_error!("上传失败：未找到文件");
        return (StatusCode::BAD_REQUEST, "No file uploaded").into_response();
    }

    Json(response).into_response()
}

// 文件下载
async fn download_file(Path(filename): Path<String>) -> impl IntoResponse {
    log_info!("=== 开始处理文件下载 ===");
    let start_time = Instant::now();

    let file_path = format!("/tmp/{}", filename);
    log_debug!("请求文件路径：{}", file_path);

    match tokio::fs::read(&file_path).await {
        Ok(content) => {
            let file_size = content.len();
            log_info!("文件存在，大小：{} bytes ({:.2} KB)", 
                file_size, file_size as f64 / 1024.0);

            log_debug!("读取文件内容...");
            
            let elapsed = start_time.elapsed().as_millis() as i64;
            log_info!("文件读取完成，耗时：{} ms", elapsed);
            log_info!("下载响应已发送");

            (
                StatusCode::OK,
                [
                    (header::CONTENT_TYPE, "application/octet-stream"),
                    (
                        header::CONTENT_DISPOSITION,
                        format!("attachment; filename=\"{}\"", filename),
                    ),
                ],
                content,
            )
                .into_response()
        }
        Err(e) => {
            log_error!("文件不存在或读取失败：{}", e);
            (StatusCode::NOT_FOUND, format!("File not found: {}", e)).into_response()
        }
    }
}

// 创建异步下载任务
async fn create_download_task(
    state: Arc<AppState>,
    Json(payload): Json<DownloadRequest>,
) -> impl IntoResponse {
    log_info!("=== 创建异步下载任务 ===");
    let start_time = Instant::now();

    let task_id = Uuid::new_v4().to_string();
    log_info!("任务 ID: {}", task_id);
    log_info!("下载 URL: {}", payload.url);
    log_info!("目标文件名：{}", payload.filename);

    let task = DownloadTask {
        id: task_id.clone(),
        url: payload.url,
        filename: payload.filename.clone(),
        status: TaskStatus::Pending,
        created_at: Local::now().to_rfc3339_opts(SecondsFormat::Secs, true),
        completed_at: None,
    };

    state.tasks.lock().unwrap().insert(task_id.clone(), task);

    // 启动异步下载任务
    let state_clone = Arc::clone(&state);
    tokio::spawn(async move {
        simulate_download(state_clone, task_id, payload.filename).await;
    });

    let elapsed = start_time.elapsed().as_millis() as i64;
    log_info!("任务创建完成，耗时：{} ms", elapsed);

    Json(TaskResponse {
        id: task_id,
        status: "pending".to_string(),
        progress: 0,
        message: "Task created".to_string(),
    })
    .into_response()
}

// 模拟下载过程
async fn simulate_download(state: Arc<AppState>, task_id: String, filename: String) {
    // 更新状态为进行中
    {
        let mut tasks = state.tasks.lock().unwrap();
        if let Some(task) = tasks.get_mut(&task_id) {
            task.status = TaskStatus::InProgress(0);
        }
    }

    // 模拟下载进度（每200ms增加20%）
    for progress in (20..=100).step_by(20) {
        tokio::time::sleep(Duration::from_millis(200)).await;
        
        {
            let mut tasks = state.tasks.lock().unwrap();
            if let Some(task) = tasks.get_mut(&task_id) {
                task.status = TaskStatus::InProgress(progress);
            }
        }
        
        log_info!("任务 [{}] 进度：{}%", task_id, progress);
    }

    // 标记完成
    {
        let mut tasks = state.tasks.lock().unwrap();
        if let Some(task) = tasks.get_mut(&task_id) {
            task.status = TaskStatus::Completed;
            task.completed_at = Some(Local::now().to_rfc3339_opts(SecondsFormat::Secs, true));
        }
    }

    log_info!("任务 [{}] 完成，文件路径：/tmp/{}", task_id, filename);
}

// 查询任务状态
async fn get_task_status(
    state: Arc<AppState>,
    Path(task_id): Path<String>,
) -> impl IntoResponse {
    log_debug!("查询任务状态：{}", task_id);

    let tasks = state.tasks.lock().unwrap();
    match tasks.get(&task_id) {
        Some(task) => {
            let (status_str, progress) = match &task.status {
                TaskStatus::Pending => ("pending".to_string(), 0),
                TaskStatus::InProgress(p) => ("in_progress".to_string(), *p),
                TaskStatus::Completed => ("completed".to_string(), 100),
                TaskStatus::Failed(e) => ("failed".to_string(), 0),
            };
            
            log_info!("任务 [{}] 状态：{} ({})", task_id, status_str, progress);
            
            Json(TaskResponse {
                id: task_id,
                status: status_str,
                progress,
                message: "Status retrieved".to_string(),
            })
            .into_response()
        }
        None => {
            log_error!("任务不存在：{}", task_id);
            (StatusCode::NOT_FOUND, "Task not found").into_response()
        }
    }
}

// 获取系统状态
async fn get_system_status(state: Arc<AppState>) -> impl IntoResponse {
    log_debug!("获取系统状态");

    let uploaded_files = state.uploaded_files.lock().unwrap().len();
    let tasks = state.tasks.lock().unwrap();
    
    let active_tasks = tasks.values().filter(|t| matches!(t.status, TaskStatus::Pending | TaskStatus::InProgress(_))).count();
    let completed_tasks = tasks.values().filter(|t| matches!(t.status, TaskStatus::Completed)).count();

    log_info!("系统状态：{} 个上传文件，{} 个活跃任务，{} 个完成任务", 
        uploaded_files, active_tasks, completed_tasks);

    Json(SystemStatusResponse {
        uploaded_files,
        active_tasks,
        completed_tasks,
    })
    .into_response()
}

// SSE 进度推送
async fn sse_progress(
    state: Arc<AppState>,
    Path(task_id): Path<String>,
) -> Sse<impl Stream<Item = Result<axum::response::sse::Event, axum::Error>>> {
    log_info!("=== SSE 进度推送 ===");
    log_info!("订阅任务进度：{}", task_id);

    let stream = IntervalStream::new(interval(Duration::from_millis(500)))
        .map(move |_| {
            let tasks = state.tasks.lock().unwrap();
            match tasks.get(&task_id) {
                Some(task) => {
                    let progress = match &task.status {
                        TaskStatus::InProgress(p) => *p,
                        TaskStatus::Completed => 100,
                        _ => 0,
                    };
                    let status = match &task.status {
                        TaskStatus::Pending => "pending",
                        TaskStatus::InProgress(_) => "in_progress",
                        TaskStatus::Completed => "completed",
                        TaskStatus::Failed(_) => "failed",
                    };

                    let data = serde_json::json!({
                        "task_id": task.id,
                        "status": status,
                        "progress": progress,
                        "filename": task.filename,
                    });

                    Ok(axum::response::sse::Event::default().data(data.to_string()))
                }
                None => Ok(axum::response::sse::Event::default().data(r#"{"error": "Task not found"}"#)),
            }
        });

    Sse::new(stream)
}

// 下载请求结构
#[derive(Debug, Deserialize)]
struct DownloadRequest {
    url: String,
    filename: String,
}

#[tokio::main]
async fn main() {
    log_info!("=== Axum 文件服务器启动 ===");
    log_info!("初始化应用状态...");

    // 初始化应用状态
    let state = Arc::new(AppState {
        tasks: Mutex::new(HashMap::new()),
        uploaded_files: Mutex::new(VecDeque::new()),
    });

    log_info!("配置路由...");

    // 构建路由
    let app = Router::new()
        .route("/upload", post(upload_file))
        .route("/download/:filename", get(download_file))
        .route("/task", post(create_download_task))
        .route("/task/:task_id", get(get_task_status))
        .route("/task/:task_id/progress", get(sse_progress))
        .route("/status", get(get_system_status))
        .with_state(state);

    // 启动服务器
    let addr = std::net::SocketAddr::from(([127, 0, 0, 1], 3000));
    log_info!("启动服务器，监听地址：{}", addr);

    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await
        .unwrap();
}
