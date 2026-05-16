//! Rust HTTP 客户端 - 调用 Python 模拟服务

use std::collections::HashMap;
use std::time::{Instant, Duration};

#[derive(Debug, serde::Serialize, serde::Deserialize, Clone)]
struct Skill {
    id: String,
    name: String,
    description: String,
    version: String,
    author: String,
    enabled: bool,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct CreateSkillRequest {
    skill: Skill,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct CreateSkillResponse {
    skill: Option<Skill>,
    success: bool,
    message: String,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct GetSkillRequest {
    skill_id: String,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct GetSkillResponse {
    skill: Option<Skill>,
    found: bool,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct InstallSkillRequest {
    skill_id: String,
    skill_type: String,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct InstallSkillResponse {
    success: bool,
    message: String,
    skill: Option<Skill>,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct ListSkillsResponse {
    skills: Vec<Skill>,
}

fn http_post(path: &str, body: &str) -> Result<String, String> {
    let client = ureq::Agent::new();
    let url = format!("http://localhost:50051{}", path);
    
    let response = client.post(&url)
        .set("Content-Type", "application/json")
        .send_string(body)
        .map_err(|e| e.to_string())?;
    
    let status = response.status();
    if status != 200 {
        return Err(format!("HTTP error: {}", status));
    }
    
    response.into_string().map_err(|e| e.to_string())
}

fn main() -> Result<(), String> {
    println!("=== Rust HTTP Client ===");
    println!("Connected to Python server at localhost:50051\n");
    
    // 测试创建技能
    let skill = Skill {
        id: "rust_test_skill".to_string(),
        name: "Rust Test Skill".to_string(),
        description: "Created from Rust client".to_string(),
        version: "1.0.0".to_string(),
        author: "Rust Client".to_string(),
        enabled: true,
    };
    
    let req = CreateSkillRequest { skill: skill.clone() };
    let body = serde_json::to_string(&req).map_err(|e| e.to_string())?;
    
    let start = Instant::now();
    let response = http_post("/CreateSkill", &body)?;
    let duration = start.elapsed();
    
    let resp: CreateSkillResponse = serde_json::from_str(&response).map_err(|e| e.to_string())?;
    println!(
        "[Rust] CreateSkill response: success={}, message={}",
        resp.success, resp.message
    );
    println!("Response time: {:?}\n", duration);
    
    // 测试获取技能
    let req = GetSkillRequest {
        skill_id: "rust_test_skill".to_string(),
    };
    let body = serde_json::to_string(&req).map_err(|e| e.to_string())?;
    
    let start = Instant::now();
    let response = http_post("/GetSkill", &body)?;
    let duration = start.elapsed();
    
    let resp: GetSkillResponse = serde_json::from_str(&response).map_err(|e| e.to_string())?;
    if resp.found {
        if let Some(s) = resp.skill {
            println!(
                "[Rust] GetSkill found: {} ({})",
                s.name, s.id
            );
        }
    } else {
        println!("[Rust] GetSkill: not found");
    }
    println!("Response time: {:?}\n", duration);
    
    // 测试安装技能（性能测试）
    let iterations = 10;
    let mut total_time = Duration::new(0, 0);
    
    println!(
        "[Rust] Starting performance test: {} installations",
        iterations
    );
    
    for i in 0..iterations {
        let skill_id = format!("perf_test_{}", i);
        
        let req = InstallSkillRequest {
            skill_id: skill_id.clone(),
            skill_type: "test".to_string(),
        };
        let body = serde_json::to_string(&req).map_err(|e| e.to_string())?;
        
        let start = Instant::now();
        let response = http_post("/InstallSkill", &body)?;
        let duration = start.elapsed();
        
        let resp: InstallSkillResponse = serde_json::from_str(&response).map_err(|e| e.to_string())?;
        total_time += duration;
        
        println!(
            "  Install {}: {} ({}ms)",
            skill_id,
            resp.success,
            duration.as_millis()
        );
    }
    
    println!("\n[Rust] Performance Results:");
    println!(
        "  Average time per call: {}ms",
        total_time.as_millis() / iterations as u128
    );
    println!(
        "  Total time: {}ms",
        total_time.as_millis()
    );
    
    // 测试列表技能
    let start = Instant::now();
    let response = http_post("/ListSkills", "{}")?;
    let duration = start.elapsed();
    
    let resp: ListSkillsResponse = serde_json::from_str(&response).map_err(|e| e.to_string())?;
    
    println!(
        "\n[Rust] ListSkills found {} skills",
        resp.skills.len()
    );
    for s in resp.skills {
        println!("  - {} ({})", s.name, s.id);
    }
    println!("Response time: {:?}", duration);
    
    println!("\n=== Test completed ===");
    
    Ok(())
}
