"""Render one scripted utterance over the OpenAI Realtime WebSocket."""
import base64
from getpass import getuser
from io import BytesIO
import json
import os
import subprocess
import sys
from time import monotonic
from urllib.parse import urlencode
import wave

PROFILE_ID = 'openai-realtime-cedar-goo'
ZH_PROFILE_ID = 'openai-realtime-cedar-goo-zh'
PROFILE_IDS = (PROFILE_ID, ZH_PROFILE_ID)
SAMPLE_RATE = 24000
REALTIME_URL = 'wss://api.openai.com/v1/realtime'


def api_key(service):
    if sys.platform == 'darwin' and service:
        try:
            result = subprocess.run(
                ['/usr/bin/security', 'find-generic-password', '-a', getuser(), '-s', service, '-w'],
                text=True, capture_output=True, timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired):
            result = None
        if result and result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not key:
        raise ValueError('Configure the Goo Realtime credential in Keychain or set OPENAI_API_KEY.')
    return key


def fetch_realtime(request, service):
    from websockets.exceptions import WebSocketException
    from websockets.sync.client import connect

    key = api_key(service)
    url = REALTIME_URL + '?' + urlencode({'model': request['model']})
    chunks = []
    deadline = monotonic() + 180

    def send(socket, packet):
        socket.send(json.dumps(packet))

    def receive(socket, kind):
        while True:
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise TimeoutError('Realtime narration exceeded its request deadline')
            event = json.loads(socket.recv(timeout=remaining))
            event_type = event['type']
            if event_type == 'error':
                error = event.get('error', {})
                raise ValueError(f'OpenAI Realtime rejected the request ({error.get("code") or error.get("type")}).')
            if event_type == 'response.output_audio.delta':
                chunks.append(base64.b64decode(event['delta'], validate=True))
            if event_type == kind:
                return event

    try:
        with connect(url, additional_headers={'Authorization': f'Bearer {key}'},
                     open_timeout=20, close_timeout=3, max_size=2**22) as socket:
            receive(socket, 'session.created')
            send(socket, {'type': 'session.update', 'session': {
                'type': 'realtime',
                'instructions': request['instructions'],
                'output_modalities': ['audio'],
                'audio': {
                    'input': {'turn_detection': None},
                    'output': {'voice': request['voice'], 'speed': request['speed'],
                               'format': {'type': 'audio/pcm', 'rate': SAMPLE_RATE}},
                },
            }})
            session = receive(socket, 'session.updated')['session']
            actual = session['audio']['output']
            if session['model'] != request['model'] or actual['voice'] != request['voice']:
                raise ValueError('Realtime session returned an unexpected model or voice')
            if actual['format'] != {'type': 'audio/pcm', 'rate': SAMPLE_RATE}:
                raise ValueError('Realtime session returned an unexpected audio format')
            send(socket, {'type': 'conversation.item.create', 'item': {
                'type': 'message', 'role': 'user',
                'content': [{'type': 'input_text', 'text': request['input']}],
            }})
            receive(socket, 'conversation.item.added')
            send(socket, {'type': 'response.create'})
            response = receive(socket, 'response.done')['response']
    except (OSError, WebSocketException) as error:
        status = getattr(getattr(error, 'response', None), 'status_code', None)
        raise ValueError(f'OpenAI Realtime connection failed ({status or type(error).__name__}).') from None

    if response['status'] != 'completed':
        details = response.get('status_details') or {}
        reason = (details.get('error') or {}).get('code') or details.get('reason') or response['status']
        raise ValueError(f'OpenAI Realtime narration did not complete ({reason}).')
    transcript = ' '.join(
        part.get('transcript', '') for item in response.get('output', [])
        for part in item.get('content', []) if part.get('type') in ('audio', 'output_audio')
    ).strip()
    pcm = b''.join(chunks)
    if not pcm or len(pcm) % 2 or not transcript:
        raise ValueError('OpenAI Realtime did not return complete audio and transcript')
    output = BytesIO()
    with wave.open(output, 'wb') as wav:
        wav.setparams((1, 2, SAMPLE_RATE, 0, 'NONE', 'not compressed'))
        wav.writeframes(pcm)
    return output.getvalue(), {'response_id': response['id'], 'transcript': transcript}
