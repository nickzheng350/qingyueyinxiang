use axum::{
    extract::{Multipart, Path, Query},
    http::{Response, StatusCode, HeaderMap, HeaderValue},
    routing::{get, post},
    Json, Router,
};
use futures_util::{stream, StreamExt};
use serde::Deserialize;
use std::{
    fs::File,
    io::Write,
    path::PathBuf,
    sync::{Arc, Mutex},
    time::Duration,
    collections::HashMap,
};
use tokio::{fs::File as TokioFile, io::AsyncReadExt};
use tokio_util::io::ReaderStream;
use uuid::Uuid;
use chrono::Local;

// 日志宏
macro_rules! log_info {
    ($($arg:tt)*) => {
        println!("[INFO] {} - {}", Local::now().format("%Y-%m-%d %H:%M:%S"), format!($($arg)*))
    }
}

macro_rules! log_error {
    ($($arg:tt)*) => {
        eprintln!("[ERROR] {} - {}", Local::now().format("%Y-%m-%d %H:%M:%S"), format!($($arg)*))
    }
}

macro_rules! log_debug {
    ($($arg:tt)*) => {
        println!("[DEBUG] {} - {}", Local::now().format("%Y-%m-%d %H:%M:%S"), format!($($arg)*))
    }
}

// 应用状态
struct AppState {
    download_tasks: Mutex<Vec<DownloadTask>>,
    uploaded_files: Mutex<Vec<String>>,
    task_history: Mutex<HashMap<String, Vec<TaskEvent>>>,
}

#[derive(Debug, Clone)]
struct DownloadTask {
    id: String,
    status: String,
    progress: u32,
    file_path: String,
    started_at: String,
    completed_at: Option<String>,
}

#[derive(Debug, Clone)]
struct TaskEvent {
    timestamp: String,
    event: String,
    details: String,
}

#[derive(Deserialize)]
struct DownloadQuery {
    url: String,
    filename: Option<String>,
}

#[tokio::main]
async fn main() {
    // 初始化日志
    log_info!("=== Axum 文件处理服务启动 ===");
    log_info!("环境：{}", std::env::consts::OS);
    log_info!("Rust 版本：{}", std::env!("CARGO_PKG_VERSION"));
    
    let app_state = Arc::new(AppState {
        download_tasks: Mutex::new(Vec::new()),
        uploaded_files: Mutex::new(Vec::new()),
        task_history: Mutex::new(HashMap::new()),
    });

    let app = Router::new()
        // 文件上传路由
        .route("/upload", post(upload_file))
        .route("/upload/multiple", post(upload_multiple_files))
        .route("/upload/progress", post(upload_with_progress))
        
        // 文件下载路由
        .route("/download/:filename", get(download_file))
        .route("/download/large/:filename", get(download_large_file))
        
        // 异步下载任务路由
        .route("/download/task", post(create_download_task))
        .route("/download/task/:task_id", get(get_download_status))
        
        // SSE 路由
        .route("/progress/sse", get(sse_progress))
        
        // 状态路由
        .route("/status", get(get_status))
        
        .with_state(app_state);

    let addr = "0.0.0.0:8000";
    log_info!("服务器监听地址：{}", addr);
    log_info!("访问 http://{} 查看服务状态", addr);
    
    axum::Server::bind(&addr.parse().unwrap())
        .serve(app.into_make_service())
        .await
        .unwrap();
}

// 文件上传 - 详细日志版本
async fn upload_file(
    mut multipart: Multipart,
    state: Arc<AppState>,
) -> impl IntoResponse {
    log_info!("=== 开始处理文件上传 ===");
    let start_time = Local::now();
    
    log_debug!("解析 multipart 表单...");
    
    while let Some(field) = multipart.next_field().await.unwrap() {
        let name = field.name().unwrap().to_string();
        let filename = field.file_name().unwrap().to_string();
        
        log_info!("接收到文件字段: name={}, filename={}", name, filename);
        log_debug!("开始读取文件数据...");
        
        let data = field.bytes().await.unwrap();
        let data_size = data.len();
        
        log_info!("文件读取完成，大小：{} bytes ({:.2} KB)", 
            data_size, data_size as f64 / 1024.0);
        
        let file_path = PathBuf::from("/tmp").join(&filename);
        log_debug!("准备写入文件：{:?}", file_path);
        
        let mut file = File::create(&file_path).unwrap();
        file.write_all(&data).unwrap();
        
        log_info!("文件写入完成：{:?}", file_path);
        
        state.uploaded_files.lock().unwrap().push(filename.clone());
        
        let elapsed = Local::now().signed_duration_since(start_time).num_milliseconds();
        log_info!("上传处理完成，耗时：{} ms", elapsed);
        
        return Json(json!({
            "status": "success",
            "filename": filename,
            "size": data_size,
            "size_kb": format!("{:.2}", data_size as f64 / 1024.0),
            "path": file_path.to_string_lossy(),
            "processing_time_ms": elapsed,
            "timestamp": start_time.to_rfc3339()
        }));
    }
    
    log_error!("上传失败：未找到文件");
    (StatusCode::BAD_REQUEST, "No file uploaded").into_response()
}

