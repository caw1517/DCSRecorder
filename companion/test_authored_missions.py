"""Contracts for immutable authored mission preparation."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import authored_missions as a

class AuthoredCopies(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.source=self.root/'source.miz'
        def group(uid,skill):
            return dict(name=f'group {uid}',groupId=uid+100,units={1:dict(name=f'unit {uid}',unitId=uid,type='FA-18C_hornet',
                skill=skill,livery_id='Blue Angels Jet Team',x=uid,y=99)},route=dict(points={1:dict(type='Turning Point',
                x=uid,y=99,task=dict(id='ComboTask',params=dict(tasks={}))) }))
        self.m=dict(theatre='Caucasus',weather=dict(wind={k:dict(speed=0) for k in ('atGround','at2000','at8000')}),
                    coalition=dict(blue=dict(country={1:dict(id=2,plane=dict(group={1:group(11,'Player'),2:group(12,'High')}))})),
                    descriptionText='DictKey_brief',trig={},trigrules={},
                    triggers=dict(zones={1:dict(name='DCSR_AUTHORED_1',x=123,y=456,radius=30)}))
        self.entries={'l10n/DEFAULT/dictionary':b'dictionary={brief="original"}',
                      'l10n/FR/dictionary':b'dictionary={brief="bonjour"}','l10n/DEFAULT/sound.ogg':b'untouched bytes'}
        self.write()

    def tearDown(self):self.tmp.cleanup()
    def write(self):
        self.entries['mission']=a.encoded('mission',self.m);self.source.write_bytes(a.packed(self.entries))
    def prepare(self,name='out',**kwargs):return a.prepare_recording(self.source,11,self.root/name,**kwargs)

    def test_copy_preserves_source_scene_resources_and_repeat_is_identical(self):
        before=self.source.read_bytes();one=self.prepare();self.prepare('again')
        self.assertEqual(self.source.read_bytes(),before)
        self.assertEqual((self.root/'out/prepared.miz').read_bytes(),(self.root/'again/prepared.miz').read_bytes())
        self.assertEqual(one['namespace'],'DCSR_AUTHORED_2');self.assertTrue(one['preservation']['restored_structure_equals_source'])
        contents=a.zip_entries((self.root/'out/prepared.miz').read_bytes())
        for key in self.entries:
            if key!='mission':self.assertEqual(contents[key],self.entries[key])
        prepared=a.LuaData(contents['mission'].decode()).mission()
        self.assertEqual(a.selected(prepared,12),a.selected(self.m,12))

    def test_inspect_never_executes_authored_lua(self):
        self.entries['mission']=b'mission = {}; os.execute("bad")';self.source.write_bytes(a.packed(self.entries))
        with self.assertRaisesRegex(ValueError,'Trailing'):a.inspect(self.source)

    def test_generated_copy_and_changed_source_are_refused(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError,'generated copies'):a.inspect(self.root/'out/prepared.miz')
        with self.assertRaisesRegex(ValueError,'changed after selection'):self.prepare('changed',expected_sha='0'*64)

    def test_selected_task_is_not_silently_removed(self):
        a.selected(self.m,11)['group']['route']['points'][1]['task']=dict(id='Orbit',params={});self.write()
        with self.assertRaisesRegex(ValueError,'unit 11, route point 1: task Orbit'):self.prepare()
        self.assertFalse((self.root/'out').exists())

    def test_unknown_script_and_compiled_only_code_are_refused(self):
        self.m['trigrules']={1:dict(comment='Authored dynamic',predicate='triggerStart',rules={},actions={1:dict(predicate='a_do_script',text='arbitrary()')})};self.write()
        with self.assertRaisesRegex(ValueError,'Trigger 1 "Authored dynamic", action 1: unclassified a_do_script'):self.prepare()
        self.m['trigrules']={};self.m['trig']={'actions':{1:'arbitrary()'}};self.write()
        with self.assertRaisesRegex(ValueError,'indices differ'):self.prepare()

    def me_defaults(self,uid):
        # Exact automatic actions DCS 2.9.30 Mission Editor saved on newly placed Hornets.
        gid=1  # datalink network number; DCS 2.9.30 saved 1 on a newly placed Hornet
        wrapped=lambda n,action:dict(enabled=True,auto=True,id='WrappedAction',number=n,params=dict(action=action))
        return {1:wrapped(1,dict(id='EPLRS',params=dict(value=True,groupId=gid))),
                2:wrapped(2,dict(id='Option',params=dict(value=True,name=35)))}

    def test_mission_editor_automatic_actions_are_preserved_and_reported(self):
        for uid in (11,12):a.selected(self.m,uid)['group']['route']['points'][1]['task']['params']['tasks']=self.me_defaults(uid)
        self.write();result=self.prepare()
        self.assertEqual(result['behavior']['preserved'],['unit 11, route point 1, action 1: EPLRS datalink on (Mission Editor default)',
                                                         'unit 11, route point 1, action 2: allow formation side swap (Mission Editor default)'])
        prepared=a.LuaData(a.zip_entries((self.root/'out/prepared.miz').read_bytes())['mission'].decode()).mission()
        self.assertEqual(a.selected(prepared,11)['group']['route'],a.selected(self.m,11)['group']['route'])
        _,_,mission,manifest=self.playback()
        self.assertEqual(len(manifest['behavior']['preserved']),4)
        # Authored actions are kept; the only addition is the orbit that stops the
        # AI from finishing its route and lowering its own gear.
        tasks=dict(a.selected_row(mission,11)['group']['route']['points'][1]['task']['params']['tasks'])
        orbit=tasks.pop(max(tasks))
        self.assertEqual((orbit['id'],orbit['params']['pattern'],orbit['auto']),('Orbit','Circle',False))
        self.assertEqual(tasks,a.selected(self.m,11)['group']['route']['points'][1]['task']['params']['tasks'])

    def test_edited_or_other_automatic_actions_are_refused_by_name(self):
        tasks=self.me_defaults(11);a.selected(self.m,11)['group']['route']['points'][1]['task']['params']['tasks']=tasks
        for edit in (lambda t:t[1]['params']['action']['params'].update(value=False),
                     lambda t:t[1]['params']['action']['params'].update(groupId=100),
                     lambda t:t[1]['params']['action']['params'].update(groupId='1'),
                     lambda t:t[2].update(auto=False),
                     lambda t:t[2]['params']['action']['params'].update(name=17)):
            original=copy.deepcopy(tasks);edit(tasks);self.write()
            with self.assertRaisesRegex(ValueError,'unit 11, route point 1, action [12]: WrappedAction'):self.prepare()
            tasks.clear();tasks.update(original)
        # The CAP task's automatic set includes an engagement task: refused, not preserved.
        tasks[3]=dict(enabled=True,auto=True,id='EngageTargets',key='CAP',number=3,params=dict(targetTypes={1:'Air'},priority=0))
        self.write()
        with self.assertRaisesRegex(ValueError,r'action 3: EngageTargets \(added automatically by Mission Editor\)'):self.prepare()
        self.assertFalse((self.root/'out').exists())

    def test_every_conflict_is_listed_at_once(self):
        a.selected(self.m,11)['group']['route']['points'][1]['task']['params']['tasks']={1:dict(id='Orbit',params={})}
        a.selected(self.m,11)['group']['tasks']={1:dict(id='Follow')}
        self.m['trigrules']={1:dict(comment='Respawn',predicate='triggerOnce',rules={},actions={1:dict(predicate='a_activate_group',group=111)}),
                             2:dict(comment='Repeat',predicate='triggerContinious',rules={},actions={})}
        vehicle=dict(groupId=500,name='trucks',units={},route=dict(points={1:dict(task=dict(id='ComboTask',params=dict(tasks={1:dict(id='WrappedAction',params=dict(action=dict(id='Script',params=dict(command='x()'))))})))}))
        self.m['coalition']['blue']['country'][1]['vehicle']=dict(group={1:vehicle});self.write()
        with self.assertRaises(ValueError) as caught:self.prepare()
        text=str(caught.exception)
        for part in ('unit 11, route point 1, action 1: Orbit','unit 11, group task 1: Follow',
                     'Trigger 1 "Respawn", action 1: unclassified a_activate_group','Trigger 2 "Repeat": unsupported trigger type triggerContinious',
                     'vehicle objects: script task','preserved, not removed'):
            self.assertIn(part,text)

    def test_lifecycle_consequence_of_selected_aircraft_triggers_is_reported(self):
        rule=dict(comment='Lead alive',predicate='triggerOnce',rules={1:dict(predicate='c_unit_alive',unit=11),2:dict(predicate='c_group_alive',group=112)},
                  actions={1:dict(predicate='a_set_flag',flag='5')})
        self.m['trigrules']={1:rule}
        for field,value in a.compiled_trigger(1,rule).items():self.m['trig'][field]={1:value}
        self.write();manifest=self.playback()[3]
        self.assertEqual(len(manifest['behavior']['lifecycle']),2)
        self.assertIn('Trigger 1 "Lead alive" checks whether unit 11 exists',manifest['behavior']['lifecycle'][0])
        self.assertIn('unit 12 exists',manifest['behavior']['lifecycle'][1])

    def test_duplicate_identity_is_refused(self):
        a.selected(self.m,12)['unit']['unitId']=11;self.write()
        with self.assertRaisesRegex(ValueError,'ambiguous'):self.prepare()

    def test_existing_trigger_indices_and_flag_are_retained(self):
        rule=dict(comment='Authored flag',predicate='triggerOnce',rules={1:dict(predicate='c_time_after',seconds=4)},
                  actions={1:dict(predicate='a_set_flag_value',flag='DCSR_AUTHORED_2_READY',value=73)})
        self.m['trigrules']={9:rule}
        for field,value in a.compiled_trigger(9,rule).items():self.m['trig'][field]={9:value}
        self.write();result=self.prepare()
        self.assertEqual(result['trigger_indices'],[10]);self.assertEqual(result['namespace'],'DCSR_AUTHORED_3')
        prepared=a.LuaData(a.zip_entries((self.root/'out/prepared.miz').read_bytes())['mission'].decode()).mission()
        self.assertEqual(prepared['trigrules'][9],rule)

    def test_mission_editor_serialized_trigger_is_accepted_but_event_code_is_not(self):
        # Exact tables DCS 2.9.30 wrote for the authored fixture (source-v4-live).
        self.m['trigrules']={1:dict(comment='Authored message',predicate='triggerOnce',eventlist='',
            rules={1:dict(predicate='c_time_after',seconds=12)},actions={
            1:dict(predicate='a_set_flag_value',flag='DCSR_AUTHORED_1_READY',value=73),
            2:dict(predicate='a_out_text_delay',text='DictKey_brief',KeyDict_text='DictKey_brief',seconds=15,clearview=False,start_delay=0)})}
        self.m['trig']=dict(events={},custom={},customStartup={},funcStartup={},flag={1:True},
            conditions={1:'return(c_time_after(12) )'},
            actions={1:'a_set_flag_value("DCSR_AUTHORED_1_READY", 73);a_out_text_delay(getValueDictByKey("DictKey_brief"), 15, false, 0); mission.trig.func[1]=nil;'},
            func={1:'if mission.trig.conditions[1]() then mission.trig.actions[1]() end'})
        self.write();self.assertTrue(self.prepare()['preservation']['restored_structure_equals_source'])
        self.m['trig']['events']={1:'arbitrary()'};self.write()
        with self.assertRaisesRegex(ValueError,'Unknown compiled trigger table'):self.prepare('event')

    def playback(self,player=12,source_hash=None,livery='Blue Angels Jet Team',installed='Blue Angels Jet Team'):
        first=[0.0]*50;first[1:4]=[100,1800,200];first[8:11]=[140,0,0]
        metadata=dict(authored_source_sha256=source_hash or a.sha(self.source.read_bytes()),source='unit 11',
                      livery=livery,aircraft='FA-18C_hornet',capture_build=a.BUILD,duration=8.7,
                      exterior_available=True,engine_available=True,lights_available=True,canopy_available=True,wheels_available=True)
        return a.playback_entries(self.source,11,player,metadata,first,dict(fx=1,fz=0),'DCSRecorder-Hornet',42,livery_name=installed)

    def test_playback_retains_player_start_and_all_unselected_content(self):
        before=copy.deepcopy(a.selected(self.m,12)['group'])
        blob,entries,mission,manifest=self.playback()
        after=copy.deepcopy(a.selected(mission,12)['group'])
        after['units'][1]['skill']='High'
        self.assertEqual(after,before)
        lead=next(r['unit'] for r in a.aircraft(mission) if r['unit']['unitId']==11)
        self.assertEqual((lead['x'],lead['alt'],lead['y']),(100,1800,200))
        self.assertEqual(lead['name'],'unit 11')
        self.assertTrue(manifest['preservation']['restored_structure_equals_source'])
        self.assertEqual(a.packed(entries),a.packed(self.playback()[1]))

    def test_playback_requires_other_player_and_exact_source(self):
        with self.assertRaisesRegex(ValueError,'different stock Hornet'):self.playback(player=11)
        with self.assertRaisesRegex(ValueError,'exact authored source'):self.playback(source_hash='wrong')
        with self.assertRaisesRegex(ValueError,'missing'):self.playback(player=99)

    def test_playback_owns_only_allocated_indices_flags_and_marker(self):
        rule=dict(comment='Authored flag',predicate='triggerOnce',rules={1:dict(predicate='c_flag_is_true',flag='DCSR_AUTHORED_2_CLEANUP')},
                  actions={1:dict(predicate='a_set_flag_value',flag='73',value=1)})
        self.m['trigrules']={9:rule}
        for field,value in a.compiled_trigger(9,rule).items():self.m['trig'][field]={9:value}
        self.write();_,entries,mission,manifest=self.playback()
        namespace,indices=manifest['namespace'],manifest['trigger_indices']
        self.assertEqual((namespace,indices),('DCSR_AUTHORED_3',[10,11]))
        self.assertEqual(mission['trigrules'][9],rule)
        for field,values in mission['trig'].items():
            self.assertEqual({k:v for k,v in values.items() if k not in indices},self.m['trig'].get(field,{}),field)
        for i in indices:
            self.assertIn(i,mission['trigrules'])
            for field in ('actions','conditions','flag'):self.assertIn(i,mission['trig'][field])
        flags=[item.get('flag') for i in indices for item in mission['trigrules'][i]['rules'].values()]
        self.assertTrue(all(f.startswith(namespace+'_') for f in flags))
        self.assertEqual(manifest['preservation']['added_members'],[a.MARKER])
        self.assertEqual(sorted(r['unit']['unitId'] for r in a.aircraft(mission)),sorted(r['unit']['unitId'] for r in a.aircraft(self.m)))

    def test_mission_editor_lowercase_livery_is_the_same_livery(self):
        # Mission Editor 2.9.30 saved a newly added Blue Angels Hornet as 'blue angels jet team'.
        for uid in (11,12):a.selected(self.m,uid)['unit']['livery_id']='blue angels jet team'
        self.write();_,_,mission,manifest=self.playback()
        self.assertEqual(a.selected_row(mission,11)['unit']['livery_id'],'Blue Angels Jet Team')  # module's installed name
        self.assertEqual(a.selected_row(mission,12)['unit']['livery_id'],'blue angels jet team')  # player untouched
        self.assertTrue(manifest['preservation']['restored_structure_equals_source'])

    def test_recorded_livery_plays_back_and_player_livery_is_free(self):
        a.selected(self.m,11)['unit']['livery_id']='vfa-37';a.selected(self.m,12)['unit']['livery_id']='default';self.write()
        _,_,mission,_=self.playback(livery='VFA-37',installed='VFA-37')
        self.assertEqual(a.selected_row(mission,11)['unit']['livery_id'],'VFA-37')
        self.assertEqual(a.selected_row(mission,12)['unit']['livery_id'],'default')
        with self.assertRaisesRegex(ValueError,'configuration differs'):self.playback(livery='Blue Angels Jet Team')

    def test_find_livery_prefers_user_copy_and_refuses_missing(self):
        root=Path(self.tmp.name);dcs,saved=root/'dcs',root/'games'
        stock=dcs/'CoreMods/aircraft/FA-18C/Liveries/FA-18C_hornet';stock.mkdir(parents=True)
        (stock/'VFA-37.zip').write_bytes(b'zip');(stock/'Blue Angels Jet Team.zip').write_bytes(b'zip')
        user=saved/'Liveries/FA-18C_hornet/vfa-37';user.mkdir(parents=True)
        self.assertEqual(a.find_livery('VFA-37',dcs,saved),user)
        self.assertEqual(a.find_livery('blue angels jet team',dcs,saved),stock/'Blue Angels Jet Team.zip')
        with self.assertRaisesRegex(ValueError,'"Thunderbirds" was not found'):a.find_livery('Thunderbirds',dcs,saved)
        # Installed DCS modules (campaigns) carry their own Hornet liveries, in any folder case.
        campaign=dcs/'Mods/campaigns/FA-18C Raven One/Liveries/fa-18c_hornet';campaign.mkdir(parents=True)
        (campaign/'VFA-64 400 CAG.zip').write_bytes(b'zip')
        self.assertEqual(a.find_livery('vfa-64 400 cag',dcs,saved),campaign/'VFA-64 400 CAG.zip')
        (campaign/'VFA-37.zip').write_bytes(b'zip')  # an earlier level (here the user's copy) still wins
        self.assertEqual(a.find_livery('VFA-37',dcs,saved),user)
        other=dcs/'Mods/campaigns/Another/Liveries/FA-18C_hornet';other.mkdir(parents=True)
        (other/'VFA-64 400 CAG.zip').write_bytes(b'zip')
        with self.assertRaisesRegex(ValueError,'"vfa-64 400 cag" exists more than once'):a.find_livery('vfa-64 400 cag',dcs,saved)

    def test_library_never_routes_authored_take_to_fixed_donor(self):
        from library import Library
        lib=Library(dict(saved_games=str(self.root/'saved'),build_trial=a.BUILD),running=lambda:False)
        with patch.object(lib,'source',return_value=self.source),patch.object(lib,'validate',return_value={'authored_source_sha256':'example'}),patch.object(lib,'activate') as activate:
            with self.assertRaisesRegex(ValueError,'authored scene'):lib.playback('take.csv')
            activate.assert_not_called()

if __name__=='__main__':unittest.main()
