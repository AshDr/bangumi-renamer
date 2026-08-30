use std::env;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

use serde_json::Value;
use tauri::{AppHandle, Manager};

const ALLOWED_COMMANDS: &[&str] = &[
    "settings.get",
    "settings.save",
    "settings.test_connection",
    "plan.scan",
    "plan.candidates",
    "plan.rebuild",
    "plan.apply",
];

#[tauri::command]
async fn execute_bridge(app: AppHandle, command: String, payload: Value) -> Result<Value, String> {
    if !ALLOWED_COMMANDS.contains(&command.as_str()) {
        return Err(format!("Unsupported desktop command: {command}"));
    }

    tauri::async_runtime::spawn_blocking(move || run_bridge(&app, &command, &payload))
        .await
        .map_err(|error| format!("Desktop bridge task failed: {error}"))?
}

fn run_bridge(app: &AppHandle, command: &str, payload: &Value) -> Result<Value, String> {
    let project_root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .ok_or_else(|| "Could not resolve the project root.".to_string())?;

    let mut process = bridge_command(app)?;
    process
        .arg(command)
        .current_dir(project_root)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    let mut child = process
        .spawn()
        .map_err(|error| format!("Could not start the Python bridge: {error}"))?;
    let request = serde_json::to_vec(payload)
        .map_err(|error| format!("Could not serialize desktop request: {error}"))?;
    child
        .stdin
        .take()
        .ok_or_else(|| "Python bridge stdin was unavailable.".to_string())?
        .write_all(&request)
        .map_err(|error| format!("Could not write to the Python bridge: {error}"))?;

    let output = child
        .wait_with_output()
        .map_err(|error| format!("Could not read the Python bridge response: {error}"))?;
    if !output.status.success() && output.stdout.is_empty() {
        return Err(format!(
            "Python bridge exited with {}: {}",
            output.status,
            String::from_utf8_lossy(&output.stderr).trim()
        ));
    }
    serde_json::from_slice(&output.stdout).map_err(|error| {
        format!(
            "Python bridge returned invalid JSON: {error}. stderr: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        )
    })
}

fn bridge_command(app: &AppHandle) -> Result<Command, String> {
    if let Ok(configured) = env::var("BANGUMI_RENAMER_BRIDGE_BIN") {
        return Ok(Command::new(configured));
    }

    if cfg!(debug_assertions) {
        let mut command = Command::new("uv");
        command.args(["run", "python", "-m", "bangumi_renamer.desktop_bridge"]);
        return Ok(command);
    }

    let resource_dir = app
        .path()
        .resource_dir()
        .map_err(|error| format!("Could not resolve application resources: {error}"))?;
    let bundled = resource_dir.join(bridge_binary_name());
    if !bundled.is_file() {
        return Err(format!(
            "Bundled Python bridge is missing at {}. Rebuild the desktop package.",
            bundled.display()
        ));
    }
    Ok(Command::new(bundled))
}

fn bridge_binary_name() -> PathBuf {
    if cfg!(target_os = "windows") {
        PathBuf::from("bin/bangumi-renamer-bridge.exe")
    } else {
        PathBuf::from("bin/bangumi-renamer-bridge")
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![execute_bridge])
        .run(tauri::generate_context!())
        .expect("error while running Bangumi Renamer");
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn rejects_commands_outside_allow_list() {
        assert!(!ALLOWED_COMMANDS.contains(&"system.shell"));
        assert!(ALLOWED_COMMANDS.contains(&"plan.scan"));
    }

    #[test]
    fn allows_metadata_connection_test_command() {
        assert!(ALLOWED_COMMANDS.contains(&"settings.test_connection"));
    }

    #[test]
    fn bridge_error_is_json_serializable() {
        let value = json!({ "ok": false, "error": "failed" });
        assert_eq!(value["ok"], false);
    }
}
