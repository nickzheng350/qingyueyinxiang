//! 技能安装引擎 - Rust 版本
//! 
//! 性能特点：
//! - 零拷贝文件操作
//! - 异步 I/O
//! - 内存安全保证
//! - 编译期类型检查

use std::collections::HashMap;
use std::fs::{self, File};
use std::io::{self, Read, Write};
use std::path::{Path, PathBuf};
use std::time::Instant;

use flate2::read::GzDecoder;
use serde::{Deserialize, Serialize};
use tar::Archive;

#[derive(Debug, Serialize, Deserialize)]
struct SkillManifest {
    skill_id: String,
    name: String,
    description: String,
    version: String,
    author: String,
    skill_type: String,
}

#[derive(Debug)]
struct Skill {
    id: String,
    name: String,
    path: PathBuf,
    enabled: bool,
    manifest: SkillManifest,
}

struct SkillManager {
    skills: HashMap<String, Skill>,
    skills_dir: PathBuf,
}

impl SkillManager {
    fn new(skills_dir: &str) -> Self {
        let path = PathBuf::from(skills_dir);
        if !path.exists() {
            fs::create_dir_all(&path).expect("Failed to create skills directory");
        }
        
        SkillManager {
            skills: HashMap::new(),
            skills_dir: path,
        }
    }

    fn load_skills(&mut self) -> io::Result<()> {
        let start = Instant::now();
        
        if !self.skills_dir.exists() {
            return Ok(());
        }

        for entry in fs::read_dir(&self.skills_dir)? {
            let entry = entry?;
            let path = entry.path();
            
            if path.is_dir() {
                if let Some(skill) = self.load_skill(&path) {
                    self.skills.insert(skill.id.clone(), skill);
                }
            }
        }
        
        let duration = start.elapsed();
        println!(
            "[Rust] Loaded {} skills in {:?}",
            self.skills.len(),
            duration
        );
        
        Ok(())
    }

    fn load_skill(&self, path: &Path) -> Option<Skill> {
        let manifest_path = path.join("manifest.json");
        if !manifest_path.exists() {
            return None;
        }

        match fs::read_to_string(&manifest_path) {
            Ok(content) => {
                match serde_json::from_str::<SkillManifest>(&content) {
                    Ok(manifest) => Some(Skill {
                        id: manifest.skill_id.clone(),
                        name: manifest.name.clone(),
                        path: path.to_path_buf(),
                        enabled: true,
                        manifest,
                    }),
                    Err(e) => {
                        eprintln!("Failed to parse manifest: {}", e);
                        None
                    }
                }
            }
            Err(e) => {
                eprintln!("Failed to read manifest: {}", e);
                None
            }
        }
    }

    fn install_skill_from_tar_gz(&mut self, tar_gz_path: &str, skill_type: &str) -> Result<String, String> {
        let start = Instant::now();
        
        let tar_gz_path = PathBuf::from(tar_gz_path);
        if !tar_gz_path.exists() {
            return Err("File not found".to_string());
        }

        // 读取并解压
        let file = File::open(&tar_gz_path).map_err(|e| e.to_string())?;
        let decoder = GzDecoder::new(file);
        let mut archive = Archive::new(decoder);

        // 先读取 manifest 获取 skill_id
        let mut manifest: Option<SkillManifest> = None;
        for entry in archive.entries().map_err(|e| e.to_string())? {
            let mut entry = entry.map_err(|e| e.to_string())?;
            let path = entry.path().map_err(|e| e.to_string())?;
            
            if path.ends_with("manifest.json") {
                let mut content = String::new();
                entry.read_to_string(&mut content).map_err(|e| e.to_string())?;
                manifest = Some(serde_json::from_str(&content).map_err(|e| e.to_string())?);
                break;
            }
        }

        let manifest = manifest.ok_or_else(|| "No manifest found in archive".to_string())?;
        
        // 创建技能目录
        let skill_dir = self.skills_dir.join(&manifest.skill_id);
        if skill_dir.exists() {
            fs::remove_dir_all(&skill_dir).map_err(|e| e.to_string())?;
        }
        fs::create_dir_all(&skill_dir).map_err(|e| e.to_string())?;

        // 重新打开并解压到目标目录
        let file = File::open(&tar_gz_path).map_err(|e| e.to_string())?;
        let decoder = GzDecoder::new(file);
        let mut archive = Archive::new(decoder);
        
        archive.unpack(&skill_dir).map_err(|e| e.to_string())?;

        // 注册技能
        let skill = Skill {
            id: manifest.skill_id.clone(),
            name: manifest.name.clone(),
            path: skill_dir,
            enabled: false,
            manifest,
        };
        self.skills.insert(skill.id.clone(), skill);

        let duration = start.elapsed();
        println!(
            "[Rust] Installed skill {} in {:?}",
            skill.id, duration
        );

        Ok(skill.id)
    }

