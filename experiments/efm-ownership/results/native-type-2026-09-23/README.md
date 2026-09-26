# Native aircraft type confirmed

Fresh DCS process 7300, log opened 2026-09-24 03:12:09 UTC. The same-run ID map links Probe mission ID 9001 to runtime ID 16777472 and Observer mission ID 2 to runtime ID 16777728. The native-type record identifies object 16777472.

The inspector returned `status=ok`, with dynamic type **woAIPlane**, owned by **DCS.exe**. Its class hierarchy includes:

`woAIPlane -> woAILA -> woPlane -> woLA -> woLABase -> IwoLA`

The `Registered` and `MovingObject` bases are both at displacement **8 bytes** from the complete object in this build. The callback subobject offset is also 8. This establishes the relation between the supplied base handle and the complete AI aircraft object; it does not establish any flight-model member offset.

Other reported bases include `Graphics::ModelInstance`, `ISceneObject`, `LinkHost`, `IwNetObject`, `wAttributeOwner`, `Suicide` and `wDetectable`. No flight-model or DynamicBody base appears. A physics object could be owned through a member or another relationship; base-class metadata does not reveal that relationship.

The independently observed AI and player aircraft ran through 14.1 seconds. Evidence retained: native-types.txt, objects.csv and dcs-excerpt.txt. The DLL hash remained 1A4EE29E4DB41FBF3BA454B5821D16E2F460333633950D3C3002A4F57FC22EAF.

**Next:** offline current-build analysis of woAIPlane/woAILA/woPlane and their connection to the actual AI flight model. No repeat type-identification flight is needed. No native physics method was invoked, and no force or pose authority is established. The observed class layout is build-specific and must not be generalized across DCS updates.
