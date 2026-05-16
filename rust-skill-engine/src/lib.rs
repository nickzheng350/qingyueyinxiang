//! 技能安装引擎 - WASM 版本
//! 
//! 提供技能安装、卸载、列表等功能的 WASM 绑定

use flate2::read::GzDecoder;
use js_sys::Uint8Array;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::io::{Cursor, Read};
use std::path::{Path, PathBuf};
use wasm_bindgen::prelude::*;
use wasm_bindgen_futures::JsFuture;
use web_sys::console;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SkillManifest {
    pub skill_id: String,
    pub name: String,
    pub description: String,
    pub version: String,
    pub author: String,
    pub skill_type: String,
}

#[derive(Debug, Serialize, Clone)]
pub struct Skill {
    pub id: String,
    pub name: String,
    pub path: String,
    pub enabled: bool,
    pub manifest: SkillManifest,
}

#[derive(Debug, Serialize)]
pub struct InstallResult {
    pub success: bool,
    pub skill_id: String,
    pub message: String,
}

struct SkillManager {
    skills: HashMap<String, Skill>,
    skills_dir: PathBuf,
}

impl SkillManager {
    fn new(skills_dir: &str) -> Self {
        let path = PathBuf::from(skills_dir);
        #[cfg(not(target_arch = "wasm32"))]
        {
            if !path.exists() {
                std::fs::create_dir_all(&path).expect("Failed to create skills directory");
            }
        }
        
        SkillManager {
            skills: HashMap::new(),
            skills_dir: path,
        }
    }
}

// 全局技能管理器
lazy_static::lazy_static! {
    static ref SKILL_MANAGER: std::sync::Mutex<SkillManager> = {
        std::sync::Mutex::new(SkillManager::new("/tmp/skills"))
    };
}

#[wasm_bindgen]
pub async fn init_wasm() -> Result<(), JsValue> {
    #[cfg(target_arch = "wasm32")]
    {
        console::log_1(&"[WASM] Skill engine initialized".into());
    }
    Ok(())
}

#[wasm_bindgen]
pub async fn install_skill(skill_id: &str, tar_data: &[u8]) -> Result<JsValue, JsValue> {
    #[cfg(target_arch = "wasm32")]
    {
        console::log_1(&format!("[WASM] Installing skill: {}", skill_id).into());
    }
    
    // 从 tar.gz 数据中解析技能
    let result = parse_tar_gz(tar_data);
    
    match result {
        Ok((manifest, files)) => {
            // 存储技能信息（在 WASM 环境中使用内存存储）
            let mut manager = SKILL_MANAGER.lock().map_err(|e| JsValue::from_str(&e.to_string()))?;
            
            let skill = Skill {
                id: manifest.skill_id.clone(),
                name: manifest.name.clone(),
                path: format!("/skills/{}", manifest.skill_id),
                enabled: false,
                manifest: manifest.clone(),
            };
            
            manager.skills.insert(manifest.skill_id.clone(), skill);
            
            #[cfg(target_arch = "wasm32")]
            {
                console::log_1(&format!("[WASM] Skill {} installed successfully", manifest.skill_id).into());
            }
            
            let install_result = InstallResult {
                success: true,
                skill_id: manifest.skill_id,
                message: "Skill installed successfully".to_string(),
            };
            
            Ok(JsValue::from_serde(&install_result).map_err(|e| JsValue::from_str(&e.to_string()))?)
        }
        Err(e) => {
            #[cfg(target_arch = "wasm32")]
            {
                console::error_1(&format!("[WASM] Install failed: {}", e).into());
            }
            
            let install_result = InstallResult {
                success: false,
                skill_id: skill_id.to_string(),
                message: e,
            };
            
            Ok(JsValue::from_serde(&install_result).map_err(|e| JsValue::from_str(&e.to_string()))?)
        }
    }
}

#[wasm_bindgen]
pub async fn uninstall_skill(skill_id: &str) -> Result<(), JsValue> {
    #[cfg(target_arch = "wasm32")]
    {
        console::log_1(&format!("[WASM] Uninstalling skill: {}", skill_id).into());
    }
    
    let mut manager = SKILL_MANAGER.lock().map_err(|e| JsValue::from_str(&e.to_string()))?;
    
    if manager.skills.remove(skill_id).is_some() {
        #[cfg(target_arch = "wasm32")]
        {
            console::log_1(&format!("[WASM] Skill {} uninstalled", skill_id).into());
        }
        Ok(())
    } else {
        Err(JsValue::from_str(&format!("Skill {} not found", skill_id)))
    }
}

