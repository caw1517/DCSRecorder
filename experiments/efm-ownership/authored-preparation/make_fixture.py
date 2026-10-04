"""Construct a new stock-aircraft authored scene for the live copy test."""
from pathlib import Path
import copy, io, json, math, struct, sys, wave
sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'companion'))
import authored_missions as a


def create(baseline, output):
    # Documented construction of a NEW authored fixture, not reimport of a
    # generated copy. The template supplies installed Hornet configuration.
    data=a.zip_entries(Path(baseline).read_bytes())
    m=a.LuaData(data['mission'].decode('utf-8-sig')).mission()
    base=next(r for r in a.aircraft(m) if r['unit']['type']=='FA-18C_hornet')
    groups={}
    for i,name in enumerate(('Record Hornet','Wing Hornet','Scene Witness'),1):
        g=copy.deepcopy(base['group']);u=copy.deepcopy(base['unit']);g['units']={1:u}
        g.update(name=name+' Group',groupId=12100+i,lateActivation=False,uncontrolled=False,task='Nothing',tasks={},start_time=0)
        u.update(name=name,unitId=12200+i,skill='Player' if i==1 else 'High',type='FA-18C_hornet',
                 livery_id='Blue Angels Jet Team',x=-315000+(i-1)*180,y=892000+(i-1)*160,
                 alt=1800,alt_type='BARO',speed=140,heading=0,psi=0)
        u['payload']['pylons']={station:dict(CLSID='<CLEAN>') for station in (2,3,5,7,8)};g.update(x=u['x'],y=u['y'])
        point=dict(x=u['x'],y=u['y'],alt=1800,alt_type='BARO',speed=140,speed_locked=True,ETA=0,ETA_locked=True,
                   action='Turning Point',type='Turning Point',task=dict(id='ComboTask',params=dict(tasks={})))
        g['route']=dict(points={1:point,2:dict(point,x=u['x']+30000,ETA=30000/140,ETA_locked=False)})
        groups[i]=g
    m['coalition']['blue']['country']={1:dict(id=2,name='USA',plane=dict(group=groups))}
    m['coalition']['red']['country']={};m['coalition']['neutrals']['country']={}
    truck=dict(name='Authored reference truck',unitId=12301,type='M 818',skill='Average',x=-315050,y=891900,heading=0,playerCanDrive=False,coldAtStart=False)
    vehicle=dict(name='Authored trucks',groupId=12401,units={1:truck},x=truck['x'],y=truck['y'],start_time=0,
                 task='Ground Nothing',taskSelected=True,tasks={},uncontrollable=False,visible=False,hidden=False,route=dict(points={1:dict(x=truck['x'],y=truck['y'],
                 alt=0,alt_type='BARO',speed=0,action='Off Road',type='Turning Point',formation_template='',ETA=0,ETA_locked=True,
                 speed_locked=True,task=dict(id='ComboTask',params=dict(tasks={})))}))
    m['coalition']['blue']['country'][1]['vehicle']=dict(group={1:vehicle})
    m['triggers']={'zones':{1:dict(name='Authored reference zone',zoneId=13001,x=-315050,y=891900,radius=100,type=0,
                                 color={1:1,2:1,3:1,4:0.15},hidden=False,heading=0,  # fields the Mission Editor saves and requires
                                 properties={1:dict(key='',value='')})}}
    m['theatre']='Caucasus'
    for value in m['weather']['wind'].values():value['speed']=0
    m['start_time']=12*3600;m['descriptionText']='DictKey_AuthoredBriefing';m['descriptionBlueTask']='DictKey_AuthoredTask';m['maxDictId']=15000
    dictionary=dict(DictKey_AuthoredBriefing='AUTHORED COPY CONTROL. Three stock Hornets, one truck and one reference zone. A message and short chime occur after 12 seconds.',
                    DictKey_AuthoredTask='Record Hornet is the capture aircraft. Wing Hornet is the separately authored player start for playback.',
                    DictKey_AuthoredMessage='Authored scene trigger: message, flag and chime preserved.')
    # Keep the DEFAULT/FR baseline dictionaries, resource maps and referenced
    # files (briefing image): the mission still refers to their keys.
    base={(l,k):a.LuaData(data[f'l10n/{l}/{k}'].decode('utf-8-sig')).assignment(k)
          for l in ('DEFAULT','FR') for k in ('dictionary','mapResource')}
    data={n:v for n,v in data.items() if not n.startswith(('l10n/','DCSRecorder')) and n!='mission'
          or n.startswith(('l10n/DEFAULT/','l10n/FR/')) and not n.endswith(('/dictionary','/mapResource'))}
    data['l10n/DEFAULT/dictionary']=a.encoded('dictionary',dict(base['DEFAULT','dictionary'],**dictionary))
    data['l10n/FR/dictionary']=a.encoded('dictionary',{**base['FR','dictionary'],**dictionary,'DictKey_AuthoredBriefing':'SCENE SOURCE : trois Hornet, un camion et une zone de reference.'})
    audio=io.BytesIO()
    with wave.open(audio,'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(22050)
        f.writeframes(b''.join(struct.pack('<h',int(1600*math.sin(2*math.pi*880*i/22050))) for i in range(4410)))
    for locale in ('DEFAULT','FR'):
        data[f'l10n/{locale}/mapResource']=a.encoded('mapResource',dict(base[locale,'mapResource'],ResKey_AuthoredChime='authored-chime.wav'))
        data[f'l10n/{locale}/authored-chime.wav']=audio.getvalue()
    m['trigrules']={1:dict(comment='Authored message, resource and occupied flag',predicate='triggerOnce',eventlist='',
        rules={1:dict(predicate='c_time_after',seconds=12)},actions={
            1:dict(predicate='a_set_flag_value',flag='DCSR_AUTHORED_1_READY',value=73),
            2:dict(predicate='a_out_text_delay',text='DictKey_AuthoredMessage',seconds=15,clearview=False,start_delay=0),
            3:dict(predicate='a_out_sound',file='ResKey_AuthoredChime',start_delay=0)})}
    m['trig']={k:{} for k in ('actions','conditions','func','funcStartup','flag')}
    for field,value in a.compiled_trigger(1,m['trigrules'][1]).items():m['trig'][field][1]=value
    data['mission']=a.encoded('mission',m)
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    with Path(output).open('xb') as f:f.write(a.packed(data))
    print(json.dumps(a.inspect(output),indent=2))


if __name__=='__main__':create(sys.argv[1],sys.argv[2])
