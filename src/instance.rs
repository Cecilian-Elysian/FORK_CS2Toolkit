use std::ffi::OsStr;
use std::os::windows::ffi::OsStrExt;
use windows::{
    Win32::{
        Foundation::{GetLastError, ERROR_ALREADY_EXISTS},
        System::Threading::CreateMutexW,
        UI::WindowsAndMessaging::{FindWindowW, SW_RESTORE, SetForegroundWindow, ShowWindow},
    },
    core::PCWSTR,
};
use windows::Win32::Foundation::HANDLE;

const MUTEX_NAME: &str = "Local\\CS2DeathSwitch.singlex";
const WINDOW_TITLE: &str = "CS2 死亡切换";

pub struct SingleInstanceGuard {
    _handle: HANDLE,
}

/// Try to acquire single-instance ownership. Returns `Some(guard)` when this
/// is the only running instance (the caller should proceed normally). When a
/// previous instance already owns the named mutex the existing window is
/// restored and brought to the foreground, then `None` is returned and the
/// caller should exit.
pub fn acquire() -> Option<SingleInstanceGuard> {
    let name = wide(MUTEX_NAME);
    unsafe {
        let handle = CreateMutexW(None, true, PCWSTR(name.as_ptr())).ok()?;
        if GetLastError() == ERROR_ALREADY_EXISTS {
            wake_existing();
            None
        } else {
            Some(SingleInstanceGuard { _handle: handle })
        }
    }
}

fn wake_existing() {
    let title = wide(WINDOW_TITLE);
    unsafe {
        if let Ok(window) = FindWindowW(None, PCWSTR(title.as_ptr())) {
            if window.0 != std::ptr::null_mut() {
                let _ = ShowWindow(window, SW_RESTORE);
                let _ = SetForegroundWindow(window);
            }
        }
    }
}

fn wide(value: &str) -> Vec<u16> {
    OsStr::new(value).encode_wide().chain(Some(0)).collect()
}