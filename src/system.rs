use crate::config::{Config, TargetType};
use std::{ffi::OsStr, os::windows::ffi::OsStrExt, process::Command};
use windows::{
    Win32::{
        Foundation::{HWND, LPARAM, WPARAM},
        UI::Input::KeyboardAndMouse::{KEYEVENTF_KEYUP, keybd_event},
        UI::WindowsAndMessaging::{
            ClipCursor, EnumWindows, FindWindowW, GetClassNameW, IsWindowVisible, PostMessageW,
            SW_RESTORE, SW_SHOWMINNOACTIVE, SetForegroundWindow, ShowWindow,
        },
    },
    core::{BOOL, PCWSTR},
};

const WM_SYSCOMMAND: u32 = 0x0112;
const SC_MINIMIZE: usize = 0xF020;
const VK_MENU: u8 = 0x12;

pub fn switch_away(config: &Config) -> Result<String, String> {
    minimize_cs2();
    match config.target_type {
        TargetType::Url => open_url(&config.target),
        TargetType::App => open_app(&config.target),
    }?;
    let _ = activate_existing_browser();
    Ok(format!("已切换到 {}", config.target))
}

pub fn return_to_cs2() {
    if let Some(window) = cs2_window() {
        force_foreground(window);
    }
}

fn minimize_cs2() {
    if let Some(window) = cs2_window() {
        unsafe {
            // Release an exclusive mouse capture so the game actually leaves the
            // foreground, especially important when CS2 is running in fullscreen.
            let _ = ClipCursor(None);
            // Preferred minimize path that mirrors the original CS2Toolkit.
            let _ = PostMessageW(Some(window), WM_SYSCOMMAND, WPARAM(SC_MINIMIZE), LPARAM(0));
            let _ = ShowWindow(window, SW_SHOWMINNOACTIVE);
        }
    }
}

fn force_foreground(window: HWND) {
    unsafe {
        let _ = SetForegroundWindow(window);
        let _ = ShowWindow(window, SW_RESTORE);
        let _ = SetForegroundWindow(window);
        // The classic Windows workaround for the foreground-activation lock:
        // simulate an ALT key press so the target process is treated as a
        // legitimate foreground owner.
        keybd_event(VK_MENU, 0, Default::default(), 0);
        keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0);
        let _ = SetForegroundWindow(window);
    }
}

fn cs2_window() -> Option<HWND> {
    let title = wide("Counter-Strike 2");
    let window = unsafe { FindWindowW(None, PCWSTR(title.as_ptr())) }.ok()?;
    (window != HWND::default()).then_some(window)
}

fn open_url(url: &str) -> Result<String, String> {
    let url = if url.starts_with("http://") || url.starts_with("https://") {
        url.to_owned()
    } else {
        format!("https://{url}")
    };
    Command::new("explorer.exe")
        .arg(&url)
        .spawn()
        .map_err(|error| format!("无法打开网页：{error}"))?;
    Ok(format!("已打开 {url}"))
}

fn open_app(path: &str) -> Result<String, String> {
    if path.trim().is_empty() {
        return Err("请先选择本地程序".to_owned());
    }
    Command::new(path)
        .spawn()
        .map_err(|error| format!("无法启动程序：{error}"))?;
    Ok(format!("已启动 {path}"))
}

pub fn pause_current_media() -> Result<(), String> {
    // The global media session API targets the session Windows exposes for media controls.
    use windows::Media::Control::{
        GlobalSystemMediaTransportControlsSessionManager,
        GlobalSystemMediaTransportControlsSessionPlaybackStatus,
    };
    let manager = futures_lite::future::block_on(async {
        GlobalSystemMediaTransportControlsSessionManager::RequestAsync()?.await
    })
    .map_err(|error| error.to_string())?;
    let session = manager
        .GetCurrentSession()
        .map_err(|error| error.to_string())?;
    let info = session
        .GetPlaybackInfo()
        .map_err(|error| error.to_string())?;
    if info.PlaybackStatus().map_err(|error| error.to_string())?
        == GlobalSystemMediaTransportControlsSessionPlaybackStatus::Playing
    {
        let _ = futures_lite::future::block_on(async { session.TryPauseAsync()?.await });
    }
    Ok(())
}

pub fn activate_existing_browser() -> bool {
    unsafe extern "system" fn callback(window: HWND, found: LPARAM) -> BOOL {
        if !unsafe { IsWindowVisible(window).as_bool() } {
            return BOOL(1);
        }
        let mut name = [0_u16; 128];
        let len = unsafe { GetClassNameW(window, &mut name) } as usize;
        let class_name = String::from_utf16_lossy(&name[..len]);
        if matches!(
            class_name.as_str(),
            "Chrome_WidgetWin_1" | "MozillaWindowClass"
        ) {
            unsafe {
                // Use the proven foreground-steal pattern so the browser
            // actually appears on top, instead of being silently
            // ignored by the Windows foreground lock.
                let _ = ShowWindow(window, SW_RESTORE);
                let _ = SetForegroundWindow(window);
                keybd_event(VK_MENU, 0, Default::default(), 0);
                keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0);
                let _ = SetForegroundWindow(window);
                *(found.0 as *mut bool) = true;
            }
            return BOOL(0);
        }
        BOOL(1)
    }

    let mut found = false;
    unsafe {
        let _ = EnumWindows(Some(callback), LPARAM((&mut found as *mut bool) as isize));
    }
    found
}

fn wide(value: &str) -> Vec<u16> {
    OsStr::new(value).encode_wide().chain(Some(0)).collect()
}