// Compile the locally installed ED sample; no SDK source is redistributed.
#ifdef ENGINE_SOUND_TRACE
#define ed_fm_get_param engine_sample_get_param
#endif
#define ed_fm_simulate sample_simulate
#define ed_fm_set_current_state sample_set_current_state
#define ed_fm_hot_start_in_air sample_hot_start_in_air
#define ed_fm_hot_start sample_hot_start
#define ed_fm_cold_start sample_cold_start
#define ed_fm_add_global_force sample_add_global_force
#define ed_fm_add_global_moment sample_add_global_moment
#include "ED_FM_Template.cpp"
#ifdef ENGINE_SOUND_TRACE
#undef ed_fm_get_param
#endif
#undef ed_fm_simulate
#undef ed_fm_set_current_state
#undef ed_fm_hot_start_in_air
#undef ed_fm_hot_start
#undef ed_fm_cold_start
#undef ed_fm_add_global_force
#undef ed_fm_add_global_moment
#include <filesystem>
#include <fstream>
#include <iomanip>

namespace {
double elapsed = 0, next_log = 0;
unsigned long long calls = 0, states = 0, run = 0;
double position[3]{}, quaternion[4]{};
std::ofstream output;
void open_log() {
    if (output.is_open()) return;
    HMODULE module = nullptr;
    GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
        GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        reinterpret_cast<LPCWSTR>(&open_log), &module);
    wchar_t path[32768]{};
    if (!GetModuleFileNameW(module, path, 32768)) return;
    auto folder = std::filesystem::path(path).parent_path() / "probe-logs";
    std::error_code error;
    std::filesystem::create_directories(folder, error);
    if (error) return;
    auto name = "callbacks-" + std::to_string(GetCurrentProcessId()) + "-" +
        std::to_string(GetTickCount64()) + ".csv";
    output.open(folder / name);
    output << "run,event,sim_seconds,simulate_calls,state_calls,x,y,z,qx,qy,qz,qw,pulse_nm\n";
    output << std::setprecision(12);
}
void record(const char* event, double pulse = 0) {
    open_log();
    if (!output) return;
    output << run << ',' << event << ',' << elapsed << ',' << calls << ',' << states;
    for (double v : position) output << ',' << v;
    for (double v : quaternion) output << ',' << v;
    output << ',' << pulse << '\n';
    output.flush();
}
void reset(const char* kind) {
    elapsed = next_log = 0; calls = states = 0; ++run;
    throttle = stick_roll = stick_pitch = 0;
    record(kind);
}
}

extern "C" __declspec(dllexport) void ed_fm_hot_start_in_air() {
    sample_hot_start_in_air(); reset("hot_air");
}
extern "C" __declspec(dllexport) void ed_fm_hot_start() {
    sample_hot_start(); reset("hot_ground");
}
extern "C" __declspec(dllexport) void ed_fm_cold_start() {
    sample_cold_start(); reset("cold");
}
extern "C" __declspec(dllexport) void ed_fm_release() {
    record("release"); output.close();
}
extern "C" __declspec(dllexport) void ed_fm_set_current_state(
    double ax,double ay,double az,double vx,double vy,double vz,
    double px,double py,double pz,double ox,double oy,double oz,
    double wx,double wy,double wz,double qx,double qy,double qz,double qw) {
    sample_set_current_state(ax,ay,az,vx,vy,vz,px,py,pz,ox,oy,oz,wx,wy,wz,qx,qy,qz,qw);
    position[0]=px; position[1]=py; position[2]=pz;
    quaternion[0]=qx; quaternion[1]=qy; quaternion[2]=qz; quaternion[3]=qw;
    ++states;
}
extern "C" __declspec(dllexport) void ed_fm_simulate(double dt) {
    if (!std::isfinite(dt) || dt <= 0) return;
    sample_simulate(dt);
    // Average over the step for a bounded 2000 N*m*s impulse even at boundary crossings.
    const double overlap = std::max(0.0, std::min(elapsed+dt, 5.5)-std::max(elapsed,5.0));
#ifdef LAYOUT_READ_ONLY
    const double pulse = 0;
#else
    const double pulse = 4000.0 * overlap / dt;
#endif
    common_moment.x += pulse;
    elapsed += dt; ++calls;
    if (elapsed >= next_log) { record("simulate", pulse); next_log = elapsed + 0.05; }
}
// The sample leaves these output references untouched; explicitly supply zero.
extern "C" __declspec(dllexport) void ed_fm_add_global_force(
    double& x,double& y,double& z,double& px,double& py,double& pz) {
    x=y=z=px=py=pz=0;
}
extern "C" __declspec(dllexport) void ed_fm_add_global_moment(double& x,double& y,double& z) {
    x=y=z=0;
}
