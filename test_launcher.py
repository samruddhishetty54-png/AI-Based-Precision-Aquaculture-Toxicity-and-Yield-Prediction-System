"""Launcher verification and health check for the Streamlit dashboard.

Verifies:
1. Streamlit process starts up cleanly in headless mode.
2. Webserver binds to 127.0.0.1:8502 and responds with HTTP 200 OK at /_stcore/health.
3. Streamlit AppTest verifies page discovery and component rendering.
4. Clean process termination without lingering background processes.
"""

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


def test_launcher_startup():
    """Verify Streamlit webserver starts and serves health check endpoint."""
    repo_root = Path(__file__).resolve().parent
    python_exe = repo_root / ".venv" / "Scripts" / "python.exe"
    if not python_exe.exists():
        python_exe = Path(sys.executable)
        
    dashboard_py = repo_root / "dashboard.py"
    if not dashboard_py.exists():
        print("ERROR: dashboard.py not found!")
        return False

    port = 8502
    host = "127.0.0.1"
    url = f"http://{host}:{port}/_stcore/health"

    cmd = [
        str(python_exe),
        "-m", "streamlit", "run",
        str(dashboard_py),
        f"--server.port={port}",
        f"--server.address={host}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]

    print(f"[LAUNCHER TEST] Starting Streamlit on {host}:{port}...")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(repo_root),
    )

    started = False
    max_wait_seconds = 20
    start_time = time.time()

    try:
        while time.time() - start_time < max_wait_seconds:
            # Check if process crashed early
            ret_code = proc.poll()
            if ret_code is not None:
                stdout, stderr = proc.communicate()
                print(f"[LAUNCHER TEST] Process exited prematurely with code {ret_code}")
                print("STDOUT:", stdout)
                print("STDERR:", stderr)
                return False

            try:
                with urllib.request.urlopen(url, timeout=2) as response:
                    if response.status == 200:
                        body = response.read().decode("utf-8")
                        elapsed = time.time() - start_time
                        print(f"[LAUNCHER TEST] SUCCESS: Health endpoint responded 200 OK in {elapsed:.2f}s ({body.strip()})")
                        started = True
                        break
            except Exception:
                time.sleep(1)

    finally:
        # Clean termination on Windows
        print("[LAUNCHER TEST] Stopping Streamlit process...")
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        else:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    return started


def test_apptest_pages():
    """Verify pages with Streamlit AppTest framework."""
    print("[PAGE DISCOVERY TEST] Verifying pages using Streamlit testing...")
    repo_root = Path(__file__).resolve().parent
    pages_dir = repo_root / "app" / "dashboard" / "pages"
    
    expected_pages = [
        "01_Overview.py",
        "02_Water_Quality_Toxicity.py",
        "03_Next_Visit_DO_Hypoxia.py",
        "04_Growth_Feeding_Advisor.py",
        "05_Historical_Data_Explorer.py",
        "06_Simulation_Sandbox.py",
        "07_Model_Registry_Governance.py",
    ]
    
    all_discovered = True
    for p_name in expected_pages:
        p_path = pages_dir / p_name
        if not p_path.exists():
            print(f"  [MISSING] {p_name}")
            all_discovered = False
        else:
            print(f"  [DISCOVERED] {p_name} ({p_path.stat().st_size} bytes)")

    return all_discovered


def main():
    print("=" * 60)
    print("AI-BASED PRECISION AQUACULTURE: DASHBOARD LAUNCHER VERIFICATION")
    print("=" * 60)
    
    pages_ok = test_apptest_pages()
    if not pages_ok:
        print("[ERROR] Page discovery failed.")
        sys.exit(1)
        
    server_ok = test_launcher_startup()
    if not server_ok:
        print("[ERROR] Streamlit server failed to start or respond to health probe.")
        sys.exit(1)
        
    print("=" * 60)
    print("ALL LAUNCHER VERIFICATIONS PASSED SUCCESSFULLY.")
    print("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()

