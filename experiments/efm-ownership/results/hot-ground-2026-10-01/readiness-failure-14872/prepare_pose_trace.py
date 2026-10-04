from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
repo=Path('E:/Projects/DCS_Recorder/experiments/efm-ownership')
source=repo/'object_probe.cpp'
text=source.read_text(encoding='utf-8')
(root/'object_probe-before.cpp').write_text(text,encoding='utf-8')
def replace(old,new):
    global text
    assert text.count(old)==1,old
    text=text.replace(old,new)
replace('std::ofstream motion_file;', '''std::ofstream motion_file;
#ifdef HORNET_GROUND_PROTOTYPE
std::ofstream ground_pose_file;
#endif''')
replace('void after_native_animation(const void* handle) {', '''#ifdef HORNET_GROUND_PROTOTYPE
// Read-only boundary evidence: distinguish native integration from animation
// or later pose replacement. No extra pose/velocity writes are performed.
void trace_ground_pose(const char* phase,const void* handle,const Observation& state) {
    if(state.path.samples.empty() || !ground_pose_file)return;
    std::array<float,16> pose{};std::array<double,3> precise{};
    const auto object=reinterpret_cast<uintptr_t>(handle);
    const bool readable=native_identity::read(object+0x174,pose) && native_identity::read(object+0x1c8,precise);
    const auto target=state.path.at_sample(state.clock.elapsed);
    ground_pose_file<<phase<<','<<state.runtime_id<<','<<state.calls<<','<<state.step_calls<<','
        <<state.clock.last<<','<<state.clock.elapsed<<','<<readable;
    for(double v:target.p)ground_pose_file<<','<<v;
    for(double v:precise)ground_pose_file<<','<<v;
    for(int k=0;k<3;++k)ground_pose_file<<','<<pose[12+k];
    ground_pose_file<<'\\n';ground_pose_file.flush();
}
void after_ground_native_step(const void* handle) {
    std::lock_guard<std::mutex> guard(lock);
    const auto key=reinterpret_cast<ED_OBJECT_HANDLE>(const_cast<void*>(handle));
    const auto it=observed.find(key);
    if(it!=observed.end() && it->second.motion_active)trace_ground_pose("after_step",handle,it->second);
}
#endif
void after_native_animation(const void* handle) {''')
replace('    const auto view=api->ed_get_object_args(sdk_handle);', '''#ifdef HORNET_GROUND_PROTOTYPE
    trace_ground_pose("after_animation",handle,state);
#endif
    const auto view=api->ed_get_object_args(sdk_handle);''')
replace('    state.step_pending=false; // A missing SDK callback cannot leave a stale override running.', '''#ifdef HORNET_GROUND_PROTOTYPE
    trace_ground_pose("before_step",handle,state);
#endif
    state.step_pending=false; // A missing SDK callback cannot leave a stale override running.''')
replace('reinterpret_cast<native_step_hook::Step>(image+native_build::dcs(0x70fef0)),&before_native_step,nullptr,', '''reinterpret_cast<native_step_hook::Step>(image+native_build::dcs(0x70fef0)),&before_native_step,
#ifdef HORNET_GROUND_PROTOTYPE
            &after_ground_native_step,
#else
            nullptr,
#endif''')
replace('    motion_file << ",step_hook_calls,step_hook_applied,step_hook_status\\n" << std::setprecision(12);', '''    motion_file << ",step_hook_calls,step_hook_applied,step_hook_status\\n" << std::setprecision(12);
#ifdef HORNET_GROUND_PROTOTYPE
    ground_pose_file.open(folder/("ground-pose-"+std::to_string(GetCurrentProcessId())+".csv"));
    ground_pose_file<<"phase,id,call,step,model_time,replay_time,readable,target_x,target_y,target_z,precise_x,precise_y,precise_z,float_x,float_y,float_z\\n"<<std::setprecision(15);
#endif''')
replace('    ++state.calls;\n#ifdef HORNET_STAGED_PROTOTYPE', '''    ++state.calls;
#ifdef HORNET_GROUND_PROTOTYPE
    trace_ground_pose("sdk_entry",handle,state);
#endif
#ifdef HORNET_STAGED_PROTOTYPE''')
target=root.parent/'ground-code/object_probe.cpp'
target.write_text(text,encoding='utf-8')
(root/'trace-source.json').write_text(json.dumps(dict(before_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),after_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),scope='Read-only pose traces for ground build only'),indent=2))
print('Prepared ground-only read-only pose traces at SDK, integrator and animation boundaries')
