"""Bounded Dinda Hermes check; retain summary/tool names, never raw page snapshots."""
from pathlib import Path
import argparse
import fcntl
import json
import os
import signal
import subprocess
import threading
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True)
    parser.add_argument('--report', required=True)
    parser.add_argument('--toolsets', default='file,mcp-flow_chrome,mcp-dinda_editor_guard')
    args = parser.parse_args()
    task = (ROOT / args.task).resolve()
    report = (ROOT / args.report).resolve()
    if not task.is_relative_to(ROOT / 'operations/tasks') or not report.is_relative_to(ROOT / 'operations/reports'):
        parser.error('Task and report must stay in project operations directories')
    with (ROOT / 'operations/hermes-worker.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = {'started_at': datetime.now(timezone.utc).isoformat(), 'tools': [], 'tool_errors': 0}
        command = ['/Users/zidane/.local/bin/hermes', '-p', 'ai-influencer-dinda', '--in', str(ROOT),
                   'chat', '--oneshot', '--format', 'stream-json', '--max-turns', '28',
                   '-t', args.toolsets, '--query-file', str(task)]
        process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                   text=True, start_new_session=True)
        def stop():
            result['runner_timeout'] = True
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        timer = threading.Timer(180, stop)
        timer.start()
        try:
            for line in process.stdout:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if event.get('type') == 'tool_use':
                    name = event.get('name', '')
                    result['tools'].append(name)
                    print('Hermes: ' + name, flush=True)
                elif event.get('type') == 'tool_result' and event.get('is_error'):
                    result['tool_errors'] += 1
                elif event.get('type') == 'result':
                    result['summary'] = event.get('text', '')
                    result['session_id'] = event.get('session_id')
                    result['model_exit_code'] = event.get('exit_code')
                    if event.get('error'):
                        result['runner_error'] = event['error']
            result['process_exit_code'] = process.wait()
        finally:
            timer.cancel()
            if process.poll() is None:
                stop()
                process.wait(timeout=10)
            report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result.get('process_exit_code', 1)

if __name__ == '__main__':
    raise SystemExit(main())
