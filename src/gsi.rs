use crate::detector::GameState;
use std::{
    net::TcpListener,
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
        mpsc::Sender,
    },
    thread,
};
use tiny_http::{Method, Response, Server, StatusCode};

pub fn start(
    port: u16,
    sender: Sender<GameState>,
    running: Arc<AtomicBool>,
) -> Result<thread::JoinHandle<()>, String> {
    let listener = TcpListener::bind(("127.0.0.1", port)).map_err(|error| match error.kind() {
        std::io::ErrorKind::AddrInUse => format!(
            "port {port} is already in use; close the other GSI listener or change the configured port"
        ),
        _ => format!("could not bind 127.0.0.1:{port}: {error}"),
    })?;
    listener
        .set_nonblocking(true)
        .map_err(|error| error.to_string())?;
    let server = Server::from_listener(listener, None).map_err(|error| error.to_string())?;
    Ok(thread::spawn(move || {
        while running.load(Ordering::Relaxed) {
            let Some(mut request) = server
                .recv_timeout(std::time::Duration::from_millis(250))
                .ok()
                .flatten()
            else {
                continue;
            };
            if request.method() != &Method::Post {
                let _ = request.respond(Response::empty(StatusCode(405)));
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
                StatusCode(200)
            } else {
                StatusCode(400)
            };
            let _ = request.respond(Response::empty(status));
        }
    }))
}
