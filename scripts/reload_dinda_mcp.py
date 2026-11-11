"""Reconcile only Dinda's MCP servers using Hermes' authenticated local client."""
import json
import os
import subprocess
import sys

SESSION = 'local-dafa55d43ff737da77ad56ebd24fd6ab74f4c64031c7cdfb24d65a60a0d7c776'
CODE = '''import sys,asyncio,json
sys.path.insert(0,'/Users/zidane/.hermes/hermes-agent')
import hermes_bootstrap
from hermes_cli.gateway_client import connect_gateway
async def main():
 async with connect_gateway() as client:
  result=await client.rpc('reload.mcp',session_id=sys.argv[1],confirm=True,_timeout=50)
  print(json.dumps(result))
asyncio.run(main())
'''

def main():
    env = dict(os.environ)
    env['HERMES_HOME'] = '/Users/zidane/.hermes/profiles/ai-influencer-dinda'
    result = subprocess.run(['/Users/zidane/.hermes/tools/python-3.14.9+20261021-darwin-arm64/bin/python3',
                             '-I', '-c', CODE, sys.argv[1] if len(sys.argv) > 1 else SESSION],
                            env=env, capture_output=True, text=True, timeout=60)
    if result.returncode:
        print('Dinda MCP reconciliation failed; exit ' + str(result.returncode))
        return result.returncode
    print(json.dumps(json.loads(result.stdout.strip()), ensure_ascii=False))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
