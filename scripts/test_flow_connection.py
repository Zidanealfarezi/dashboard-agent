"""One-shot read-only MCP connection check. No model request or generation."""
from pathlib import Path
import json
import os
import queue
import re
import subprocess
import threading
import time

root = Path(__file__).resolve().parents[1]
entry = json.loads((root / 'operations/reports/chrome-connector-active-entry.json').read_text())
env = os.environ.copy()
env.update(entry['env'])
process = subprocess.Popen([entry['command'], *entry['args']], stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env=env)
messages = queue.Queue()


def reader():
    for line in process.stdout:
        try:
            messages.put(json.loads(line))
        except ValueError:
            continue


threading.Thread(target=reader, daemon=True).start()
request_id = 0


def rpc(method, params):
    global request_id
    request_id += 1
    process.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': request_id, 'method': method, 'params': params}) + '\n')
    process.stdin.flush()
    deadline = time.monotonic() + 180
    while True:
        response = messages.get(timeout=max(0, deadline - time.monotonic()))
        if response.get('id') == request_id:
            if 'error' in response:
                raise RuntimeError('MCP protocol request failed')
            return response.get('result', {})


def call(name, arguments):
    if name not in ('list_pages', 'select_page', 'take_snapshot'):
        raise RuntimeError('Read-only test tool restriction')
    result = rpc('tools/call', {'name': name, 'arguments': arguments})
    if result.get('isError'):
        # Return a bounded diagnostic without writing page contents or credentials.
        text = '\n'.join(c.get('text', '') for c in result.get('content', []) if c.get('type') == 'text')
        if any(s in text.lower() for s in ('permission', 'allow', 'connect', 'debugging', 'devtoolsactiveport')):
            print('Browser connection not ready; permission/connection diagnostic: ' + text[:350], flush=True)
        raise RuntimeError('Browser tool failed')
    return '\n'.join(c.get('text', '') for c in result.get('content', []) if c.get('type') == 'text')


try:
    rpc('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {},
                       'clientInfo': {'name': 'hermes-flow-connection-check', 'version': '1.0'}})
    process.stdin.write(json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'}) + '\n')
    process.stdin.flush()
    tools = rpc('tools/list', {})
    schemas = {t['name']: t.get('inputSchema', {}).get('properties', {}) for t in tools.get('tools', [])}
    assert all(n in schemas for n in ('list_pages', 'select_page', 'take_snapshot'))
    print('MCP ready. Requesting Chrome read access; approve Chrome dialog if shown.', flush=True)
    text = call('list_pages', {})
    print('Chrome page list received.', flush=True)
    project = 'https://flow.google.com/project/3e9fe2ca-ee39-4235-81a1-9d8bfdee9603'
    matches = [(int(m.group(1)), m.group(2)) for m in re.finditer(r'^\s*(\d+):[^\n]*?\((https?://[^\s)]+)\)', text, re.M)
               if m.group(2).rstrip('/') == project]
    if not matches:
        flow_lines = [line for line in text.splitlines() if project in line]
        print('Flow page entries found: ' + str(len(flow_lines)), flush=True)
        print('Connection reached Chrome, but the exact Dinda Flow tab was not found. Other tab contents not recorded.', flush=True)
        raise SystemExit(2)
    page_id = matches[0][0]
    print('Exact Dinda Flow page found.', flush=True)
    args = {'pageId': page_id}
    if 'bringToFront' in schemas['select_page']:
        args['bringToFront'] = False
    call('select_page', args)
    print('Dinda context selected; reading snapshot.', flush=True)
    snapshot_args = {'pageId': page_id} if 'pageId' in schemas['take_snapshot'] else {}
    snapshot = call('take_snapshot', snapshot_args)
    print('Snapshot received: ' + str(len(snapshot)) + ' characters; Dinda marker=' + str('dinda' in snapshot.lower()), flush=True)
    if 'dinda' not in snapshot.lower():
        raise RuntimeError('Dinda page was not confirmed')
    report = {'connection_verified': True, 'project_title_verified': 'dinda', 'project_url': project,
              'tools_used': ['list_pages', 'select_page', 'take_snapshot'], 'generation_started': False,
              'other_page_contents_stored': False, 'snapshot_stored': False}
    (root / 'operations/reports/hermes-flow-connection-test.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)
except queue.Empty:
    print('Chrome connection timed out. No generation performed.', flush=True)
    raise SystemExit(3)
except Exception as exc:
    print('Read test failed: ' + type(exc).__name__ + ': ' + str(exc)[:150] + '. No generation performed.', flush=True)
    raise SystemExit(1)
finally:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
