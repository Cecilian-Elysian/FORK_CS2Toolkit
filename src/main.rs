mod app;
mod config;
mod detector;
mod gsi;
mod steam;
mod system;
mod tray;

fn main() -> eframe::Result<()> {
    let options = eframe::NativeOptions {
        viewport: eframe::egui::ViewportBuilder::default()
            .with_inner_size([560.0, 430.0])
            .with_min_inner_size([500.0, 390.0])
            .with_title("CS2 Death Switch"),
        ..Default::default()
    };
    eframe::run_native(
        "CS2 Death Switch",
        options,
        Box::new(|creation_context| Ok(Box::new(app::DeathSwitchApp::new(creation_context)))),
    )
}
