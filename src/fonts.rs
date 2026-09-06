use eframe::egui::{self, FontData, FontDefinitions, FontFamily};
use std::path::PathBuf;

const FALLBACK_FONT_FILES: &[&str] = &[
    "msyh.ttc",
    "msyh.ttf",
    "simhei.ttf",
    "simsun.ttc",
    "Deng.ttf",
];

const FONT_NAME: &str = "system_cjk";

pub fn install(ctx: &egui::Context) -> Option<&'static str> {
    let Some((source, data)) = load_font() else {
        return None;
    };
    let mut fonts = FontDefinitions::default();
    fonts
        .font_data
        .insert(FONT_NAME.to_owned(), FontData::from_owned(data).into());
    for family in [FontFamily::Proportional, FontFamily::Monospace] {
        fonts
            .families
            .entry(family)
            .or_default()
            .push(FONT_NAME.to_owned());
    }
    ctx.set_fonts(fonts);
    Some(source)
}

fn load_font() -> Option<(&'static str, Vec<u8>)> {
    let mut candidates = Vec::new();
    if let Ok(windir) = std::env::var("WINDIR") {
        for file in FALLBACK_FONT_FILES {
            candidates.push((font_label(file), PathBuf::from(&windir).join("Fonts").join(file)));
        }
    }
    candidates
        .into_iter()
        .find_map(|(label, path)| std::fs::read(path).ok().map(|data| (label, data)))
}

fn font_label(file: &str) -> &'static str {
    match file {
        "msyh.ttc" | "msyh.ttf" => "微软雅黑",
        "simhei.ttf" => "黑体",
        "simsun.ttc" => "宋体",
        "Deng.ttf" => "等线",
        _ => "系统字体",
    }
}
