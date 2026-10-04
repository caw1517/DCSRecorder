from pathlib import Path
import shutil,json,hashlib
root=Path(__file__).resolve().parent
work=root.parent
package=root/'package-v3'
shutil.copytree(work/'ground-readiness-failure/corrected-package',package,dirs_exist_ok=True)
relative='Mods/aircraft/DCSRecorder-Hornet-Ground-Test/bin/HornetGroundProbe.dll'
shutil.copy2(work/'ground-build/Release/HornetGroundProbe.dll',package/'payload'/relative)
manifest=json.loads((package/'manifest.json').read_text())
manifest['files'][relative]=hashlib.sha256((package/'payload'/relative).read_bytes()).hexdigest()
manifest['status']='Ground pre-integration pose restore built and offline checked; live hold and release pending'
manifest['pose_boundary_repair']={
 'evidence':'Both live mission starts in ground-pose-26844.csv show a pose replacement between SDK apply and before_step, surviving after_step and after_animation; held error reaches 0.109632271 m.',
 'change':'Ground-only: reapply same recorded pose and motion at before_step with all native_motion guards; consume existing pending SDK tick once; publish failure if any step guard fails.',
 'regression':'check_held_pose.py fails on retained original trace; only a new live trace can establish repair success.',
 'source_sha256':hashlib.sha256((work/'ground-code/object_probe.cpp').read_bytes()).hexdigest()
}
(package/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
shutil.copy2(work/'ground-build/Testing/Temporary/LastTest.log',package/'native-tests.log')
for rel,digest in manifest['files'].items():
 assert hashlib.sha256((package/'payload'/rel).read_bytes()).hexdigest()==digest,rel
print('Prepared package-v3; all',len(manifest['files']),'payload digests verified')
