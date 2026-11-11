"""Bounded, explicit one-shot Hermes pilot test; no production flags changed by runner.

Only tool names, terminal answer and usage are retained, not page snapshots or tab lists.
"""
from pathlib import Path
import argparse
import fcntl
import json
import os
import signal
import subprocess
import sys
import threading
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', default='operations/tasks/dinda-browser-read-pilot.txt')
    parser.add_argument('--toolsets', default='mcp-flow_chrome')
    parser.add_argument('--report', default='hermes-model-browser-read-pilot')
    parser.add_argument('--max-turns', type=int, default=6)
    parser.add_argument('--scope', choices=['read_only', 'prepare_only', 'submit_once', 'monitor_only'], default='read_only')
    options = parser.parse_args()
    task = (ROOT / options.task).resolve()
    if not task.is_relative_to(ROOT / 'operations/tasks') or not options.report.replace('-', '').isalnum():
        parser.error('Task/report must stay within the project pilot area')
    lock = (ROOT / 'operations/hermes-worker.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        parser.error('Another Hermes worker is active')
    if options.scope == 'submit_once':
        from app import review
        project = json.loads((ROOT / 'config/project.json').read_text())
        permission = json.loads((ROOT / 'config/pilot.json').read_text())
        with review.connect(ROOT) as db:
            job = db.execute('SELECT * FROM generation_jobs WHERE id=?',
                             (permission.get('job_id'),)).fetchone()
        if (not project.get('generation_enabled') or project.get('mode') != 'controlled_pilot'
                or not job or job['state'] != 'submitted' or job['authorized_credits'] > 25):
            lock.close()
            parser.error('No current authorized submission reservation; inspect existing jobs')
    args = [str(Path.home() / '.local/bin/hermes'), '-p', 'ai-influencer-dinda',
            '--in', str(ROOT), 'chat', '--provider', 'openai-codex',
            '--oneshot', '--format', 'stream-json', '--max-turns', str(options.max_turns),
            '-t', options.toolsets, '--query-file', str(task)]
    report = {'started_at': datetime.now(timezone.utc).isoformat(),
              'executor': 'hermes_model', 'scope': options.scope, 'tools': [],
              'generation_submission_authorized': options.scope == 'submit_once',
              'generation_started': None if options.scope == 'submit_once' else False,
              'raw_snapshots_saved_by_runner': False}
    process = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True, start_new_session=True)

    def stop():
        report['runner_timeout'] = True
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    timer = threading.Timer(210, stop)
    timer.start()
    try:
        for line in process.stdout:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get('type') == 'tool_use':
                name = event.get('name', '')
                report['tools'].append(name)
                print('Hermes tool: ' + name, flush=True)
            elif event.get('type') == 'tool_result':
                text = str(event.get('output', '')).lower()
                if event.get('is_error') or any(s in text for s in
                    ('devtoolsactiveport', 'could not connect', 'connection refused', 'timed out')):
                    report.setdefault('tool_errors', []).append(event.get('name'))
            elif event.get('type') == 'result':
                report['result'] = {k: event[k] for k in
                    ('exit_code', 'text', 'tokens', 'duration_ms', 'session_id') if k in event}
        report['process_exit_code'] = process.wait()
    finally:
        timer.cancel()
        if process.poll() is None:
            stop()
            process.wait(timeout=10)
        path = ROOT / ('operations/reports/' + options.report + '.json')
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        lock.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report.get('process_exit_code', 1) or report.get('result', {}).get('exit_code', 1)


if __name__ == '__main__':
    sys.exit(main())
