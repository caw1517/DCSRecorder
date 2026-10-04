"""Retain the validated correction and remove temporary source instrumentation."""
from pathlib import Path
import re

root=Path(r'C:\Users\w_can\.codex\worktrees\airborne-staging\DCS_Recorder\experiments\efm-ownership')
evidence=Path(__file__).resolve().parent
source=root/'object_probe.cpp'
text=source.read_text()
text,count=re.subn(r'#ifdef DCS_POSE_DIAGNOSTICS\n.*?#endif\n','',text,flags=re.S)
assert count==4,count
text=text.replace('DCS_SUPPRESS_PRESENTATION_PITCH','HORNET_STAGED_PROTOTYPE')
text=text.replace('"[DEBUG-nose],"','"presentation_restore_error,"')
assert 'DEBUG-nose' not in text and 'DCS_POSE_DIAGNOSTICS' not in text
cmake=root/'CMakeLists.txt'
config=cmake.read_text()
begin=config.index('# Temporary read-only attitude investigation;')
end=config.index('add_executable(presentation_pitch_check',begin)
config=config[:begin]+config[end:]
header=root/'native_presentation_pitch.h'
content=header.read_text().replace('Build-specific staged-playback experiment.','Build-specific staged recorded playback.')
temporary=root/'pose_diagnostics.h'
archive=evidence/'diagnostic-source'
archive.mkdir(exist_ok=True)
archived=archive/temporary.name
assert not archived.exists()
archived.write_bytes(temporary.read_bytes())
source.write_text(text)
cmake.write_text(config)
header.write_text(content)
temporary.unlink()
print('Correction now applies to staged playback by default; temporary diagnostic source archived outside the build.')
