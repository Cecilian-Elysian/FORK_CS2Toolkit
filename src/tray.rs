use tray_icon::{
    Icon, TrayIcon, TrayIconBuilder,
    menu::{Menu, MenuEvent, MenuId, MenuItem},
};

const ICON_SIZE: usize = 32;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TrayAction {
    Toggle,
    Show,
    Quit,
}

pub struct Tray {
    _icon: TrayIcon,
    toggle: MenuId,
    show: MenuId,
    quit: MenuId,
}

impl Tray {
    pub fn new() -> Result<Self, String> {
        let menu = Menu::new();
        let toggle = MenuItem::new("Pause switching", true, None);
        let show = MenuItem::new("Show window", true, None);
        let quit = MenuItem::new("Exit", true, None);
        menu.append(&toggle).map_err(|error| error.to_string())?;
        menu.append(&show).map_err(|error| error.to_string())?;
        menu.append(&quit).map_err(|error| error.to_string())?;
        let icon = Icon::from_rgba(gradient_rgba(), ICON_SIZE as u32, ICON_SIZE as u32)
            .map_err(|error| error.to_string())?;
        let tray = TrayIconBuilder::new()
            .with_tooltip("CS2 Death Switch")
            .with_menu(Box::new(menu))
            .with_icon(icon)
            .build()
            .map_err(|error| error.to_string())?;
        Ok(Self {
            _icon: tray,
            toggle: toggle.id().clone(),
            show: show.id().clone(),
            quit: quit.id().clone(),
        })
    }

    pub fn poll(&self) -> Option<TrayAction> {
        let event = MenuEvent::receiver().try_recv().ok()?;
        if event.id == self.toggle {
            Some(TrayAction::Toggle)
        } else if event.id == self.show {
            Some(TrayAction::Show)
        } else if event.id == self.quit {
            Some(TrayAction::Quit)
        } else {
            None
        }
    }
}

fn gradient_rgba() -> Vec<u8> {
    let mut buffer = Vec::with_capacity(ICON_SIZE * ICON_SIZE * 4);
    for y in 0..ICON_SIZE {
        for x in 0..ICON_SIZE {
            let center = (ICON_SIZE as f32 - 1.0) / 2.0;
            let distance = ((x as f32 - center).powi(2) + (y as f32 - center).powi(2)).sqrt();
            let radius = center;
            let t = (1.0 - (distance / radius).clamp(0.0, 1.0)).powf(1.2);
            buffer.push((46.0 + (210.0 - 46.0) * t) as u8);
            buffer.push((120.0 + (90.0 - 120.0) * t) as u8);
            buffer.push((220.0 * t) as u8);
            buffer.push(255);
        }
    }
    buffer
}
