from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parent
package=root/'corrected-package'
relative='Mods/aircraft/DCSRecorder-Hornet-Ground-Test/bin/HornetGroundProbe.dll'
shutil.copy2(root.parent/'ground-build/Release/HornetGroundProbe.dll',package/'payload'/relative)
manifest=json.loads((package/'manifest.json').read_text())
manifest['files'][relative]=hashlib.sha256((package/'payload'/relative).read_bytes()).hexdigest()
manifest['status']='Reference repair verified against captured loaded mission; read-only pose tracing added; live ground hold still unverified'
manifest['pose_trace']=json.loads((root/'trace-source.json').read_text())
(package/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
shutil.copy2(root.parent/'ground-build/Testing/Temporary/LastTest.log',package/'native-tests.log')
print('Updated package manifest for reference repair and read-only ground pose tracing')
