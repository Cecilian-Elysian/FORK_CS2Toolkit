#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod app;
mod config;
mod detector;
mod fonts;
mod gsi;
mod instance;
mod steam;
mod system;
mod tray;

fn main() -> eframe::Result<()> {
    if instance::acquire().is_none() {
        // Another instance is already running and its window has been woken.
        // Exit silently so the user is not confused by a second window.
        return Ok(());
    }
    let options = eframe::NativeOptions {
        viewport: eframe::egui::ViewportBuilder::default()
            .with_inner_size([560.0, 430.0])
            .with_min_inner_size([500.0, 390.0])
            .with_title("CS2 死亡切换"),
        ..Default::default()
    };
    eframe::run_native(
        "CS2 Death Switch",
        options,
        Box::new(|creation_context| Ok(Box::new(app::DeathSwitchApp::new(creation_context)))),
    )
}