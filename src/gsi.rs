use crate::detector::GameState;
use std::{
    net::TcpListener,
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
        mpsc::Sender,
    },
    thread::{self, JoinHandle},
};

pub struct ServerHandle {
    pub thread: JoinHandle<()>,
    pub bound_port: u16,
}

pub fn start(
    preferred_port: u16,
    sender: Sender<GameState>,
    running: Arc<AtomicBool>,
) -> Result<ServerHandle, String> {
    let (listener, bound_port) = bind_port(preferred_port)?;
    listener
        .set_nonblocking(true)
        .map_err(|error| error.to_string())?;
    let server = tiny_http::Server::from_listener(listener, None).map_err(|error| error.to_string())?;
    let thread = thread::spawn(move || {
        while running.load(Ordering::Relaxed) {
            let Some(mut request) = server
                .recv_timeout(std::time::Duration::from_millis(250))
                .ok()
                .flatten()
            else {
                continue;
            };
            if request.method() != &tiny_http::Method::Post {
                let _ = request.respond(tiny_http::Response::empty(tiny_http::StatusCode(405)));
                continue;
            }
            let mut body = String::new();
            let result = request
                .as_reader()
                .read_to_string(&mut body)
                .ok()
                .and_then(|_| serde_json::from_str::<GameState>(&body).ok())
                .map(|state| sender.send(state).is_ok())
                .unwrap_or(false);
            let status = if result {
                tiny_http::StatusCode(200)
            } else {
                tiny_http::StatusCode(400)
            };
            let _ = request.respond(tiny_http::Response::empty(status));
        }
    });
    Ok(ServerHandle { thread, bound_port })
}

fn bind_port(preferred: u16) -> Result<(TcpListener, u16), String> {
    // Mirror the original CS2Toolkit: if the preferred port is busy, try a
    // small range before giving up. The caller is expected to surface the
    // mismatch to the user so they regenerate the GSI config to match.
    for offset in 0..=10u16 {
        let port = preferred.saturating_add(offset);
        match TcpListener::bind(("127.0.0.1", port)) {
            Ok(listener) => return Ok((listener, port)),
            Err(error) if error.kind() == std::io::ErrorKind::AddrInUse => continue,
            Err(error) => return Err(format!("无法绑定 127.0.0.1:{port}：{error}")),
        }
    }
    Err(format!(
        "端口 {preferred}–{} 均被占用：请关闭占用程序，或在配置中更换端口",
        preferred.saturating_add(10)
    ))
}