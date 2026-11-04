"""Short, deterministic prop sounds. Anchor their first sample to the picture contact."""
import numpy as np

def render_foley(timeline, frames, rate):
    bus = np.zeros((frames,2), np.float32)
    rng = np.random.default_rng(104)
    for cue in timeline['foley']:
        t = np.arange(round(.18*rate))/rate
        noise = rng.normal(0,1,len(t))
        kind = cue['kind']
        if kind == 'clap':
            sound = np.diff(noise,prepend=0)*np.exp(-t*68) + .8*np.sin(2*np.pi*440*t)*np.exp(-t*53)
        elif kind in ('tap','switch'):
            sound = np.sin(2*np.pi*(1050 if kind=='switch' else 330)*t)*np.exp(-t*65)
        elif kind in ('paper','pencil'):
            sound = np.diff(noise,prepend=0)*np.sin(np.pi*t/t[-1])**2*np.exp(-t*16)
        else:
            raise ValueError(f'Add a sound for {kind} in scripts/foley.py')
        gain = cue.get('gain',.1)
        assert 0 <= gain <= .5
        at = cue['frame']*(rate//24)
        n = min(len(t), frames-at)
        bus[at:at+n] += (gain*sound[:n]/max(1e-6,np.max(np.abs(sound))))[:,None]
    return bus