// 多文件上传 - 详细日志版本
async fn upload_multiple_files(
    mut multipart: Multipart,
    state: Arc<AppState>,
) -> impl IntoResponse {
    log_info!("=== 开始处理多文件上传 ===");
    let start_time = Local::now();
    
    let mut uploaded_files = Vec::new();
    let mut total_size = 0u64;
    let mut file_count = 0u32;
    
    while let Some(field) = multipart.next_field().await.unwrap() {
        let filename = field.file_name().unwrap().to_string();
        file_count += 1;
        
        log_info!("处理文件 [{}/?]: {}", file_count, filename);
        
        let data = field.bytes().await.unwrap();
        let data_size = data.len() as u64;
        total_size += data_size;
        
        let file_path = PathBuf::from("/tmp").join(&filename);
        let mut file = File::create(&file_path).unwrap();
        file.write_all(&data).unwrap();
        
        state.uploaded_files.lock().unwrap().push(filename.clone());
        
        uploaded_files.push(json!({
            "filename": filename,
            "size": data_size,
            "size_kb": format!("{:.2}", data_size as f64 / 1024.0)
        }));
        
        log_info!("文件 [{}] 上传完成：{:.2} KB", filename, data_size as f64 / 1024.0);
    }
    
    let elapsed = Local::now().signed_duration_since(start_time).num_milliseconds();
    log_info!("多文件上传完成，共 {} 个文件，总大小 {:.2} KB，耗时 {} ms",
        file_count, total_size as f64 / 1024.0, elapsed);
    
    Json(json!({
        "status": "success",
        "files": uploaded_files,
        "total_files": file_count,
        "total_size": total_size,
        "total_size_kb": format!("{:.2}", total_size as f64 / 1024.0),
        "processing_time_ms": elapsed,
        "timestamp": start_time.to_rfc3339()
    }))
}

// 带进度的文件上传 - 详细日志版本
async fn upload_with_progress(
    mut multipart: Multipart,
) -> impl IntoResponse {
    log_info!("=== 开始处理带进度的文件上传 ===");
    let start_time = Local::now();
    
    while let Some(mut field) = multipart.next_field().await.unwrap() {
        let filename = field.file_name().unwrap().to_string();
        let file_path = PathBuf::from("/tmp").join(&filename);
        let mut file = File::create(&file_path).unwrap();
        let mut total_bytes = 0u64;
        let mut chunk_count = 0u32;
        
        log_info!("上传文件：{}", filename);
        log_debug!("目标路径：{:?}", file_path);
        
        while let Some(chunk) = field.chunk().await.unwrap() {
            let chunk_size = chunk.len();
            total_bytes += chunk_size as u64;
            chunk_count += 1;
            
            file.write_all(&chunk).unwrap();
            
            // 每 10% 打印一次进度
            if chunk_count % 10 == 0 {
                log_info!("上传进度：{} bytes ({:.2} KB)", 
                    total_bytes, total_bytes as f64 / 1024.0);
            }
        }
        
        let elapsed = Local::now().signed_duration_since(start_time).num_milliseconds();
        let speed = if elapsed > 0 {
            (total_bytes as f64 / elapsed as f64) * 1000.0
        } else {
            0.0
        };
        
        log_info!("上传完成：{} bytes, 平均速度：{:.2} KB/s", 
            total_bytes, speed / 1024.0);
        
        return Json(json!({
            "status": "success",
            "filename": filename,
            "size": total_bytes,
            "size_kb": format!("{:.2}", total_bytes as f64 / 1024.0),
            "avg_speed_kbs": format!("{:.2}", speed / 1024.0),
            "processing_time_ms": elapsed,
            "timestamp": start_time.to_rfc3339()
        }));
    }
    
    log_error!("上传失败：未找到文件");
    (StatusCode::BAD_REQUEST, "No file uploaded").into_response()
}