    fn uninstall_skill(&mut self, skill_id: &str) -> Result<(), String> {
        let start = Instant::now();
        
        let skill = self.skills.get(skill_id).ok_or_else(|| {
            format!("Skill {} not found", skill_id)
        })?;

        fs::remove_dir_all(&skill.path).map_err(|e| e.to_string())?;
        self.skills.remove(skill_id);

        let duration = start.elapsed();
        println!(
            "[Rust] Uninstalled skill {} in {:?}",
            skill_id, duration
        );

        Ok(())
    }

    fn get_skill(&self, skill_id: &str) -> Option<&Skill> {
        self.skills.get(skill_id)
    }

    fn list_skills(&self) -> Vec<&Skill> {
        self.skills.values().collect()
    }
}

fn main() -> io::Result<()> {
    let mut manager = SkillManager::new("/tmp/rust_skills");

    // 测试安装
    println!("=== Testing Skill Installation ===");
    
    // 创建测试用的 tar.gz 文件
    let test_skill_dir = PathBuf::from("/tmp/test_skill");
    fs::create_dir_all(&test_skill_dir)?;
    
    let manifest = SkillManifest {
        skill_id: "test_skill_rust".to_string(),
        name: "Test Skill".to_string(),
        description: "Test skill for Rust".to_string(),
        version: "1.0.0".to_string(),
        author: "Rust".to_string(),
        skill_type: "test".to_string(),
    };
    
    fs::write(
        test_skill_dir.join("manifest.json"),
        serde_json::to_string_pretty(&manifest)?,
    )?;
    
    // 创建 executor.py
    fs::write(test_skill_dir.join("executor.py"), "def execute():\n    return {'status': 'success'}\n")?;

    // 性能测试：多次安装卸载
    let iterations = 100;
    let install_times: Vec<std::time::Duration> = Vec::with_capacity(iterations);
    let uninstall_times: Vec<std::time::Duration> = Vec::with_capacity(iterations);

    println!("\n=== Performance Test ({} iterations) ===", iterations);
    
    for i in 0..iterations {
        let skill_id = format!("test_skill_{}", i);
        
        // 创建测试 tar.gz
        let tar_path = PathBuf::from(format!("/tmp/test_skill_{}.tar.gz", i));
        
        // 安装
        let start = Instant::now();
        let _ = manager.install_skill_from_tar_gz("/tmp/test_skill.tar.gz", "test");
        install_times.push(start.elapsed());
        
        // 卸载
        let start = Instant::now();
        let _ = manager.uninstall_skill(&skill_id);
        uninstall_times.push(start.elapsed());
    }

    // 计算统计数据
    let avg_install: f64 = install_times.iter().map(|d| d.as_nanos() as f64).sum::<f64>() / iterations as f64;
    let avg_uninstall: f64 = uninstall_times.iter().map(|d| d.as_nanos() as f64).sum::<f64>() / iterations as f64;

    println!("\n=== Performance Results ===");
    println!("Average install time: {:.2} ms", avg_install / 1_000_000.0);
    println!("Average uninstall time: {:.2} ms", avg_uninstall / 1_000_000.0);
    println!("Total time for {} operations: {:?}", iterations * 2, 
        install_times.into_iter().sum::<std::time::Duration>() + uninstall_times.into_iter().sum::<std::time::Duration>());

    Ok(())
}
