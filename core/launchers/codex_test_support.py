"""External app-server spy used by launcher subprocess tests."""

CODEX_STUB = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
roots = []
thread = {}
def send(value):
    print(json.dumps(value), flush=True)
for line in sys.stdin:
    request = json.loads(line)
    method, params = request['method'], request.get('params', {})
    result = {}
    if method == 'skills/extraRoots/set':
        roots = params['extraRoots']
    elif method == 'skills/list':
        skills = [{'name': p.parent.name, 'path': str(p.resolve()), 'enabled': True}
                  for root in roots for p in Path(root).rglob('SKILL.md')]
        result = {'data': [{'cwd': params['cwds'][0], 'skills': skills, 'errors': []}]}
    elif method == 'thread/start':
        thread = params
        result = {'thread': {'id': 'thread'}}
    elif method == 'turn/start':
        result = {'turn': {'id': 'turn'}}
        skill = next(x for x in params['input'] if x['type'] == 'skill')
        prompt = '\n'.join(x['text'] for x in params['input'] if x['type'] == 'text')
        # Flatten only received fields for the existing flag-oriented assertions.
        # A run with no declared model starts its thread with none, and the record carries no
        # --model.
        observed = [*sys.argv[1:], *(['--model', thread['model']] if thread['model'] else []),
                    '--skill-name', skill['name'], '--skill-path', skill['path']]
        for root in thread['config']['sandbox_workspace_write']['writable_roots']:
            observed += ['--add-dir', root]
        observed += [prompt]
        log = Path(os.environ['CODEX_ARGV_LOG'])
        log.write_text(json.dumps(observed) if log.suffix == '.json' else '\n'.join(observed)+'\n')
        log.with_suffix('.requests.json').write_text(json.dumps({'thread':thread,'turn':params,'roots':roots}))
    if 'id' in request:
        send({'id': request['id'], 'result': result})
    if method == 'turn/start':
        send({'method': 'item/completed', 'params': {'threadId': 'thread', 'item': {'id': 'message', 'type': 'agentMessage', 'text': 'done'}}})
        send({'method': 'turn/completed', 'params': {'threadId': 'thread', 'turn': {'id': 'turn', 'status': 'completed', 'error': None}}})
'''
