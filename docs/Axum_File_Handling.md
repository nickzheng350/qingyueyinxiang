# Axum 文件处理完整示例

## 目录

1. [文件上传处理](#文件上传处理)
2. [异步下载任务](#异步下载任务)
3. [流式响应](#流式响应)
4. [完整路由示例](#完整路由示例)
5. [与 FastAPI 对比](#与-fastapi-对比)

---

## 文件上传处理

### Axum 文件上传

```rust
use axum::{
    extract::Multipart,
    http::{StatusCode, HeaderMap},
    routing::post,
    Json, Router,
};
use futures_util::StreamExt;
use std::{fs::File, io::Write, path::PathBuf};

// 单文件上传
async fn upload_file(mut multipart: Multipart) -> impl IntoResponse {
    while let Some(field) = multipart.next_field().await.unwrap() {
        let name = field.name().unwrap().to_string();
        let filename = field.file_name().unwrap().to_string();
        let data = field.bytes().await.unwrap();
        
        // 保存文件
        let mut file = File::create(&filename).unwrap();
        file.write_all(&data).unwrap();
        
        return Json(json!({
            "status": "success",
            "field": name,
            "filename": filename,
            "size": data.len()
        }));
    }
    
    (StatusCode::BAD_REQUEST, "No file uploaded").into_response()
}

// 多文件上传
async fn upload_multiple_files(mut multipart: Multipart) -> impl IntoResponse {
    let mut uploaded_files = Vec::new();
    
    while let Some(field) = multipart.next_field().await.unwrap() {
        let name = field.name().unwrap().to_string();
        let filename = field.file_name().unwrap().to_string();
        let data = field.bytes().await.unwrap();
        
        // 保存文件
        let mut file = File::create(&filename).unwrap();
        file.write_all(&data).unwrap();
        
        uploaded_files.push(json!({
            "field": name,
            "filename": filename,
            "size": data.len()
        }));
    }
    
    Json(json!({
        "status": "success",
        "files": uploaded_files
    }))
}

// 带进度的文件上传
async fn upload_with_progress(mut multipart: Multipart) -> impl IntoResponse {
    while let Some(mut field) = multipart.next_field().await.unwrap() {
        let filename = field.file_name().unwrap().to_string();
        let mut file = File::create(&filename).unwrap();
        let mut total_bytes = 0u64;
        
        while let Some(chunk) = field.chunk().await.unwrap() {
            total_bytes += chunk.len() as u64;
            file.write_all(&chunk).unwrap();
            
            // 打印进度（生产环境可发送 WebSocket 更新）
            println!("Uploaded: {} bytes", total_bytes);
        }
        
        return Json(json!({
            "status": "success",
            "filename": filename,
            "size": total_bytes
        }));
    }
    
    (StatusCode::BAD_REQUEST, "No file uploaded").into_response()
}
```

---

## 异步下载任务

### Axum 异步文件下载

```rust
use axum::{
    http::{Response, StatusCode, HeaderValue},
    routing::get,
    Router,
};
use futures_util::StreamExt;
use tokio::{fs::File, io::AsyncReadExt};
use tokio_util::io::ReaderStream;

// 简单文件下载
async fn download_file(Path(filename): Path<String>) -> Result<impl IntoResponse, StatusCode> {
    let path = PathBuf::from(&filename);
    
    // 检查文件是否存在
    if !path.exists() {
        return Err(StatusCode::NOT_FOUND);
    }
    
    // 读取文件内容
    let mut file = File::open(&path).await.map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    let mut contents = Vec::new();
    file.read_to_end(&mut contents).await.map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    // 设置响应头
    let mut headers = HeaderMap::new();
    headers.insert(
        "Content-Disposition",
        HeaderValue::from_str(&format!("attachment; filename={}", filename)).unwrap(),
    );
    headers.insert(
        "Content-Type",
        HeaderValue::from_static("application/octet-stream"),
    );
    
    Ok((StatusCode::OK, headers, contents))
}

// 流式文件下载（大文件）
async fn download_large_file(Path(filename): Path<String>) -> Result<impl IntoResponse, StatusCode> {
    let path = PathBuf::from(&filename);
    
    if !path.exists() {
        return Err(StatusCode::NOT_FOUND);
    }
    
    // 创建文件流
    let file = File::open(&path).await.map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    let stream = ReaderStream::new(file);
    
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
    
    Ok(Response::new(axum::body::StreamBody::new(stream)))
}

// 异步任务下载（返回任务ID，后台处理）
use std::sync::{Arc, Mutex};

struct DownloadTask {
    id: String,
    status: String,
    progress: u32,
    file_path: String,
}

struct AppState {
    tasks: Mutex<Vec<DownloadTask>>,
}

async fn create_download_task(
    Path(url): Path<String>,
    state: Arc<AppState>,
) -> impl IntoResponse {
    let task_id = uuid::Uuid::new_v4().to_string();
    
    // 创建任务记录
    let task = DownloadTask {
        id: task_id.clone(),
        status: "pending".to_string(),
        progress: 0,
        file_path: "".to_string(),
    };
    
    state.tasks.lock().unwrap().push(task);
    
    // 启动异步下载任务
    tokio::spawn(async move {
        // 模拟下载过程
        for i in 0..=100 {
            tokio::time::sleep(Duration::from_millis(50)).await;
            
            // 更新进度
            let mut tasks = state.tasks.lock().unwrap();
            if let Some(t) = tasks.iter_mut().find(|t| t.id == task_id) {
                t.progress = i;
                t.status = if i == 100 { "completed".to_string() } else { "downloading".to_string() };
                if i == 100 {
                    t.file_path = format!("/tmp/downloaded_{}.zip", task_id);
                }
            }
        }
    });
    
    Json(json!({
        "task_id": task_id,
        "status": "started"
    }))
}

async fn get_download_status(
    Path(task_id): Path<String>,
    state: Arc<AppState>,
) -> impl IntoResponse {
    let tasks = state.tasks.lock().unwrap();
    
    if let Some(task) = tasks.iter().find(|t| t.id == task_id) {
        Json(json!({
            "task_id": task.id,
            "status": task.status,
            "progress": task.progress,
            "file_path": task.file_path
        }))
    } else {
        (StatusCode::NOT_FOUND, "Task not found").into_response()
    }
}
```

---

## 流式响应

### Server-Sent Events (SSE)

```rust
use axum::{
    http::{StatusCode, HeaderValue},
    routing::get,
    Router,
};
use futures_util::{stream, Stream};
use std::time::Duration;

// SSE 进度更新
async fn sse_progress() -> impl IntoResponse {
    // 创建流式响应
    let stream = stream::unfold(0, |count| async move {
        if count > 100 {
            return None;
        }
        
        tokio::time::sleep(Duration::from_millis(100)).await;
        
        let event = format!("data: {{\"progress\": {}}}\n\n", count);
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
    
    (headers, axum::body::StreamBody::new(stream))
}
```

---

## 完整路由示例

```rust
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
};
use tokio::{fs::File as TokioFile, io::AsyncReadExt};
use tokio_util::io::ReaderStream;
use uuid::Uuid;

// 应用状态
struct AppState {
    download_tasks: Mutex<Vec<DownloadTask>>,
    uploaded_files: Mutex<Vec<String>>,
}

#[derive(Debug, Clone)]
struct DownloadTask {
    id: String,
    status: String,
    progress: u32,
    file_path: String,
}

// 查询参数
#[derive(Deserialize)]
struct DownloadQuery {
    url: String,
    filename: Option<String>,
}

#[tokio::main]
async fn main() {
    let app_state = Arc::new(AppState {
        download_tasks: Mutex::new(Vec::new()),
        uploaded_files: Mutex::new(Vec::new()),
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

    axum::Server::bind(&"0.0.0.0:8000".parse().unwrap())
        .serve(app.into_make_service())
        .await
        .unwrap();
}

// 实现文件上传函数
async fn upload_file(mut multipart: Multipart, state: Arc<AppState>) -> impl IntoResponse {
    while let Some(field) = multipart.next_field().await.unwrap() {
        let filename = field.file_name().unwrap().to_string();
        let data = field.bytes().await.unwrap();
        
        let file_path = PathBuf::from("/tmp").join(&filename);
        let mut file = File::create(&file_path).unwrap();
        file.write_all(&data).unwrap();
        
        state.uploaded_files.lock().unwrap().push(filename.clone());
        
        return Json(json!({
            "status": "success",
            "filename": filename,
            "size": data.len(),
            "path": file_path.to_string_lossy()
        }));
    }
    
    (StatusCode::BAD_REQUEST, "No file uploaded").into_response()
}

async fn upload_multiple_files(mut multipart: Multipart, state: Arc<AppState>) -> impl IntoResponse {
    let mut uploaded_files = Vec::new();
    
    while let Some(field) = multipart.next_field().await.unwrap() {
        let filename = field.file_name().unwrap().to_string();
        let data = field.bytes().await.unwrap();
        
        let file_path = PathBuf::from("/tmp").join(&filename);
        let mut file = File::create(&file_path).unwrap();
        file.write_all(&data).unwrap();
        
        state.uploaded_files.lock().unwrap().push(filename.clone());
        
        uploaded_files.push(json!({
            "filename": filename,
            "size": data.len()
        }));
    }
    
    Json(json!({
        "status": "success",
        "files": uploaded_files
    }))
}

async fn upload_with_progress(mut multipart: Multipart) -> impl IntoResponse {
    while let Some(mut field) = multipart.next_field().await.unwrap() {
        let filename = field.file_name().unwrap().to_string();
        let file_path = PathBuf::from("/tmp").join(&filename);
        let mut file = File::create(&file_path).unwrap();
        let mut total_bytes = 0u64;
        
        while let Some(chunk) = field.chunk().await.unwrap() {
            total_bytes += chunk.len() as u64;
            file.write_all(&chunk).unwrap();
            println!("Upload progress: {} bytes", total_bytes);
        }
        
        return Json(json!({
            "status": "success",
            "filename": filename,
            "size": total_bytes
        }));
    }
    
    (StatusCode::BAD_REQUEST, "No file uploaded").into_response()
}

// 实现下载函数
async fn download_file(Path(filename): Path<String>) -> Result<impl IntoResponse, StatusCode> {
    let path = PathBuf::from("/tmp").join(&filename);
    
    if !path.exists() {
        return Err(StatusCode::NOT_FOUND);
    }
    
    let mut file = TokioFile::open(&path).await.map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    let mut contents = Vec::new();
    file.read_to_end(&mut contents).await.map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    let mut headers = HeaderMap::new();
    headers.insert(
        "Content-Disposition",
        HeaderValue::from_str(&format!("attachment; filename={}", filename)).unwrap(),
    );
    
    Ok((StatusCode::OK, headers, contents))
}

async fn download_large_file(Path(filename): Path<String>) -> Result<impl IntoResponse, StatusCode> {
    let path = PathBuf::from("/tmp").join(&filename);
    
    if !path.exists() {
        return Err(StatusCode::NOT_FOUND);
    }
    
    let file = TokioFile::open(&path).await.map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    let stream = ReaderStream::new(file);
    
    let mut headers = HeaderMap::new();
    headers.insert(
        "Content-Disposition",
        HeaderValue::from_str(&format!("attachment; filename={}", filename)).unwrap(),
    );
    headers.insert(
        "Transfer-Encoding",
        HeaderValue::from_static("chunked"),
    );
    
    Ok(Response::new(axum::body::StreamBody::new(stream)))
}

async fn create_download_task(
    Query(params): Query<DownloadQuery>,
    state: Arc<AppState>,
) -> impl IntoResponse {
    let task_id = Uuid::new_v4().to_string();
    let filename = params.filename.unwrap_or_else(|| "downloaded.zip".to_string());
    
    let task = DownloadTask {
        id: task_id.clone(),
        status: "pending".to_string(),
        progress: 0,
        file_path: "".to_string(),
    };
    
    state.download_tasks.lock().unwrap().push(task);
    
    tokio::spawn(async move {
        for i in 0..=100 {
            tokio::time::sleep(Duration::from_millis(50)).await;
            
            let mut tasks = state.download_tasks.lock().unwrap();
            if let Some(t) = tasks.iter_mut().find(|t| t.id == task_id) {
                t.progress = i;
                t.status = if i == 100 { "completed".to_string() } else { "downloading".to_string() };
                if i == 100 {
                    t.file_path = format!("/tmp/{}", filename);
                }
            }
        }
    });
    
    Json(json!({
        "task_id": task_id,
        "status": "started",
        "filename": filename
    }))
}

async fn get_download_status(
    Path(task_id): Path<String>,
    state: Arc<AppState>,
) -> impl IntoResponse {
    let tasks = state.download_tasks.lock().unwrap();
    
    if let Some(task) = tasks.iter().find(|t| t.id == task_id) {
        Json(json!({
            "task_id": task.id,
            "status": task.status,
            "progress": task.progress,
            "file_path": task.file_path
        }))
    } else {
        (StatusCode::NOT_FOUND, "Task not found").into_response()
    }
}

async fn sse_progress() -> impl IntoResponse {
    let stream = stream::unfold(0, |count| async move {
        if count > 100 {
            return None;
        }
        
        tokio::time::sleep(Duration::from_millis(100)).await;
        
        let event = format!("data: {{\"progress\": {}}}\n\n", count);
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
    
    (headers, axum::body::StreamBody::new(stream))
}

async fn get_status(state: Arc<AppState>) -> impl IntoResponse {
    let uploaded_files = state.uploaded_files.lock().unwrap().clone();
    let tasks = state.download_tasks.lock().unwrap().clone();
    
    Json(json!({
        "uploaded_files": uploaded_files,
        "active_tasks": tasks.len(),
        "tasks": tasks.into_iter().map(|t| json!({
            "id": t.id,
            "status": t.status,
            "progress": t.progress
        })).collect::<Vec<_>>()
    }))
}
```

---

## 与 FastAPI 对比

### 文件上传对比

| 特性 | FastAPI | Axum |
|------|---------|------|
| 单文件 | `UploadFile` | `Multipart` |
| 多文件 | 循环处理 | `StreamExt::next_field` |
| 进度跟踪 | 回调函数 | 手动跟踪 |
| 流式处理 | 内置支持 | 需要手动实现 |

### 文件下载对比

| 特性 | FastAPI | Axum |
|------|---------|------|
| 简单下载 | `FileResponse` | `File::open` + 返回字节 |
| 大文件 | 自动流式 | `ReaderStream` |
| 异步任务 | `BackgroundTasks` | `tokio::spawn` |
| SSE | `EventSourceResponse` | `StreamBody` |

### 性能对比

| 场景 | FastAPI | Axum |
|------|---------|------|
| 小文件上传 | ~10ms | ~5ms |
| 大文件下载 | ~50ms | ~20ms |
| 并发连接 | ~1k | ~10k |
| 内存占用 | 高 | 低 |

---

**文档版本**: v1.0.0  
**更新日期**: 2026年5月