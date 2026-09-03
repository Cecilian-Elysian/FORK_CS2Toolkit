use directories::ProjectDirs;
use serde::{Deserialize, Serialize};
use std::{fs, io, path::PathBuf};

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum TargetType {
    #[default]
    Url,
    App,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(default)]
pub struct Config {
    pub enabled: bool,
    pub cs2_path: String,
    pub gsi_port: u16,
    pub target_type: TargetType,
    pub target: String,
    pub delay_seconds: u8,
    pub pause_media_on_return: bool,
    pub close_to_tray: bool,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            enabled: true,
            cs2_path: String::new(),
            gsi_port: 3000,
            target_type: TargetType::Url,
            target: String::new(),
            delay_seconds: 0,
            pause_media_on_return: true,
            close_to_tray: true,
        }
    }
}

pub fn config_path() -> io::Result<PathBuf> {
    let dirs = ProjectDirs::from("com", "Cecilian-Elysian", "CS2DeathSwitch")
        .ok_or_else(|| io::Error::other("cannot determine local application data directory"))?;
    let dir = dirs.data_local_dir();
    fs::create_dir_all(dir)?;
    Ok(dir.join("config.json"))
}

pub fn load() -> Config {
    let Ok(path) = config_path() else {
        return Config::default();
    };
    fs::read_to_string(path)
        .ok()
        .and_then(|text| serde_json::from_str(&text).ok())
        .unwrap_or_default()
}

pub fn save(config: &Config) -> io::Result<()> {
    let path = config_path()?;
    let text = serde_json::to_string_pretty(config).map_err(io::Error::other)?;
    fs::write(path, text)
}
