"""Read-only sampling of existing service health during deployment/benchmark."""
import json
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path('/home/guoliang/kokoro-tts-deploy/evidence')
STOP = ROOT / 'monitor.stop'
with (ROOT / 'monitor.jsonl').open('a') as output:
    while not STOP.exists():
        record = {'time': time.time(), 'health': {}, 'load': Path('/proc/loadavg').read_text().split()[:3]}
        for port in [8090, 8092]:
            start = time.monotonic()
            try:
                response = urllib.request.urlopen('http://10.60.11.3:%s/health' % port, timeout=3)
                body = json.load(response)
                record['health'][str(port)] = {'http': response.status, 'milliseconds': (time.monotonic()-start)*1000, 'body': body}
            except Exception as error:
                record['health'][str(port)] = {'error': str(error)}
        result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}'], stdout=subprocess.PIPE, universal_newlines=True, timeout=10)
        record['containers'] = result.stdout.splitlines()
        output.write(json.dumps(record)+'\n')
        output.flush()
        time.sleep(3)
