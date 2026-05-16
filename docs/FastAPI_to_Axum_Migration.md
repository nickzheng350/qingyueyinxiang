# FastAPI → Axum 迁移指南

## 目录

1. [核心概念对比](#核心概念对比)
2. [依赖注入对比](#依赖注入对比)
3. [路由定义对比](#路由定义对比)
4. [请求处理对比](#请求处理对比)
5. [响应处理对比](#响应处理对比)
6. [中间件对比](#中间件对比)
7. [完整示例对比](#完整示例对比)
8. [迁移注意事项](#迁移注意事项)

---

## 核心概念对比

| 概念 | FastAPI (Python) | Axum (Rust) |
|------|------------------|-------------|
| 路由定义 | 装饰器 `@app.get()` | 路由宏 `Route::new()` |
| 依赖注入 | 函数参数声明 | `FromRequest` trait |
| 请求体 | `Pydantic` 模型 | `Json<T>` 提取器 |
| 路径参数 | 函数参数 | `Path<T>` 提取器 |
| 查询参数 | 函数参数 | `Query<T>` 提取器 |
| 响应 | `JSONResponse` / 字典 | `Json<T>` / `Response` |
| 错误处理 | 异常类 | `Result<T, E>` |
| 异步 | `async def` | `async fn` |

---

## 依赖注入对比

### FastAPI 依赖注入

```python
from fastapi import Depends, FastAPI

app = FastAPI()

# 定义依赖
async def get_db():
    db = DatabaseConnection()
    try:
        yield db
    finally:
        db.close()

# 使用依赖
@app.get("/items")
async def read_items(db: Database = Depends(get_db)):
    return db.query("SELECT * FROM items")

# 类依赖
class AuthHandler:
    def __init__(self, secret: str):
        self.secret = secret
    
    async def __call__(self, token: str = Header(...)):
        return self.verify_token(token)

auth_handler = AuthHandler(secret="SECRET")

@app.get("/protected")
async def protected(auth: str = Depends(auth_handler)):
    return {"user": auth}
```

### Axum 依赖注入

```rust
use axum::{
    extract::{FromRequest, RequestParts},
    routing::get,
    Router,
};
use std::sync::Arc;

// 定义提取器（依赖注入）
struct Database(pub Arc<DatabaseConnection>);

#[axum::async_trait]
impl<B> FromRequest<B> for Database
where
    B: Send,
{
    type Rejection = StatusCode;

    async fn from_request(req: &mut RequestParts<B>) -> Result<Self, Self::Rejection> {
        let db = req
            .extensions()
            .get::<Arc<DatabaseConnection>>()
            .ok_or(StatusCode::INTERNAL_SERVER_ERROR)?;
        Ok(Self(db.clone()))
    }
}

// 定义状态提取器
struct AuthHandler {
    secret: String,
}

#[axum::async_trait]
impl<B> FromRequest<B> for AuthHandler
where
    B: Send,
{
    type Rejection = StatusCode;

    async fn from_request(req: &mut RequestParts<B>) -> Result<Self, Self::Rejection> {
        let token = req
            .headers()
            .get("Authorization")
            .ok_or(StatusCode::UNAUTHORIZED)?;
        // 验证 token...
        Ok(Self {
            secret: "SECRET".to_string(),
        })
    }
}

// 使用提取器
async fn read_items(Database(db): Database) -> impl IntoResponse {
    let items = db.query("SELECT * FROM items").await;
    Json(items)
}

async fn protected(auth: AuthHandler) -> impl IntoResponse {
    Json(json!({"user": auth.secret}))
}
```

---

## 路由定义对比

### FastAPI 路由

```python
from fastapi import FastAPI, Path, Query

app = FastAPI()

# 基本路由
@app.get("/")
async def root():
    return {"message": "Hello World"}

# 路径参数
@app.get("/items/{item_id}")
async def read_item(item_id: int = Path(..., ge=1)):
    return {"item_id": item_id}

# 查询参数
@app.get("/search")
async def search(q: str = Query(None, max_length=50)):
    return {"q": q}

# 多个路由
@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(user_id: int, item_id: int):
    return {"user_id": user_id, "item_id": item_id}

# 路由分组
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")

@router.get("/items")
async def get_items():
    return []

app.include_router(router)
```

### Axum 路由

```rust
use axum::{
    extract::{Path, Query},
    routing::{get, post},
    Router,
};
use serde::Deserialize;

// 基本路由
let app = Router::new()
    .route("/", get(root));

// 路径参数
async fn read_item(Path(item_id): Path<i32>) -> impl IntoResponse {
    Json(json!({"item_id": item_id}))
}

// 查询参数
#[derive(Deserialize)]
struct SearchParams {
    q: Option<String>,
}

async fn search(Query(params): Query<SearchParams>) -> impl IntoResponse {
    Json(json!({"q": params.q}))
}

// 多个路径参数
async fn read_user_item(Path((user_id, item_id)): Path<(i32, i32)>) -> impl IntoResponse {
    Json(json!({"user_id": user_id, "item_id": item_id}))
}

// 路由分组
let api_router = Router::new()
    .route("/items", get(get_items));

let app = Router::new()
    .nest("/api/v1", api_router);
```

---

## 请求处理对比

### FastAPI 请求处理

```python
from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

# 请求体
class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = None

@app.post("/items")
async def create_item(item: Item):
    return item.dict()

# 表单数据
from fastapi import Form

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    return {"username": username}

# 文件上传
from fastapi import File, UploadFile

@app.post("/files")
async def create_file(file: bytes = File(...)):
    return {"file_size": len(file)}

@app.post("/uploadfile")
async def create_upload_file(file: UploadFile = File(...)):
    return {"filename": file.filename}

# 访问请求对象
@app.get("/request-info")
async def request_info(request: Request):
    return {
        "url": str(request.url),
        "method": request.method,
        "headers": dict(request.headers),
    }
```

### Axum 请求处理

```rust
use axum::{
    extract::{Json, Form, Multipart, Request},
    routing::post,
    Router,
};
use serde::Deserialize;

// 请求体
#[derive(Deserialize)]
struct Item {
    name: String,
    price: f64,
    is_offer: Option<bool>,
}

async fn create_item(Json(item): Json<Item>) -> impl IntoResponse {
    Json(item)
}

// 表单数据
#[derive(Deserialize)]
struct LoginForm {
    username: String,
    password: String,
}

async fn login(Form(form): Form<LoginForm>) -> impl IntoResponse {
    Json(json!({"username": form.username}))
}

// 文件上传
async fn create_file(mut multipart: Multipart) -> impl IntoResponse {
    while let Some(field) = multipart.next_field().await.unwrap() {
        let name = field.name().unwrap().to_string();
        let data = field.bytes().await.unwrap();
        println!("Field {} has {} bytes", name, data.len());
    }
    "OK"
}

// 访问请求对象
async fn request_info(request: Request) -> impl IntoResponse {
    let uri = request.uri().to_string();
    let method = request.method().to_string();
    Json(json!({"url": uri, "method": method}))
}
```

---

## 响应处理对比

### FastAPI 响应

```python
from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse

app = FastAPI()

# 基本响应
@app.get("/")
async def root():
    return {"message": "Hello"}

# 自定义状态码
@app.post("/items", status_code=status.HTTP_201_CREATED)
async def create_item():
    return {"id": 1}

# 自定义响应头
@app.get("/headers")
async def get_headers(response: Response):
    response.headers["X-Custom"] = "value"
    return {"message": "Hello"}

# JSON 响应
@app.get("/json")
async def get_json():
    return JSONResponse(
        content={"message": "Hello"},
        status_code=status.HTTP_200_OK,
    )

# HTML 响应
@app.get("/html")
async def get_html():
    return HTMLResponse(content="<h1>Hello</h1>")

# 文件响应
@app.get("/file")
async def get_file():
    return FileResponse("path/to/file")

# 错误响应
from fastapi import HTTPException

@app.get("/error")
async def get_error():
    raise HTTPException(
        status_code=404,
        detail="Item not found",
    )
```

### Axum 响应

```rust
use axum::{
    http::{Response, StatusCode, HeaderMap, HeaderValue},
    routing::get,
    Json, Router,
};

// 基本响应
async fn root() -> impl IntoResponse {
    Json(json!({"message": "Hello"}))
}

// 自定义状态码
async fn create_item() -> (StatusCode, impl IntoResponse) {
    (StatusCode::CREATED, Json(json!({"id": 1})))
}

// 自定义响应头
async fn get_headers() -> impl IntoResponse {
    let mut headers = HeaderMap::new();
    headers.insert("X-Custom", HeaderValue::from_static("value"));
    (
        StatusCode::OK,
        headers,
        Json(json!({"message": "Hello"})),
    )
}

// JSON 响应
async fn get_json() -> impl IntoResponse {
    Json(json!({"message": "Hello"}))
}

// HTML 响应
async fn get_html() -> impl IntoResponse {
    "<h1>Hello</h1>"
}

// 文件响应
use tokio::fs::File;
use axum::body::StreamBody;
use futures_util::StreamExt;

async fn get_file() -> Result<impl IntoResponse, StatusCode> {
    let file = File::open("path/to/file").await.map_err(|_| StatusCode::NOT_FOUND)?;
    let stream = tokio_util::io::ReaderStream::new(file);
    Ok(StreamBody::new(stream))
}

// 错误响应
use axum::response::IntoResponse;

async fn get_error() -> impl IntoResponse {
    (
        StatusCode::NOT_FOUND,
        Json(json!({"detail": "Item not found"})),
    )
}
```

---

## 中间件对比

### FastAPI 中间件

```python
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

# 自定义中间件
class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print("Before request")
        response = await call_next(request)
        print("After request")
        return response

app.add_middleware(CustomMiddleware)

# 内置中间件
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Axum 中间件

```rust
use axum::{
    http::{Request, Response},
    middleware::{self, Next},
    routing::get,
    Router,
};
use tower_http::{cors::CorsLayer, compression::CompressionLayer};

// 自定义中间件
async fn custom_middleware<B>(
    request: Request<B>,
    next: Next<B>,
) -> Result<Response<axum::body::BoxBody>, axum::Error> {
    println!("Before request");
    let response = next.run(request).await;
    println!("After request");
    Ok(response)
}

// 应用中间件
let app = Router::new()
    .route("/", get(root))
    .layer(middleware::from_fn(custom_middleware))
    .layer(CorsLayer::permissive())
    .layer(CompressionLayer::new());
```

---

## 完整示例对比

### FastAPI 完整示例

```python
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Skill Manager API")

# 数据模型
class Skill(BaseModel):
    id: str
    name: str
    description: str
    enabled: bool = True

# 模拟数据库
skills_db: List[Skill] = []

# 依赖
def get_skill_db() -> List[Skill]:
    return skills_db

# CRUD 操作
@app.get("/skills", response_model=List[Skill])
async def get_skills(db: List[Skill] = Depends(get_skill_db)):
    return db

@app.get("/skills/{skill_id}", response_model=Skill)
async def get_skill(
    skill_id: str,
    db: List[Skill] = Depends(get_skill_db),
):
    skill = next((s for s in db if s.id == skill_id), None)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill

@app.post("/skills", response_model=Skill, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill: Skill,
    db: List[Skill] = Depends(get_skill_db),
):
    db.append(skill)
    return skill

@app.put("/skills/{skill_id}", response_model=Skill)
async def update_skill(
    skill_id: str,
    skill_update: Skill,
    db: List[Skill] = Depends(get_skill_db),
):
    for i, s in enumerate(db):
        if s.id == skill_id:
            db[i] = skill_update
            return skill_update
    raise HTTPException(status_code=404, detail="Skill not found")

@app.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    db: List[Skill] = Depends(get_skill_db),
):
    db[:] = [s for s in db if s.id != skill_id]
```

### Axum 完整示例

```rust
use axum::{
    extract::{Path, Json},
    http::StatusCode,
    routing::{get, post, put, delete},
    Router,
};
use serde::{Deserialize, Serialize};
use std::sync::{Arc, Mutex};

// 数据模型
#[derive(Debug, Serialize, Deserialize, Clone)]
struct Skill {
    id: String,
    name: String,
    description: String,
    enabled: bool,
}

// 共享状态
struct AppState {
    skills: Mutex<Vec<Skill>>,
}

// CRUD 操作
async fn get_skills(state: Arc<AppState>) -> impl IntoResponse {
    let skills = state.skills.lock().unwrap();
    Json(skills.clone())
}

async fn get_skill(
    Path(skill_id): Path<String>,
    state: Arc<AppState>,
) -> impl IntoResponse {
    let skills = state.skills.lock().unwrap();
    match skills.iter().find(|s| s.id == skill_id) {
        Some(skill) => Json(skill.clone()),
        None => (StatusCode::NOT_FOUND, "Skill not found").into_response(),
    }
}

async fn create_skill(
    Json(skill): Json<Skill>,
    state: Arc<AppState>,
) -> impl IntoResponse {
    let mut skills = state.skills.lock().unwrap();
    skills.push(skill.clone());
    (StatusCode::CREATED, Json(skill)).into_response()
}

async fn update_skill(
    Path(skill_id): Path<String>,
    Json(skill_update): Json<Skill>,
    state: Arc<AppState>,
) -> impl IntoResponse {
    let mut skills = state.skills.lock().unwrap();
    if let Some(skill) = skills.iter_mut().find(|s| s.id == skill_id) {
        *skill = skill_update.clone();
        Json(skill_update).into_response()
    } else {
        (StatusCode::NOT_FOUND, "Skill not found").into_response()
    }
}

async fn delete_skill(
    Path(skill_id): Path<String>,
    state: Arc<AppState>,
) -> impl IntoResponse {
    let mut skills = state.skills.lock().unwrap();
    let len_before = skills.len();
    skills.retain(|s| s.id != skill_id);
    if skills.len() < len_before {
        StatusCode::NO_CONTENT.into_response()
    } else {
        (StatusCode::NOT_FOUND, "Skill not found").into_response()
    }
}

#[tokio::main]
async fn main() {
    let app_state = Arc::new(AppState {
        skills: Mutex::new(Vec::new()),
    });

    let app = Router::new()
        .route("/skills", get(get_skills).post(create_skill))
        .route("/skills/:skill_id", get(get_skill).put(update_skill).delete(delete_skill))
        .with_state(app_state);

    axum::Server::bind(&"0.0.0.0:8000".parse().unwrap())
        .serve(app.into_make_service())
        .await
        .unwrap();
}
```

---

## 迁移注意事项

### 类型系统差异

| Python | Rust |
|--------|------|
| 动态类型 | 静态类型 |
| `Optional[T]` | `Option<T>` |
| `List[T]` | `Vec<T>` |
| `Dict[K, V]` | `HashMap<K, V>` |
| 运行时检查 | 编译期检查 |

### 异步模型差异

- **FastAPI**: 基于 `asyncio`，使用 `async def`
- **Axum**: 基于 `tokio`，使用 `async fn`

### 生态系统差异

| 领域 | FastAPI | Axum |
|------|---------|------|
| ORM | SQLAlchemy, Tortoise ORM | Diesel, sqlx |
| 验证 | Pydantic | serde + validator |
| 文档 | 自动生成 | 需要手动配置 |
| 部署 | Uvicorn, Gunicorn | systemd, Docker |

### 性能对比

| 指标 | FastAPI | Axum |
|------|---------|------|
| 吞吐量 | ~10k req/s | ~50k req/s |
| 内存占用 | 较高 | 较低 |
| 启动时间 | 较快 | 较慢（编译时间） |
| 响应延迟 | 中等 | 低 |

---

**文档版本**: v1.0.0  
**更新日期**: 2026年5月