// 文件下载 - 详细日志版本
async fn download_file(Path(filename): Path<String>) -> Result<impl IntoResponse, StatusCode> {
    log_info!("=== 开始处理文件下载 ===");
    let start_time = Local::now();
    
    let path = PathBuf::from("/tmp").join(&filename);
    log_debug!("请求文件路径：{:?}", path);
    
    if !path.exists() {
        log_error!("文件不存在：{:?}", path);
        return Err(StatusCode::NOT_FOUND);
    }
    
    let metadata = std::fs::metadata(&path).unwrap();
    let file_size = metadata.len();
    log_info!("文件存在，大小：{} bytes ({:.2} KB)", file_size, file_size as f64 / 1024.0);
    
    log_debug!("打开文件...");
    let mut file = TokioFile::open(&path).await.map_err(|e| {
        log_error!("打开文件失败：{}", e);
        StatusCode::INTERNAL_SERVER_ERROR
    })?;
    
    log_debug!("读取文件内容...");
    let mut contents = Vec::new();
    file.read_to_end(&mut contents).await.map_err(|e| {
        log_error!("读取文件失败：{}", e);
        StatusCode::INTERNAL_SERVER_ERROR
    })?;
    
    let elapsed = Local::now().signed_duration_since(start_time).num_milliseconds();
    log_info!("文件读取完成，耗时：{} ms", elapsed);
    
    let mut headers = HeaderMap::new();
    headers.insert(
        "Content-Disposition",
        HeaderValue::from_str(&format!("attachment; filename={}", filename)).unwrap(),
    );
    headers.insert(
        "Content-Type",
        HeaderValue::from_static("application/octet-stream"),
    );
    headers.insert(
        "Content-Length",
        HeaderValue::from(file_size),
    );
    
    log_info!("下载响应已发送");
    
    Ok((StatusCode::OK, headers, contents))
}

// 大文件流式下载 - 详细日志版本
async fn download_large_file(Path(filename): Path<String>) -> Result<impl IntoResponse, StatusCode> {
    log_info!("=== 开始处理大文件流式下载 ===");
    let start_time = Local::now();
    
    let path = PathBuf::from("/tmp").join(&filename);
    log_debug!("请求文件路径：{:?}", path);
    
    if !path.exists() {
        log_error!("文件不存在：{:?}", path);
        return Err(StatusCode::NOT_FOUND);
    }
    
    let metadata = std::fs::metadata(&path).unwrap();
    let file_size = metadata.len();
    log_info!("文件存在，大小：{} bytes ({:.2} MB)", file_size, file_size as f64 / 1024.0 / 1024.0);
    
    log_debug!("创建文件流...");
    let file = TokioFile::open(&path).await.map_err(|e| {
        log_error!("打开文件失败：{}", e);
        StatusCode::INTERNAL_SERVER_ERROR
    })?;
    
    let stream = ReaderStream::new(file);
    log_info!("文件流创建成功");
    
    let mut headers = HeaderMap::new();
    headers.insert(
        "Content-Disposition",
        HeaderValue::from_str(&format!("attachment; filename={}", filename)).unwrap(),
    );
    headers.insert(
        "Content-Type",
        HeaderValue::from_static("application/octet-stream"),
    );
    headers.insert(
        "Transfer-Encoding",
        HeaderValue::from_static("chunked"),
    );
    headers.insert(
        "Content-Length",
        HeaderValue::from(file_size),
    );
    
    let elapsed = Local::now().signed_duration_since(start_time).num_milliseconds();
    log_info!("流式响应已发送，准备耗时：{} ms", elapsed);
    
    Ok(Response::new(axum::body::StreamBody::new(stream)))
}

// 创建下载任务 - 详细日志版本
async fn create_download_task(
    Query(params): Query<DownloadQuery>,
    state: Arc<AppState>,
) -> impl IntoResponse {
    log_info!("=== 创建异步下载任务 ===");
    let start_time = Local::now();
    
    let task_id = Uuid::new_v4().to_string();
    let filename = params.filename.unwrap_or_else(|| "downloaded.zip".to_string());
    
    log_info!("任务 ID: {}", task_id);
    log_info!("下载 URL: {}", params.url);
    log_info!("目标文件名：{}", filename);
    
    let task = DownloadTask {
        id: task_id.clone(),
        status: "pending".to_string(),
        progress: 0,
        file_path: "".to_string(),
        started_at: start_time.to_rfc3339(),
        completed_at: None,
    };
    
    state.download_tasks.lock().unwrap().push(task);
    
    // 记录任务事件
    let mut history = state.task_history.lock().unwrap();
    history.insert(task_id.clone(), vec![TaskEvent {
        timestamp: start_time.to_rfc3339(),
        event: "created".to_string(),
        details: format!("Task created for URL: {}", params.url),
    }]);
    
    // 启动异步下载任务
    let state_clone = state.clone();
    let task_id_clone = task_id.clone();
    let url = params.url.clone();
    let filename_clone = filename.clone();
    
    tokio::spawn(async move {
        log_info!("后台任务 [{}] 启动", task_id_clone);
        
        for i in 0..=100 {
            tokio::time::sleep(Duration::from_millis(50)).await;
            
            let mut tasks = state_clone.download_tasks.lock().unwrap();
            if let Some(t) = tasks.iter_mut().find(|t| t.id == task_id_clone) {
                t.progress = i;
                
                if i == 0 {
                    t.status = "downloading".to_string();
                    log_info!("任务 [{}] 状态：downloading (0%)", task_id_clone);
                } else if i % 20 == 0 {
                    log_info!("任务 [{}] 进度：{}%", task_id_clone, i);
                }
                
                if i == 100 {
                    t.status = "completed".to_string();
                    t.file_path = format!("/tmp/{}", filename_clone);
                    t.completed_at = Some(Local::now().to_rfc3339());
                    log_info!("任务 [{}] 完成，文件路径：{}", task_id_clone, t.file_path);
                    
                    // 记录完成事件
                    let mut history = state_clone.task_history.lock().unwrap();
                    if let Some(events) = history.get_mut(&task_id_clone) {
                        events.push(TaskEvent {
                            timestamp: Local::now().to_rfc3339(),
                            event: "completed".to_string(),
                            details: format!("File downloaded to: {}", t.file_path),
                        });
                    }
                }
            }
        }
    });
    
    let elapsed = Local::now().signed_duration_since(start_time).num_milliseconds();
    log_info!("任务创建完成，耗时：{} ms", elapsed);
    
    Json(json!({
        "task_id": task_id,
        "status": "started",
        "filename": filename,
        "url": params.url,
        "created_at": start_time.to_rfc3339(),
        "processing_time_ms": elapsed
    }))
}

