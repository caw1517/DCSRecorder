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
        with self.assertRaisesRegex(ValueError,'unsupported task'):self.prepare()
        self.assertFalse((self.root/'out').exists())

    def test_unknown_script_and_compiled_only_code_are_refused(self):
        self.m['trigrules']={1:dict(comment='Authored dynamic',predicate='triggerStart',rules={},actions={1:dict(predicate='a_do_script',text='arbitrary()')})};self.write()
        with self.assertRaisesRegex(ValueError,'unclassified behavior'):self.prepare()
        self.m['trigrules']={};self.m['trig']={'actions':{1:'arbitrary()'}};self.write()
        with self.assertRaisesRegex(ValueError,'indices differ'):self.prepare()

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

    def playback(self,player=12,source_hash=None):
        first=[0.0]*50;first[1:4]=[100,1800,200];first[8:11]=[140,0,0]
        metadata=dict(authored_source_sha256=source_hash or a.sha(self.source.read_bytes()),source='unit 11',
                      livery='Blue Angels Jet Team',aircraft='FA-18C_hornet',capture_build=a.BUILD,duration=8.7,
                      exterior_available=True,engine_available=True,lights_available=True,canopy_available=True,wheels_available=True)
        return a.playback_entries(self.source,11,player,metadata,first,dict(fx=1,fz=0),'DCSRecorder-Hornet-Authored-Test',42)

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

    def test_mission_editor_lowercase_livery_is_the_same_livery(self):
        # Mission Editor 2.9.30 saved a newly added Blue Angels Hornet as 'blue angels jet team'.
        for uid in (11,12):a.selected(self.m,uid)['unit']['livery_id']='blue angels jet team'
        self.write();_,_,mission,manifest=self.playback()
        self.assertEqual(a.selected_row(mission,11)['unit']['livery_id'],'Blue Angels Jet Team')  # module's installed name
        self.assertEqual(a.selected_row(mission,12)['unit']['livery_id'],'blue angels jet team')  # player untouched
        self.assertTrue(manifest['preservation']['restored_structure_equals_source'])
        a.selected(self.m,12)['unit']['livery_id']='default';self.write()
        with self.assertRaisesRegex(ValueError,'Blue Angels Jet Team livery'):self.playback()

    def test_library_never_routes_authored_take_to_fixed_donor(self):
        from library import Library
        lib=Library(dict(saved_games=str(self.root/'saved'),build_trial=a.BUILD),running=lambda:False)
        with patch.object(lib,'source',return_value=self.source),patch.object(lib,'validate',return_value={'authored_source_sha256':'example'}),patch.object(lib,'activate') as activate:
            with self.assertRaisesRegex(ValueError,'authored scene'):lib.playback('take.csv')
            activate.assert_not_called()

if __name__=='__main__':unittest.main()
