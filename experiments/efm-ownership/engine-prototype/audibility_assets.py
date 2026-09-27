"""Generate original, quiet control audio and explicit local source definitions."""
import math
import struct
import wave

def prepare(mod):
    sounds=mod/'Sounds'
    tone=sounds/'Effects/DCSRecorderAudibility/Tone.wav'
    tone.parent.mkdir(parents=True,exist_ok=True)
    rate=48000
    # A one-second loop: two gently faded 660 Hz beeps, peak amplitude 0.15.
    samples=[]
    for i in range(rate):
        t=i/rate;local=t%0.5
        envelope=max(0,min(1,local/0.02,(0.2-local)/0.02))
        samples.append(round(32767*0.15*envelope*math.sin(2*math.pi*660*t)))
    with wave.open(str(tone),'wb')as output:
        output.setnchannels(1);output.setsampwidth(2);output.setframerate(rate)
        output.writeframes(struct.pack('<'+'h'*len(samples),*samples))
    definitions=sounds/'sdef/DCSRecorderAudibility'
    definitions.mkdir(parents=True,exist_ok=True)
    for name,asset in [('Tone','Effects/DCSRecorderAudibility/Tone'),
                       ('Afterburner','Effects/Aircrafts/FA-18/Afterburner')]:
        # Documented fields from the locally installed Doc/Sounds/example.sdef.
        (definitions/(name+'.sdef')).write_text(
            '-- THROWAWAY: known attenuation, no directional cone.\n'
            f'wave = "{asset}"\n'
            'gain = 1\npitch = 1\nposition = {0, 0, 0}\n'
            'silent_radius = 0\npeak_radius = 0\ninner_radius = 100\nouter_radius = 4000\n'
            'direction = {0, 0, 0}\ncone_inner_angle = 0\ncone_outer_angle = 0\ncone_outer_gain = 1\n',
            encoding='ascii')