// 获取下载任务状态 - 详细日志版本
async fn get_download_status(
    Path(task_id): Path<String>,
    state: Arc<AppState>,
) -> impl IntoResponse {
    log_debug!("查询任务状态：{}", task_id);
    
    let tasks = state.download_tasks.lock().unwrap();
    
    if let Some(task) = tasks.iter().find(|t| t.id == task_id) {
        let history = state.task_history.lock().unwrap();
        let events = history.get(&task_id).map(|h| h.clone()).unwrap_or_default();
        
        log_info!("任务 [{}] 状态：{} ({}%)", task_id, task.status, task.progress);
        
        Json(json!({
            "task_id": task.id,
            "status": task.status,
            "progress": task.progress,
            "file_path": task.file_path,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "history": events.iter().map(|e| json!({
                "timestamp": e.timestamp,
                "event": e.event,
                "details": e.details
            })).collect::<Vec<_>>()
        }))
    } else {
        log_error!("任务不存在：{}", task_id);
        (StatusCode::NOT_FOUND, "Task not found").into_response()
    }
}

// SSE 进度更新 - 详细日志版本
async fn sse_progress() -> impl IntoResponse {
    log_info!("=== 开始 SSE 进度推送 ===");
    
    let stream = stream::unfold(0, |count| async move {
        if count > 100 {
            log_info!("SSE 推送完成");
            return None;
        }
        
        tokio::time::sleep(Duration::from_millis(100)).await;
        
        let event = format!("data: {{\"progress\": {}}}\n\n", count);
        
        if count % 20 == 0 {
            log_info!("SSE 推送进度：{}%", count);
        }
        
        Some((event, count + 10))
    });
    
    let mut headers = HeaderMap::new();
    headers.insert(
        "Content-Type",
        HeaderValue::from_static("text/event-stream"),
    );
    headers.insert(
        "Cache-Control",
        HeaderValue::from_static("no-cache"),
    );
    headers.insert(
        "Connection",
        HeaderValue::from_static("keep-alive"),
    );
    
    log_info!("SSE 流已建立");
    
    (headers, axum::body::StreamBody::new(stream))
}

// 获取状态 - 详细日志版本
async fn get_status(state: Arc<AppState>) -> impl IntoResponse {
    log_debug!("获取系统状态");
    
    let uploaded_files = state.uploaded_files.lock().unwrap().clone();
    let tasks = state.download_tasks.lock().unwrap().clone();
    
    let active_tasks = tasks.iter().filter(|t| t.status != "completed").count();
    let completed_tasks = tasks.iter().filter(|t| t.status == "completed").count();
    
    log_info!("系统状态：{} 个上传文件，{} 个活跃任务，{} 个完成任务",
        uploaded_files.len(), active_tasks, completed_tasks);
    
    Json(json!({
        "uploaded_files": uploaded_files,
        "uploaded_count": uploaded_files.len(),
        "active_tasks": active_tasks,
        "completed_tasks": completed_tasks,
        "total_tasks": tasks.len(),
        "tasks": tasks.into_iter().map(|t| json!({
            "id": t.id,
            "status": t.status,
            "progress": t.progress,
            "started_at": t.started_at,
            "completed_at": t.completed_at
        })).collect::<Vec<_>>()
    }))
}
