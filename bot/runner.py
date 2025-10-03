"""
Bot runner with process management.
"""

import os
import sys
import time
import subprocess
import signal

def kill_existing_bot_processes():
    """Kill all existing bot processes to prevent multiple instances."""
    try:
        # Find all python processes running bot/main.py or bot/runner.py
        result = subprocess.run(
            ["pgrep", "-f", "python3.*bot/(main|runner).py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"Found {len(pids)} existing bot processes: {pids}")
            
            for pid in pids:
                try:
                    pid_int = int(pid.strip())
                    # Skip current process
                    if pid_int != os.getpid():
                        print(f"Terminating bot process {pid_int}")
                        os.kill(pid_int, signal.SIGTERM)
                        time.sleep(0.5)  # Give it time to terminate gracefully
                        
                        # Force kill if still running
                        try:
                            os.kill(pid_int, signal.SIGKILL)
                        except ProcessLookupError:
                            pass  # Process already terminated
                except (ValueError, ProcessLookupError) as e:
                    print(f"Could not terminate process {pid}: {e}")
            
            print("All existing bot processes terminated")
            time.sleep(1)  # Wait for processes to fully terminate
        else:
            print("No existing bot processes found")
            
    except Exception as e:
        print(f"Error killing existing processes: {e}")

def main():
    """Main runner function."""
    print("Starting Raiden Shogun Bot Runner...")
    
    # Kill any existing bot processes
    print("Checking for existing bot processes...")
    kill_existing_bot_processes()
    
    # Start the bot
    while True:
        print("Starting bot...")
        exit_code = os.system("python3 bot/main.py")
        print(f"Bot exited with code {exit_code}")
        
        if exit_code == 0:
            # Clean shutdown requested
            print("Shutting down runner.")
            break
        else:
            # Bot crashed or requested restart
            print("Restarting bot in 2 seconds...")
            time.sleep(2)

if __name__ == "__main__":
    main()