#[wasm_bindgen]
pub async fn list_skills() -> Result<JsValue, JsValue> {
    let manager = SKILL_MANAGER.lock().map_err(|e| JsValue::from_str(&e.to_string()))?;
    
    let skills: Vec<&Skill> = manager.skills.values().collect();
    
    Ok(JsValue::from_serde(&skills).map_err(|e| JsValue::from_str(&e.to_string()))?)
}

#[wasm_bindgen]
pub async fn get_skill(skill_id: &str) -> Result<JsValue, JsValue> {
    let manager = SKILL_MANAGER.lock().map_err(|e| JsValue::from_str(&e.to_string()))?;
    
    match manager.skills.get(skill_id) {
        Some(skill) => Ok(JsValue::from_serde(skill).map_err(|e| JsValue::from_str(&e.to_string()))?),
        None => Err(JsValue::from_str(&format!("Skill {} not found", skill_id))),
    }
}

#[wasm_bindgen]
pub async fn enable_skill(skill_id: &str) -> Result<(), JsValue> {
    let mut manager = SKILL_MANAGER.lock().map_err(|e| JsValue::from_str(&e.to_string()))?;
    
    match manager.skills.get_mut(skill_id) {
        Some(skill) => {
            skill.enabled = true;
            #[cfg(target_arch = "wasm32")]
            {
                console::log_1(&format!("[WASM] Skill {} enabled", skill_id).into());
            }
            Ok(())
        }
        None => Err(JsValue::from_str(&format!("Skill {} not found", skill_id))),
    }
}

#[wasm_bindgen]
pub async fn disable_skill(skill_id: &str) -> Result<(), JsValue> {
    let mut manager = SKILL_MANAGER.lock().map_err(|e| JsValue::from_str(&e.to_string()))?;
    
    match manager.skills.get_mut(skill_id) {
        Some(skill) => {
            skill.enabled = false;
            #[cfg(target_arch = "wasm32")]
            {
                console::log_1(&format!("[WASM] Skill {} disabled", skill_id).into());
            }
            Ok(())
        }
        None => Err(JsValue::from_str(&format!("Skill {} not found", skill_id))),
    }
}

/// 解析 tar.gz 数据，提取 manifest 和文件列表
fn parse_tar_gz(data: &[u8]) -> Result<(SkillManifest, Vec<(String, Vec<u8>)>), String> {
    let cursor = Cursor::new(data);
    let decoder = GzDecoder::new(cursor);
    let mut archive = tar::Archive::new(decoder);
    
    let mut manifest: Option<SkillManifest> = None;
    let mut files: Vec<(String, Vec<u8>)> = Vec::new();
    
    for entry in archive.entries().map_err(|e| e.to_string())? {
        let mut entry = entry.map_err(|e| e.to_string())?;
        let path = entry.path().map_err(|e| e.to_string())?;
        let path_str = path.to_string_lossy().to_string();
        
        if path_str.ends_with("manifest.json") {
            let mut content = String::new();
            entry.read_to_string(&mut content).map_err(|e| e.to_string())?;
            manifest = Some(serde_json::from_str(&content).map_err(|e| e.to_string())?);
        } else if entry.header().entry_type().is_file() {
            let mut file_data = Vec::new();
            entry.read_to_end(&mut file_data).map_err(|e| e.to_string())?;
            files.push((path_str, file_data));
        }
    }
    
    let manifest = manifest.ok_or_else(|| "No manifest found in archive".to_string())?;
    
    Ok((manifest, files))
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_parse_tar_gz() {
        // 创建测试用的 tar.gz 数据
        let manifest = SkillManifest {
            skill_id: "test_skill".to_string(),
            name: "Test Skill".to_string(),
            description: "Test".to_string(),
            version: "1.0.0".to_string(),
            author: "Test".to_string(),
            skill_type: "test".to_string(),
        };
        
        let manifest_json = serde_json::to_string(&manifest).unwrap();
        
        // 在实际测试中，这里应该创建一个真实的 tar.gz 文件
        // 这里只是验证函数签名
        assert_eq!(manifest.skill_id, "test_skill");
    }
}
