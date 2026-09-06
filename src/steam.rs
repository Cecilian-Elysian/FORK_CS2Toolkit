use std::{
    env, fs, io,
    path::{Path, PathBuf},
};

const CS2_FOLDER: &str = "Counter-Strike Global Offensive";
const VDF_PATH_KEY: &str = "\"path\"";

pub fn is_cs2_root(path: &Path) -> bool {
    path.join("game/bin/win64/cs2.exe").is_file()
}

pub fn detect_cs2() -> Option<PathBuf> {
    let steam = steam_path()?;
    libraries(&steam)
        .into_iter()
        .map(|library| library.join("steamapps/common").join(CS2_FOLDER))
        .find(|path| is_cs2_root(path))
}

pub fn write_gsi_config(cs2_root: &Path, port: u16) -> io::Result<PathBuf> {
    if !is_cs2_root(cs2_root) {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "无效的 CS2 目录",
        ));
    }
    let cfg_dir = cs2_root.join("game/csgo/cfg");
    let cfg_path = cfg_dir.join("gamestate_integration_cs2deathswitch.cfg");
    let config = format!(
        "\"CS2 Death Switch\"\n{{\n    \"uri\" \"http://127.0.0.1:{port}\"\n    \"timeout\" \"1.0\"\n    \"buffer\" \"0.0\"\n    \"throttle\" \"0.0\"\n    \"heartbeat\" \"60.0\"\n    \"data\"\n    {{\n        \"player_id\" \"1\"\n        \"player_state\" \"1\"\n        \"provider\" \"1\"\n        \"round\" \"1\"\n    }}\n}}\n"
    );
    fs::write(&cfg_path, config)?;
    Ok(cfg_path)
}

fn steam_path() -> Option<PathBuf> {
    [
        env::var_os("CS2_DEATH_SWITCH_STEAM")
            .map(PathBuf::from)
            .filter(|path| path.join("steam.exe").is_file()),
        env::var_os("PROGRAMFILES(X86)").map(|base| PathBuf::from(base).join("Steam")),
        env::var_os("PROGRAMFILES").map(|base| PathBuf::from(base).join("Steam")),
        Some(PathBuf::from("C:/Program Files (x86)/Steam")),
        Some(PathBuf::from("C:/Program Files/Steam")),
        Some(PathBuf::from("D:/Steam")),
        Some(PathBuf::from("E:/Steam")),
    ]
    .into_iter()
    .flatten()
    .find(|path| path.join("steam.exe").is_file())
}

fn libraries(steam: &Path) -> Vec<PathBuf> {
    let mut result = vec![steam.to_path_buf()];
    let Ok(vdf) = fs::read_to_string(steam.join("steamapps/libraryfolders.vdf")) else {
        return result;
    };
    for raw in vdf.lines() {
        let line = raw.trim();
        let Some(rest) = line.strip_prefix(VDF_PATH_KEY) else {
            continue;
        };
        let Some(value) = parse_vdf_value(rest.trim()) else {
            continue;
        };
        let normalized = value
            .replace("\\\\", "\\")
            .replace("\\\"", "\"")
            .replace('\\', "/");
        let path = PathBuf::from(expand_env(&normalized));
        if path.is_dir() && !result.iter().any(|existing| existing == &path) {
            result.push(path);
        }
    }
    result
}

fn parse_vdf_value(input: &str) -> Option<String> {
    let trimmed = input.trim();
    if let Some(inner) = trimmed.strip_prefix('"').and_then(|rest| rest.split_once('"')) {
        return Some(inner.0.to_owned());
    }
    if trimmed.starts_with('"') && trimmed.ends_with('"') && trimmed.len() >= 2 {
        return Some(trimmed[1..trimmed.len() - 1].to_owned());
    }
    let token: String = trimmed
        .chars()
        .take_while(|character| !character.is_whitespace())
        .collect();
    if token.is_empty() {
        None
    } else {
        Some(token)
    }
}

fn expand_env(value: &str) -> String {
    let mut result = String::with_capacity(value.len());
    let mut chars = value.chars().peekable();
    while let Some(character) = chars.next() {
        if character == '%' {
            let mut name = String::new();
            while let Some(&next) = chars.peek() {
                if next == '%' {
                    chars.next();
                    break;
                }
                name.push(next);
                chars.next();
            }
            if name.is_empty() {
                result.push('%');
            } else if let Ok(replacement) = env::var(&name) {
                result.push_str(&replacement);
            } else {
                result.push('%');
                result.push_str(&name);
                result.push('%');
            }
        } else {
            result.push(character);
        }
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_double_quoted_path() {
        assert_eq!(
            parse_vdf_value("\"D:\\\\Steam\"").as_deref(),
            Some("D:\\\\Steam")
        );
    }

    #[test]
    fn parses_unquoted_path() {
        assert_eq!(parse_vdf_value("D:/Steam").as_deref(), Some("D:/Steam"));
    }

    #[test]
    fn expands_environment_variables() {
        unsafe {
            env::set_var("CS2DS_TEST_DIR", "X:/Steam");
        }
        assert_eq!(expand_env("%CS2DS_TEST_DIR%/common"), "X:/Steam/common");
        unsafe {
            env::remove_var("CS2DS_TEST_DIR");
        }
    }
}