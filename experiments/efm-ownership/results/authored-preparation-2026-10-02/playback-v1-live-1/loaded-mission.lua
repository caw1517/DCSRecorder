mission = 
{
	["groundControl"] = 
	{
		["passwords"] = 
		{
			["artillery_commander"] = {},
			["instructor"] = {},
			["observer"] = {},
			["forward_observer"] = {},
		}, -- end of ["passwords"]
		["roles"] = 
		{
			["artillery_commander"] = 
			{
				["name"] = "GROUND FORCE CMD",
				["blue"] = 0,
				["neutrals"] = 0,
				["red"] = 0,
			}, -- end of ["artillery_commander"]
			["instructor"] = 
			{
				["name"] = "GAME MASTER",
				["blue"] = 0,
				["neutrals"] = 0,
				["red"] = 0,
			}, -- end of ["instructor"]
			["observer"] = 
			{
				["name"] = "OBSERVER",
				["blue"] = 0,
				["neutrals"] = 0,
				["red"] = 0,
			}, -- end of ["observer"]
			["forward_observer"] = 
			{
				["name"] = "JTAC",
				["blue"] = 0,
				["neutrals"] = 0,
				["red"] = 0,
			}, -- end of ["forward_observer"]
		}, -- end of ["roles"]
		["isPilotControlVehicles"] = false,
	}, -- end of ["groundControl"]
	["requiredModules"] = 
	{
		["DCSRecorder-Hornet-Authored-Test"] = "DCSRecorder-Hornet-Authored-Test",
	}, -- end of ["requiredModules"]
	["date"] = 
	{
		["Year"] = 2011,
		["Day"] = 1,
		["Month"] = 6,
	}, -- end of ["date"]
	["trig"] = 
	{
		["actions"] = 
		{
			[1] = "a_set_flag_value(\"DCSR_AUTHORED_1_READY\", 73);a_out_text_delay(getValueDictByKey(\"DictKey_AuthoredMessage\"), 15, false, 0);a_out_sound(getValueResourceByKey(\"ResKey_AuthoredChime\"), 0); mission.trig.func[1]=nil;",
			[2] = "a_set_command(816);a_do_script(\"DCSR_AUTHORED_2_CONFIG={\\\
[\\\"expected\\\"]={\\\
[21]=0.0,\\\
[38]=0.0,\\\
[0]=0.0,\\\
[3]=0.0,\\\
[5]=0.0,\\\
[9]=0.11533036083,\\\
[10]=0.115174889565,\\\
[11]=-0.000244275550358,\\\
[12]=0.000439658761024,\\\
[13]=0.139793604612,\\\
[14]=0.139793604612,\\\
[15]=0.0106101222336,\\\
[16]=0.0109763452783,\\\
[17]=0.00228146091104,\\\
[18]=0.00228149187751,\\\
[28]=0.0,\\\
[29]=0.0,\\\
[89]=0.0129789467901,\\\
[90]=0.0129725849256,\\\
[88]=0.0,\\\
[190]=0.0,\\\
[191]=0.0,\\\
[192]=0.0,\\\
[193]=0.0,\\\
[210]=0.0,\\\
[212]=0.0,\\\
[1]=0.0,\\\
[6]=0.0,\\\
[4]=0.0,\\\
[101]=1.0,\\\
[103]=1.0,\\\
[102]=1.0,\\\
[2]=-0.0,\\\
},\\\
[\\\"token_high\\\"]=0.798355758190155,\\\
[\\\"token_low\\\"]=0.6081656217575073,\\\
[\\\"duration\\\"]=22.62,\\\
[\\\"smoke_events\\\"]={\\\
[1]={\\\
[\\\"time\\\"]=0,\\\
[\\\"on\\\"]=false,\\\
},\\\
},\\\
}\\\
-- Bounded airborne integration. The installed user hook commits the native\\\
-- one-shot latch and dispatches Active Pause release in the same hook callback.\\\
local c=assert(DCSR_AUTHORED_2_CONFIG)\\\
local s={phase='preparing',held=true,started=timer.getTime(),smoke_index=0,last_replay=0}\\\
DCSR_AUTHORED_2=s\\\
local function emit(text)env.info('DCSR_AUTHORED_2 '..text)end\\\
local function notice(text)trigger.action.outText('Release test: '..text,15)end\\\
local function flag(name,value)trigger.action.setUserFlag(name,value)end\\\
local function lead()local u=Unit.getByName(\\\"Record Hornet\\\");return u and u:isExist() and u or nil end\\\
local function matched(u)\\\
    return math.abs(u:getDrawArgumentValue(997)-c.token_high)<1e-8 and\\\
        math.abs(u:getDrawArgumentValue(998)-c.token_low)<1e-8\\\
end\\\
local function initial(u)\\\
    if not matched(u) or u:getDrawArgumentValue(999)~=.125 or u:getDrawArgumentValue(996)~=0 then return false end\\\
    for index,value in pairs(c.expected)do\\\
        local actual=u:getDrawArgumentValue(index)\\\
        if actual~=actual or math.abs(actual-value)>0.000001 then return false end\\\
    end\\\
    return true\\\
end\\\
function s.fail(reason)\\\
    if s.phase=='failed' or s.phase=='complete' then return end\\\
    s.phase='failed';flag('DCSR_AUTHORED_2_PENDING',0)\\\
    local u=lead();if u then u:destroy()end\\\
    if s.held then flag('DCSR_AUTHORED_2_CLEANUP',1)end\\\
    emit('FAILED,'..tostring(reason));notice('FAILED: '..tostring(reason)..'. Exit normally and retain logs.')\\\
end\\\
function s.cleaned()s.held=false;emit('HOLD_CLEANED')end\\\
function s.arm(session,generation)\\\
    if s.phase~='preparing' and s.phase~='waiting' then return false end\\\
    local u=lead()\\\
    if not u or not initial(u) or type(session)~='string' or not session:match('^[%w_]+$') or\\\
        type(generation)~='number' or generation<1 then return false end\\\
    s.session,s.generation=session,generation\\\
    if s.phase~='waiting' then\\\
        s.phase='waiting';emit('READY,'..session..','..generation)\\\
        notice('Ready. Inspect the held lead, then F10 > DCS Recorder playback > Start playback. Do not toggle Active Pause.')\\\
    end\\\
    return true\\\
end\\\
function s.released(session,generation)\\\
    if s.phase~='requested' or s.session~=session or s.generation~=generation then\\\
        s.fail('unexpected_release_ack');return false\\\
    end\\\
    s.held=false;flag('DCSR_AUTHORED_2_PENDING',0)\\\
    s.phase='starting';s.release_time=timer.getTime()\\\
    emit(string.format('PLAYER_RELEASED,%s,%d,%.9f',session,generation,s.release_time))\\\
    notice('Released. Watch first movement and smoke, then let the short recording finish.')\\\
    return true\\\
end\\\
local function sample(name)\\\
    local u=Unit.getByName(name);if not u or not u:isExist() then return end\\\
    local p,v=u:getPosition(),u:getVelocity();local values={}\\\
    for _,a in ipairs({0,3,5,9,10,11,12,13,14,15,16,17,18,21,38,88,190,191,192,193,210,212,1,6,4,101,103,102,2,89,90,28,29})do\\\
        values[#values+1]=string.format('%.9g',u:getDrawArgumentValue(a))\\\
    end\\\
    emit(string.format('SAMPLE,%s,%s,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9g,%s',\\\
        s.phase,name,timer.getTime(),p.p.x,p.p.y,p.p.z,p.x.x,p.x.y,p.x.z,p.y.x,p.y.y,p.y.z,\\\
        v.x,v.y,v.z,1000*u:getDrawArgumentValue(996),u:getDrawArgumentValue(999),table.concat(values,',')))\\\
end\\\
local function smoke(u)\\\
    local elapsed=1000*u:getDrawArgumentValue(996)\\\
    assert(elapsed==elapsed and elapsed>=s.last_replay and elapsed<=c.duration+.1,'invalid_replay_clock')\\\
    s.last_replay=elapsed\\\
    while c.smoke_events[s.smoke_index+1] and c.smoke_events[s.smoke_index+1].time<=elapsed do\\\
        s.smoke_index=s.smoke_index+1\\\
    end\\\
    local desired=assert(c.smoke_events[s.smoke_index])\\\
    if desired.on~=s.smoke_on then\\\
        u:getController():setCommand({id='SMOKE_ON_OFF',params={value=desired.on}})\\\
        s.smoke_on=desired.on\\\
        emit(string.format('SMOKE,%.9f,%.9f,%d',timer.getTime(),elapsed,desired.on and 1 or 0))\\\
    end\\\
end\\\
local function tick()\\\
    if s.phase=='failed' or s.phase=='complete' then return end\\\
    local now=timer.getTime();local u=lead()\\\
    if not u then s.fail('missing_aircraft');return end\\\
    local status=u:getDrawArgumentValue(999)\\\
    if status~=0 and (not matched(u) or status==.75) then s.fail('native_readiness_lost');return end\\\
    if s.phase=='preparing' then\\\
        if matched(u) and status==.125 then\\\
            if not initial(u) then s.fail('snapshot_mismatch');return end\\\
            smoke(u)\\\
        end\\\
        if now-s.started>10 then s.fail('bridge_or_native_readiness_timeout');return end\\\
    elseif s.phase=='waiting' or s.phase=='countdown' then\\\
        if not initial(u) then s.fail('initial_state_not_retained');return end\\\
        smoke(u)\\\
    elseif s.phase=='requested' then\\\
        if now-s.request_time>1 then s.fail('release_ack_timeout');return end\\\
    elseif s.phase=='starting' or s.phase=='playing' then\\\
        if status==.25 then\\\
            if s.phase=='starting' then s.phase='playing';emit(string.format('NATIVE_RUNNING,%.9f,%.9f',now,1000*u:getDrawArgumentValue(996)))end\\\
            smoke(u)\\\
        elseif status==.5 and s.phase=='playing' then\\\
            smoke(u);sample(\\\"Wing Hornet\\\");sample(\\\"Record Hornet\\\");u:destroy();s.phase='complete'\\\
            emit('COMPLETE');notice('Recording ended. Report first movement, smoke onset, and any jump or sound change. Exit normally.');return\\\
        elseif s.phase=='playing' or now-s.release_time>1 then s.fail('native_release_not_confirmed');return end\\\
        if now-s.release_time>c.duration+2 then s.fail('completion_timeout');return end\\\
    end\\\
    sample(\\\"Wing Hornet\\\");sample(\\\"Record Hornet\\\")\\\
    return now+.02\\\
end\\\
local function checked_tick()\\\
    local ok,next_time=pcall(tick)\\\
    if not ok then s.fail(next_time);return end\\\
    return next_time\\\
end\\\
local function start()\\\
    if s.phase~='waiting' then emit('START_REFUSED,'..s.phase);notice('Start unavailable: '..s.phase..'.');return end\\\
    local u=lead();if not u or not initial(u) then s.fail('not_ready');return end\\\
    s.phase='countdown';s.countdown_time=timer.getTime();emit(string.format('COUNTDOWN,%.9f',s.countdown_time))\\\
    notice('Starting in 3. Do not toggle Active Pause.')\\\
    local remaining=3\\\
    timer.scheduleFunction(function()\\\
        if s.phase~='countdown' then return end\\\
        remaining=remaining-1\\\
        if remaining>0 then notice('Starting in '..remaining..'.');return timer.getTime()+1 end\\\
        local current=lead()\\\
        if not current or not initial(current) then s.fail('not_ready_at_release');return end\\\
        s.phase='requested';s.request_time=timer.getTime();flag('DCSR_AUTHORED_2_PENDING',1)\\\
        emit(string.format('REQUEST,%s,%d,%.9f',s.session,s.generation,s.request_time))\\\
    end,nil,s.countdown_time+1)\\\
end\\\
local menu=missionCommands.addSubMenu('DCS Recorder playback')\\\
missionCommands.addCommand('Start playback (3-second countdown)',menu,start)\\\
missionCommands.addCommand('Show status',menu,function()notice(s.phase)end)\\\
flag('DCSR_AUTHORED_2_PENDING',0);flag('DCSR_AUTHORED_2_CLEANUP',0)\\\
emit('INITIALIZED');notice('Player held. Waiting for the complete snapshot and release bridge.')\\\
checked_tick()\\\
if s.phase~='failed' then timer.scheduleFunction(checked_tick,nil,timer.getTime()+.02)end\\\
\");",
			[3] = "a_set_command(816);a_do_script(\"DCSR_AUTHORED_2.cleaned()\"); mission.trig.func[3]=nil;",
		}, -- end of ["actions"]
		["events"] = {},
		["custom"] = {},
		["func"] = 
		{
			[1] = "if mission.trig.conditions[1]() then mission.trig.actions[1]() end",
			[3] = "if mission.trig.conditions[3]() then mission.trig.actions[3]() end",
		}, -- end of ["func"]
		["flag"] = 
		{
			[1] = true,
			[2] = true,
			[3] = true,
		}, -- end of ["flag"]
		["conditions"] = 
		{
			[1] = "return(c_time_after(12) )",
			[2] = "return(true)",
			[3] = "return(c_flag_is_true(\"DCSR_AUTHORED_2_CLEANUP\") )",
		}, -- end of ["conditions"]
		["customStartup"] = {},
		["funcStartup"] = 
		{
			[2] = "if mission.trig.conditions[2]() then mission.trig.actions[2]() end",
		}, -- end of ["funcStartup"]
	}, -- end of ["trig"]
	["maxDictId"] = 15000,
	["result"] = 
	{
		["offline"] = 
		{
			["conditions"] = {},
			["actions"] = {},
			["func"] = {},
		}, -- end of ["offline"]
		["total"] = 0,
		["blue"] = 
		{
			["conditions"] = {},
			["actions"] = {},
			["func"] = {},
		}, -- end of ["blue"]
		["red"] = 
		{
			["conditions"] = {},
			["actions"] = {},
			["func"] = {},
		}, -- end of ["red"]
	}, -- end of ["result"]
	["pictureFileNameN"] = {},
	["descriptionNeutralsTask"] = "DictKey_descriptionNeutralsTask_7",
	["pictureFileNameServer"] = {},
	["weather"] = 
	{
		["wind"] = 
		{
			["at8000"] = 
			{
				["speed"] = 0,
				["dir"] = 298,
			}, -- end of ["at8000"]
			["at2000"] = 
			{
				["speed"] = 0,
				["dir"] = 291,
			}, -- end of ["at2000"]
			["atGround"] = 
			{
				["speed"] = 0,
				["dir"] = 291,
			}, -- end of ["atGround"]
		}, -- end of ["wind"]
		["enable_fog"] = false,
		["season"] = 
		{
			["temperature"] = 15,
		}, -- end of ["season"]
		["qnh"] = 760,
		["cyclones"] = {},
		["dust_density"] = 0,
		["enable_dust"] = false,
		["clouds"] = 
		{
			["density"] = 6,
			["thickness"] = 200,
			["preset"] = "Preset3",
			["base"] = 2500,
			["iprecptns"] = 0,
		}, -- end of ["clouds"]
		["atmosphere_type"] = 0,
		["groundTurbulence"] = 0,
		["halo"] = 
		{
			["preset"] = "off",
		}, -- end of ["halo"]
		["type_weather"] = 0,
		["modifiedTime"] = true,
		["name"] = "Winter, clean sky",
		["fog"] = 
		{
			["thickness"] = 0,
			["visibility"] = 25,
		}, -- end of ["fog"]
		["visibility"] = 
		{
			["distance"] = 80000,
		}, -- end of ["visibility"]
		["sea"] = 
		{
			["mode"] = 1,
		}, -- end of ["sea"]
	}, -- end of ["weather"]
	["theatre"] = "Caucasus",
	["triggers"] = 
	{
		["zones"] = 
		{
			[1] = 
			{
				["radius"] = 100,
				["zoneId"] = 13001,
				["color"] = 
				{
					[1] = 1,
					[2] = 1,
					[3] = 1,
					[4] = 0.15,
				}, -- end of ["color"]
				["properties"] = 
				{
					[1] = 
					{
						["key"] = "",
						["value"] = "",
					}, -- end of [1]
				}, -- end of ["properties"]
				["hidden"] = false,
				["y"] = 891900,
				["x"] = -315050,
				["name"] = "Authored reference zone",
				["heading"] = 0,
				["type"] = 0,
			}, -- end of [1]
		}, -- end of ["zones"]
	}, -- end of ["triggers"]
	["map"] = 
	{
		["centerY"] = 898053.42857143,
		["zoom"] = 121000,
		["centerX"] = -316341,
	}, -- end of ["map"]
	["coalitions"] = 
	{
		["neutrals"] = 
		{
			[1] = 7,
			[2] = 17,
			[3] = 22,
			[4] = 23,
			[5] = 24,
			[6] = 25,
			[7] = 26,
			[8] = 27,
			[9] = 28,
			[10] = 29,
			[11] = 30,
			[12] = 31,
			[13] = 32,
			[14] = 33,
			[15] = 34,
			[16] = 35,
			[17] = 36,
			[18] = 37,
			[19] = 38,
			[20] = 39,
			[21] = 40,
			[22] = 41,
			[23] = 42,
			[24] = 43,
			[25] = 44,
			[26] = 45,
			[27] = 46,
			[28] = 47,
			[29] = 48,
			[30] = 49,
			[31] = 50,
			[32] = 51,
			[33] = 52,
			[34] = 53,
			[35] = 54,
			[36] = 55,
			[37] = 56,
			[38] = 57,
			[39] = 58,
			[40] = 59,
			[41] = 60,
			[42] = 61,
			[43] = 62,
			[44] = 63,
			[45] = 64,
			[46] = 65,
			[47] = 66,
			[48] = 67,
			[49] = 68,
			[50] = 69,
			[51] = 70,
			[52] = 71,
			[53] = 72,
			[54] = 73,
			[55] = 74,
			[56] = 75,
			[57] = 76,
			[58] = 77,
			[59] = 78,
			[60] = 79,
			[61] = 80,
			[62] = 81,
			[63] = 82,
			[64] = 83,
			[65] = 84,
			[66] = 85,
			[67] = 86,
			[68] = 87,
			[69] = 88,
			[70] = 89,
			[71] = 90,
			[72] = 91,
			[73] = 92,
		}, -- end of ["neutrals"]
		["blue"] = 
		{
			[1] = 21,
			[2] = 11,
			[3] = 4,
			[4] = 6,
			[5] = 16,
			[6] = 13,
			[7] = 15,
			[8] = 9,
			[9] = 20,
			[10] = 8,
			[11] = 10,
			[12] = 12,
			[13] = 2,
			[14] = 3,
			[15] = 5,
		}, -- end of ["blue"]
		["red"] = 
		{
			[1] = 18,
			[2] = 0,
			[3] = 1,
			[4] = 19,
		}, -- end of ["red"]
	}, -- end of ["coalitions"]
	["descriptionText"] = "DictKey_AuthoredBriefing",
	["pictureFileNameR"] = {},
	["descriptionBlueTask"] = "DictKey_AuthoredTask",
	["goals"] = {},
	["descriptionRedTask"] = "DictKey_descriptionRedTask_5",
	["pictureFileNameB"] = 
	{
		[1] = "ResKey_ImageBriefing_1",
	}, -- end of ["pictureFileNameB"]
	["coalition"] = 
	{
		["neutrals"] = 
		{
			["bullseye"] = 
			{
				["y"] = 100,
				["x"] = 100,
			}, -- end of ["bullseye"]
			["nav_points"] = {},
			["name"] = "neutrals",
			["country"] = {},
		}, -- end of ["neutrals"]
		["blue"] = 
		{
			["bullseye"] = 
			{
				["y"] = 617414,
				["x"] = -291014,
			}, -- end of ["bullseye"]
			["nav_points"] = {},
			["name"] = "blue",
			["country"] = 
			{
				[1] = 
				{
					["name"] = "USA",
					["id"] = 2,
					["vehicle"] = 
					{
						["group"] = 
						{
							[1] = 
							{
								["visible"] = false,
								["tasks"] = {},
								["uncontrollable"] = false,
								["task"] = "Ground Nothing",
								["taskSelected"] = true,
								["route"] = 
								{
									["points"] = 
									{
										[1] = 
										{
											["alt"] = 0,
											["type"] = "Turning Point",
											["ETA"] = 0,
											["alt_type"] = "BARO",
											["formation_template"] = "",
											["y"] = 891900,
											["x"] = -315050,
											["ETA_locked"] = true,
											["speed"] = 0,
											["action"] = "Off Road",
											["task"] = 
											{
												["id"] = "ComboTask",
												["params"] = 
												{
													["tasks"] = {},
												}, -- end of ["params"]
											}, -- end of ["task"]
											["speed_locked"] = true,
										}, -- end of [1]
									}, -- end of ["points"]
								}, -- end of ["route"]
								["groupId"] = 12401,
								["hidden"] = false,
								["units"] = 
								{
									[1] = 
									{
										["skill"] = "Average",
										["coldAtStart"] = false,
										["type"] = "M 818",
										["unitId"] = 12301,
										["y"] = 891900,
										["x"] = -315050,
										["name"] = "Authored reference truck",
										["heading"] = 0,
										["playerCanDrive"] = false,
									}, -- end of [1]
								}, -- end of ["units"]
								["y"] = 891900,
								["x"] = -315050,
								["name"] = "Authored trucks",
								["start_time"] = 0,
							}, -- end of [1]
						}, -- end of ["group"]
					}, -- end of ["vehicle"]
					["plane"] = 
					{
						["group"] = 
						{
							[1] = 
							{
								["lateActivation"] = false,
								["tasks"] = {},
								["radioSet"] = false,
								["task"] = "Nothing",
								["uncontrolled"] = false,
								["taskSelected"] = true,
								["route"] = 
								{
									["points"] = 
									{
										[1] = 
										{
											["alt"] = 1757.73476851,
											["action"] = "Turning Point",
											["alt_type"] = "BARO",
											["speed"] = 151.878246766,
											["task"] = 
											{
												["id"] = "ComboTask",
												["params"] = 
												{
													["tasks"] = {},
												}, -- end of ["params"]
											}, -- end of ["task"]
											["type"] = "Turning Point",
											["ETA"] = 0,
											["ETA_locked"] = true,
											["y"] = 892008.524296,
											["x"] = -312421.002171,
											["speed_locked"] = true,
										}, -- end of [1]
										[2] = 
										{
											["alt"] = 1800,
											["action"] = "Turning Point",
											["alt_type"] = "BARO",
											["speed"] = 140,
											["task"] = 
											{
												["id"] = "ComboTask",
												["params"] = 
												{
													["tasks"] = {},
												}, -- end of ["params"]
											}, -- end of ["task"]
											["type"] = "Turning Point",
											["ETA"] = 214.28571428571,
											["ETA_locked"] = false,
											["y"] = 892000,
											["x"] = -285000,
											["speed_locked"] = true,
										}, -- end of [2]
									}, -- end of ["points"]
								}, -- end of ["route"]
								["groupId"] = 12101,
								["hidden"] = false,
								["units"] = 
								{
									[1] = 
									{
										["alt"] = 1757.73476851,
										["hardpoint_racks"] = true,
										["alt_type"] = "BARO",
										["livery_id"] = "Blue Angels Jet Team",
										["skill"] = "High",
										["speed"] = 151.878246766,
										["AddPropAircraft"] = 
										{
											["HelmetMountedDevice"] = 1,
											["VoiceCallsignLabel"] = "CT",
											["OuterBoard"] = 0,
											["InnerBoard"] = 0,
											["STN_L16"] = "00051",
											["VoiceCallsignNumber"] = "11",
										}, -- end of ["AddPropAircraft"]
										["type"] = "DCSRecorder-Hornet-Authored-Test",
										["unitId"] = 12201,
										["psi"] = 0.00031086740273997,
										["onboard_num"] = "002",
										["y"] = 892008.524296,
										["x"] = -312421.002171,
										["name"] = "Record Hornet",
										["payload"] = 
										{
											["pylons"] = 
											{
												[2] = 
												{
													["CLSID"] = "<CLEAN>",
												}, -- end of [2]
												[3] = 
												{
													["CLSID"] = "<CLEAN>",
												}, -- end of [3]
												[5] = 
												{
													["CLSID"] = "<CLEAN>",
												}, -- end of [5]
												[7] = 
												{
													["CLSID"] = "<CLEAN>",
												}, -- end of [7]
												[8] = 
												{
													["CLSID"] = "<CLEAN>",
												}, -- end of [8]
											}, -- end of ["pylons"]
											["fuel"] = 3500,
											["flare"] = 15,
											["chaff"] = 30,
											["gun"] = 100,
										}, -- end of ["payload"]
										["heading"] = -0.00031086740273997,
										["callsign"] = 
										{
											[1] = 4,
											[2] = 1,
											["name"] = "Colt11",
											[3] = 1,
										}, -- end of ["callsign"]
										["datalinks"] = 
										{
											["Link16"] = 
											{
												["settings"] = 
												{
													["FF1_Channel"] = 2,
													["FF2_Channel"] = 3,
													["transmitPower"] = 0,
													["VOCB_Channel"] = 5,
													["VOCA_Channel"] = 4,
													["AIC_Channel"] = 1,
												}, -- end of ["settings"]
												["network"] = 
												{
													["teamMembers"] = 
													{
														[1] = 
														{
															["missionUnitId"] = 12201,
														}, -- end of [1]
													}, -- end of ["teamMembers"]
													["donors"] = {},
												}, -- end of ["network"]
											}, -- end of ["Link16"]
										}, -- end of ["datalinks"]
									}, -- end of [1]
								}, -- end of ["units"]
								["y"] = 892008.524296,
								["x"] = -312421.002171,
								["name"] = "Record Hornet Group",
								["communication"] = true,
								["uncontrollable"] = false,
								["start_time"] = 0,
								["modulation"] = 0,
								["frequency"] = 124,
							}, -- end of [1]
							[2] = 
							{
								["lateActivation"] = false,
								["tasks"] = {},
								["radioSet"] = false,
								["task"] = "Nothing",
								["uncontrolled"] = false,
								["taskSelected"] = true,
								["route"] = 
								{
									["points"] = 
									{
										[1] = 
										{
											["alt"] = 1800,
											["action"] = "Turning Point",
											["alt_type"] = "BARO",
											["speed"] = 140,
											["task"] = 
											{
												["id"] = "ComboTask",
												["params"] = 
												{
													["tasks"] = {},
												}, -- end of ["params"]
											}, -- end of ["task"]
											["type"] = "Turning Point",
											["ETA"] = 0,
											["ETA_locked"] = true,
											["y"] = 892160,
											["x"] = -314820,
											["speed_locked"] = true,
										}, -- end of [1]
										[2] = 
										{
											["alt"] = 1800,
											["action"] = "Turning Point",
											["alt_type"] = "BARO",
											["speed"] = 140,
											["task"] = 
											{
												["id"] = "ComboTask",
												["params"] = 
												{
													["tasks"] = {},
												}, -- end of ["params"]
											}, -- end of ["task"]
											["type"] = "Turning Point",
											["ETA"] = 214.28571428571,
											["ETA_locked"] = false,
											["y"] = 892160,
											["x"] = -284820,
											["speed_locked"] = true,
										}, -- end of [2]
									}, -- end of ["points"]
								}, -- end of ["route"]
								["groupId"] = 12102,
								["hidden"] = false,
								["units"] = 
								{
									[1] = 
									{
										["alt"] = 1800,
										["hardpoint_racks"] = true,
										["alt_type"] = "BARO",
										["livery_id"] = "Blue Angels Jet Team",
										["skill"] = "Player",
										["speed"] = 140,
										["AddPropAircraft"] = 
										{
											["HelmetMountedDevice"] = 1,
											["VoiceCallsignLabel"] = "CT",
											["OuterBoard"] = 0,
											["InnerBoard"] = 0,
											["STN_L16"] = "00052",
											["VoiceCallsignNumber"] = "11",
										}, -- end of ["AddPropAircraft"]
										["type"] = "FA-18C_hornet",
										["Radio"] = 
										{
											[1] = 
											{
												["channelsNames"] = {},
												["modulations"] = 
												{
													[1] = 0,
													[2] = 0,
													[4] = 0,
													[8] = 0,
													[16] = 0,
													[17] = 0,
													[9] = 0,
													[18] = 0,
													[19] = 0,
													[10] = 0,
													[20] = 0,
													[11] = 0,
													[3] = 0,
													[6] = 0,
													[12] = 0,
													[13] = 0,
													[7] = 0,
													[14] = 0,
													[5] = 0,
													[15] = 0,
												}, -- end of ["modulations"]
												["channels"] = 
												{
													[1] = 305,
													[2] = 264,
													[4] = 256,
													[8] = 257,
													[16] = 261,
													[17] = 267,
													[9] = 255,
													[18] = 251,
													[19] = 253,
													[10] = 262,
													[20] = 266,
													[11] = 259,
													[3] = 265,
													[6] = 250,
													[12] = 268,
													[13] = 269,
													[7] = 270,
													[14] = 260,
													[5] = 254,
													[15] = 263,
												}, -- end of ["channels"]
											}, -- end of [1]
											[2] = 
											{
												["channelsNames"] = {},
												["modulations"] = 
												{
													[1] = 0,
													[2] = 0,
													[4] = 0,
													[8] = 0,
													[16] = 0,
													[17] = 0,
													[9] = 0,
													[18] = 0,
													[19] = 0,
													[10] = 0,
													[20] = 0,
													[11] = 0,
													[3] = 0,
													[6] = 0,
													[12] = 0,
													[13] = 0,
													[7] = 0,
													[14] = 0,
													[5] = 0,
													[15] = 0,
												}, -- end of ["modulations"]
												["channels"] = 
												{
													[1] = 305,
													[2] = 264,
													[4] = 256,
													[8] = 257,
													[16] = 261,
													[17] = 267,
													[9] = 255,
													[18] = 251,
													[19] = 253,
													[10] = 262,
													[20] = 266,
													[11] = 259,
													[3] = 265,
													[6] = 250,
													[12] = 268,
													[13] = 269,
													[7] = 270,
													[14] = 260,
													[5] = 254,
													[15] = 263,
												}, -- end of ["channels"]
											}, -- end of [2]
										}, -- end of ["Radio"]
										["unitId"] = 12202,
										["psi"] = -0,
										["onboard_num"] = "002",
										["y"] = 892160,
										["x"] = -314820,
										["name"] = "Wing Hornet",
										["payload"] = 
										{
											["pylons"] = 
											{
												[2] = 
												{
													["CLSID"] = "<CLEAN>",
												}, -- end of [2]
												[3] = 
												{
													["CLSID"] = "<CLEAN>",
												}, -- end of [3]
												[5] = 
												{
													["CLSID"] = "<CLEAN>",
												}, -- end of [5]
												[7] = 
												{
													["CLSID"] = "<CLEAN>",
												}, -- end of [7]
												[8] = 
												{
													["CLSID"] = "<CLEAN>",
												}, -- end of [8]
											}, -- end of ["pylons"]
											["fuel"] = 3500,
											["flare"] = 15,
											["chaff"] = 30,
											["gun"] = 100,
										}, -- end of ["payload"]
										["heading"] = 0,
										["callsign"] = 
										{
											[1] = 4,
											[2] = 1,
											["name"] = "Colt11",
											[3] = 1,
										}, -- end of ["callsign"]
										["datalinks"] = 
										{
											["Link16"] = 
											{
												["settings"] = 
												{
													["FF1_Channel"] = 2,
													["FF2_Channel"] = 3,
													["transmitPower"] = 0,
													["VOCB_Channel"] = 5,
													["VOCA_Channel"] = 4,
													["AIC_Channel"] = 1,
												}, -- end of ["settings"]
												["network"] = 
												{
													["teamMembers"] = 
													{
														[1] = 
														{
															["missionUnitId"] = 12202,
														}, -- end of [1]
													}, -- end of ["teamMembers"]
													["donors"] = {},
												}, -- end of ["network"]
											}, -- end of ["Link16"]
										}, -- end of ["datalinks"]
									}, -- end of [1]
								}, -- end of ["units"]
								["y"] = 892160,
								["x"] = -314820,
								["name"] = "Wing Hornet Group",
								["communication"] = true,
								["uncontrollable"] = false,
								["start_time"] = 0,
								["modulation"] = 0,
								["frequency"] = 124,
							}, -- end of [2]
							[3] = 
							{
								["lateActivation"] = false,
								["tasks"] = {},
								["radioSet"] = false,
								["task"] = "Nothing",
								["uncontrolled"] = false,
								["taskSelected"] = true,
								["route"] = 
								{
									["points"] = 
									{
										[1] = 
										{
											["alt"] = 1800,
											["action"] = "Turning Point",
											["alt_type"] = "BARO",
											["speed"] = 140,
											["task"] = 
											{
												["id"] = "ComboTask",
												["params"] = 
												{
													["tasks"] = {},
												}, -- end of ["params"]
											}, -- end of ["task"]
											["type"] = "Turning Point",
											["ETA"] = 0,
											["ETA_locked"] = true,
											["y"] = 892320,
											["x"] = -314640,
											["speed_locked"] = true,
										}, -- end of [1]
										[2] = 
										{
											["alt"] = 1800,
											["action"] = "Turning Point",
											["alt_type"] = "BARO",
											["speed"] = 140,
											["task"] = 
											{
												["id"] = "ComboTask",
												["params"] = 
												{
													["tasks"] = {},
												}, -- end of ["params"]
											}, -- end of ["task"]
											["type"] = "Turning Point",
											["ETA"] = 214.28571428571,
											["ETA_locked"] = false,
											["y"] = 892320,
											["x"] = -284640,
											["speed_locked"] = true,
										}, -- end of [2]
									}, -- end of ["points"]
								}, -- end of ["route"]
								["groupId"] = 12103,
								["hidden"] = false,
								["units"] = 
								{
									[1] = 
									{
										["alt"] = 1800,
										["hardpoint_racks"] = true,
										["alt_type"] = "BARO",
										["livery_id"] = "Blue Angels Jet Team",
										["skill"] = "High",
										["speed"] = 140,
										["AddPropAircraft"] = 
										{
											["HelmetMountedDevice"] = 1,
											["VoiceCallsignLabel"] = "CT",
											["OuterBoard"] = 0,
											["InnerBoard"] = 0,
											["STN_L16"] = "00053",
											["VoiceCallsignNumber"] = "11",
										}, -- end of ["AddPropAircraft"]
										["type"] = "FA-18C_hornet",
										["unitId"] = 12203,
										["psi"] = -0,
										["onboard_num"] = "002",
										["y"] = 892320,
										["x"] = -314640,
										["name"] = "Scene Witness",
										["payload"] = 
										{
											["pylons"] = 
											{
												[2] = 
												{
													["CLSID"] = "<CLEAN>",
												}, -- end of [2]
												[3] = 
												{
													["CLSID"] = "<CLEAN>",
												}, -- end of [3]
												[5] = 
												{
													["CLSID"] = "<CLEAN>",
												}, -- end of [5]
												[7] = 
												{
													["CLSID"] = "<CLEAN>",
												}, -- end of [7]
												[8] = 
												{
													["CLSID"] = "<CLEAN>",
												}, -- end of [8]
											}, -- end of ["pylons"]
											["fuel"] = 3500,
											["flare"] = 15,
											["chaff"] = 30,
											["gun"] = 100,
										}, -- end of ["payload"]
										["heading"] = 0,
										["callsign"] = 
										{
											[1] = 4,
											[2] = 1,
											["name"] = "Colt11",
											[3] = 1,
										}, -- end of ["callsign"]
										["datalinks"] = 
										{
											["Link16"] = 
											{
												["settings"] = 
												{
													["FF1_Channel"] = 2,
													["FF2_Channel"] = 3,
													["transmitPower"] = 0,
													["VOCB_Channel"] = 5,
													["VOCA_Channel"] = 4,
													["AIC_Channel"] = 1,
												}, -- end of ["settings"]
												["network"] = 
												{
													["teamMembers"] = 
													{
														[1] = 
														{
															["missionUnitId"] = 12203,
														}, -- end of [1]
													}, -- end of ["teamMembers"]
													["donors"] = {},
												}, -- end of ["network"]
											}, -- end of ["Link16"]
										}, -- end of ["datalinks"]
									}, -- end of [1]
								}, -- end of ["units"]
								["y"] = 892320,
								["x"] = -314640,
								["name"] = "Scene Witness Group",
								["communication"] = true,
								["uncontrollable"] = false,
								["start_time"] = 0,
								["modulation"] = 0,
								["frequency"] = 124,
							}, -- end of [3]
						}, -- end of ["group"]
					}, -- end of ["plane"]
				}, -- end of [1]
			}, -- end of ["country"]
		}, -- end of ["blue"]
		["red"] = 
		{
			["bullseye"] = 
			{
				["y"] = 371700,
				["x"] = 11557,
			}, -- end of ["bullseye"]
			["nav_points"] = {},
			["name"] = "red",
			["country"] = {},
		}, -- end of ["red"]
	}, -- end of ["coalition"]
	["sortie"] = "DictKey_sortie_8",
	["version"] = 23,
	["trigrules"] = 
	{
		[1] = 
		{
			["rules"] = 
			{
				[1] = 
				{
					["predicate"] = "c_time_after",
					["seconds"] = 12,
				}, -- end of [1]
			}, -- end of ["rules"]
			["eventlist"] = "",
			["predicate"] = "triggerOnce",
			["actions"] = 
			{
				[1] = 
				{
					["flag"] = "DCSR_AUTHORED_1_READY",
					["predicate"] = "a_set_flag_value",
					["value"] = 73,
				}, -- end of [1]
				[2] = 
				{
					["seconds"] = 15,
					["start_delay"] = 0,
					["predicate"] = "a_out_text_delay",
					["text"] = "DictKey_AuthoredMessage",
					["KeyDict_text"] = "DictKey_AuthoredMessage",
					["clearview"] = false,
				}, -- end of [2]
				[3] = 
				{
					["file"] = "ResKey_AuthoredChime",
					["predicate"] = "a_out_sound",
					["start_delay"] = 0,
				}, -- end of [3]
			}, -- end of ["actions"]
			["comment"] = "Authored message, resource and occupied flag",
		}, -- end of [1]
		[2] = 
		{
			["rules"] = {},
			["eventlist"] = "",
			["predicate"] = "triggerStart",
			["actions"] = 
			{
				[1] = 
				{
					["predicate"] = "a_set_command",
					["command"] = 816,
				}, -- end of [1]
				[2] = 
				{
					["text"] = "DCSR_AUTHORED_2_CONFIG={\
[\"expected\"]={\
[21]=0.0,\
[38]=0.0,\
[0]=0.0,\
[3]=0.0,\
[5]=0.0,\
[9]=0.11533036083,\
[10]=0.115174889565,\
[11]=-0.000244275550358,\
[12]=0.000439658761024,\
[13]=0.139793604612,\
[14]=0.139793604612,\
[15]=0.0106101222336,\
[16]=0.0109763452783,\
[17]=0.00228146091104,\
[18]=0.00228149187751,\
[28]=0.0,\
[29]=0.0,\
[89]=0.0129789467901,\
[90]=0.0129725849256,\
[88]=0.0,\
[190]=0.0,\
[191]=0.0,\
[192]=0.0,\
[193]=0.0,\
[210]=0.0,\
[212]=0.0,\
[1]=0.0,\
[6]=0.0,\
[4]=0.0,\
[101]=1.0,\
[103]=1.0,\
[102]=1.0,\
[2]=-0.0,\
},\
[\"token_high\"]=0.798355758190155,\
[\"token_low\"]=0.6081656217575073,\
[\"duration\"]=22.62,\
[\"smoke_events\"]={\
[1]={\
[\"time\"]=0,\
[\"on\"]=false,\
},\
},\
}\
-- Bounded airborne integration. The installed user hook commits the native\
-- one-shot latch and dispatches Active Pause release in the same hook callback.\
local c=assert(DCSR_AUTHORED_2_CONFIG)\
local s={phase='preparing',held=true,started=timer.getTime(),smoke_index=0,last_replay=0}\
DCSR_AUTHORED_2=s\
local function emit(text)env.info('DCSR_AUTHORED_2 '..text)end\
local function notice(text)trigger.action.outText('Release test: '..text,15)end\
local function flag(name,value)trigger.action.setUserFlag(name,value)end\
local function lead()local u=Unit.getByName(\"Record Hornet\");return u and u:isExist() and u or nil end\
local function matched(u)\
    return math.abs(u:getDrawArgumentValue(997)-c.token_high)<1e-8 and\
        math.abs(u:getDrawArgumentValue(998)-c.token_low)<1e-8\
end\
local function initial(u)\
    if not matched(u) or u:getDrawArgumentValue(999)~=.125 or u:getDrawArgumentValue(996)~=0 then return false end\
    for index,value in pairs(c.expected)do\
        local actual=u:getDrawArgumentValue(index)\
        if actual~=actual or math.abs(actual-value)>0.000001 then return false end\
    end\
    return true\
end\
function s.fail(reason)\
    if s.phase=='failed' or s.phase=='complete' then return end\
    s.phase='failed';flag('DCSR_AUTHORED_2_PENDING',0)\
    local u=lead();if u then u:destroy()end\
    if s.held then flag('DCSR_AUTHORED_2_CLEANUP',1)end\
    emit('FAILED,'..tostring(reason));notice('FAILED: '..tostring(reason)..'. Exit normally and retain logs.')\
end\
function s.cleaned()s.held=false;emit('HOLD_CLEANED')end\
function s.arm(session,generation)\
    if s.phase~='preparing' and s.phase~='waiting' then return false end\
    local u=lead()\
    if not u or not initial(u) or type(session)~='string' or not session:match('^[%w_]+$') or\
        type(generation)~='number' or generation<1 then return false end\
    s.session,s.generation=session,generation\
    if s.phase~='waiting' then\
        s.phase='waiting';emit('READY,'..session..','..generation)\
        notice('Ready. Inspect the held lead, then F10 > DCS Recorder playback > Start playback. Do not toggle Active Pause.')\
    end\
    return true\
end\
function s.released(session,generation)\
    if s.phase~='requested' or s.session~=session or s.generation~=generation then\
        s.fail('unexpected_release_ack');return false\
    end\
    s.held=false;flag('DCSR_AUTHORED_2_PENDING',0)\
    s.phase='starting';s.release_time=timer.getTime()\
    emit(string.format('PLAYER_RELEASED,%s,%d,%.9f',session,generation,s.release_time))\
    notice('Released. Watch first movement and smoke, then let the short recording finish.')\
    return true\
end\
local function sample(name)\
    local u=Unit.getByName(name);if not u or not u:isExist() then return end\
    local p,v=u:getPosition(),u:getVelocity();local values={}\
    for _,a in ipairs({0,3,5,9,10,11,12,13,14,15,16,17,18,21,38,88,190,191,192,193,210,212,1,6,4,101,103,102,2,89,90,28,29})do\
        values[#values+1]=string.format('%.9g',u:getDrawArgumentValue(a))\
    end\
    emit(string.format('SAMPLE,%s,%s,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9g,%s',\
        s.phase,name,timer.getTime(),p.p.x,p.p.y,p.p.z,p.x.x,p.x.y,p.x.z,p.y.x,p.y.y,p.y.z,\
        v.x,v.y,v.z,1000*u:getDrawArgumentValue(996),u:getDrawArgumentValue(999),table.concat(values,',')))\
end\
local function smoke(u)\
    local elapsed=1000*u:getDrawArgumentValue(996)\
    assert(elapsed==elapsed and elapsed>=s.last_replay and elapsed<=c.duration+.1,'invalid_replay_clock')\
    s.last_replay=elapsed\
    while c.smoke_events[s.smoke_index+1] and c.smoke_events[s.smoke_index+1].time<=elapsed do\
        s.smoke_index=s.smoke_index+1\
    end\
    local desired=assert(c.smoke_events[s.smoke_index])\
    if desired.on~=s.smoke_on then\
        u:getController():setCommand({id='SMOKE_ON_OFF',params={value=desired.on}})\
        s.smoke_on=desired.on\
        emit(string.format('SMOKE,%.9f,%.9f,%d',timer.getTime(),elapsed,desired.on and 1 or 0))\
    end\
end\
local function tick()\
    if s.phase=='failed' or s.phase=='complete' then return end\
    local now=timer.getTime();local u=lead()\
    if not u then s.fail('missing_aircraft');return end\
    local status=u:getDrawArgumentValue(999)\
    if status~=0 and (not matched(u) or status==.75) then s.fail('native_readiness_lost');return end\
    if s.phase=='preparing' then\
        if matched(u) and status==.125 then\
            if not initial(u) then s.fail('snapshot_mismatch');return end\
            smoke(u)\
        end\
        if now-s.started>10 then s.fail('bridge_or_native_readiness_timeout');return end\
    elseif s.phase=='waiting' or s.phase=='countdown' then\
        if not initial(u) then s.fail('initial_state_not_retained');return end\
        smoke(u)\
    elseif s.phase=='requested' then\
        if now-s.request_time>1 then s.fail('release_ack_timeout');return end\
    elseif s.phase=='starting' or s.phase=='playing' then\
        if status==.25 then\
            if s.phase=='starting' then s.phase='playing';emit(string.format('NATIVE_RUNNING,%.9f,%.9f',now,1000*u:getDrawArgumentValue(996)))end\
            smoke(u)\
        elseif status==.5 and s.phase=='playing' then\
            smoke(u);sample(\"Wing Hornet\");sample(\"Record Hornet\");u:destroy();s.phase='complete'\
            emit('COMPLETE');notice('Recording ended. Report first movement, smoke onset, and any jump or sound change. Exit normally.');return\
        elseif s.phase=='playing' or now-s.release_time>1 then s.fail('native_release_not_confirmed');return end\
        if now-s.release_time>c.duration+2 then s.fail('completion_timeout');return end\
    end\
    sample(\"Wing Hornet\");sample(\"Record Hornet\")\
    return now+.02\
end\
local function checked_tick()\
    local ok,next_time=pcall(tick)\
    if not ok then s.fail(next_time);return end\
    return next_time\
end\
local function start()\
    if s.phase~='waiting' then emit('START_REFUSED,'..s.phase);notice('Start unavailable: '..s.phase..'.');return end\
    local u=lead();if not u or not initial(u) then s.fail('not_ready');return end\
    s.phase='countdown';s.countdown_time=timer.getTime();emit(string.format('COUNTDOWN,%.9f',s.countdown_time))\
    notice('Starting in 3. Do not toggle Active Pause.')\
    local remaining=3\
    timer.scheduleFunction(function()\
        if s.phase~='countdown' then return end\
        remaining=remaining-1\
        if remaining>0 then notice('Starting in '..remaining..'.');return timer.getTime()+1 end\
        local current=lead()\
        if not current or not initial(current) then s.fail('not_ready_at_release');return end\
        s.phase='requested';s.request_time=timer.getTime();flag('DCSR_AUTHORED_2_PENDING',1)\
        emit(string.format('REQUEST,%s,%d,%.9f',s.session,s.generation,s.request_time))\
    end,nil,s.countdown_time+1)\
end\
local menu=missionCommands.addSubMenu('DCS Recorder playback')\
missionCommands.addCommand('Start playback (3-second countdown)',menu,start)\
missionCommands.addCommand('Show status',menu,function()notice(s.phase)end)\
flag('DCSR_AUTHORED_2_PENDING',0);flag('DCSR_AUTHORED_2_CLEANUP',0)\
emit('INITIALIZED');notice('Player held. Waiting for the complete snapshot and release bridge.')\
checked_tick()\
if s.phase~='failed' then timer.scheduleFunction(checked_tick,nil,timer.getTime()+.02)end\
",
					["predicate"] = "a_do_script",
				}, -- end of [2]
			}, -- end of ["actions"]
			["comment"] = "DCS Recorder: hold and release selected playback aircraft",
		}, -- end of [2]
		[3] = 
		{
			["rules"] = 
			{
				[1] = 
				{
					["flag"] = "DCSR_AUTHORED_2_CLEANUP",
					["predicate"] = "c_flag_is_true",
				}, -- end of [1]
			}, -- end of ["rules"]
			["eventlist"] = "",
			["predicate"] = "triggerOnce",
			["actions"] = 
			{
				[1] = 
				{
					["predicate"] = "a_set_command",
					["command"] = 816,
				}, -- end of [1]
				[2] = 
				{
					["text"] = "DCSR_AUTHORED_2.cleaned()",
					["predicate"] = "a_do_script",
				}, -- end of [2]
			}, -- end of ["actions"]
			["comment"] = "DCS Recorder: release owned hold on failure",
		}, -- end of [3]
	}, -- end of ["trigrules"]
	["currentKey"] = 2672,
	["failures"] = 
	{
		["Failure_Fuel_Tank1Transfer"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Fuel_Tank1Transfer"]
		["Failure_Ctrl_Aileron"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Ctrl_Aileron"]
		["Failure_Ctrl_FCS_Ch3"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Ctrl_FCS_Ch3"]
		["Failure_PP_EngR_Main_FFCS"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_PP_EngR_Main_FFCS"]
		["Failure_Elec_LeftGenerator"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Elec_LeftGenerator"]
		["Failure_Gear_NWS"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Gear_NWS"]
		["Failure_Comp_ADC"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Comp_ADC"]
		["Failure_PP_RightPTS"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_PP_RightPTS"]
		["Failure_Comp_MC2"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Comp_MC2"]
		["Failure_Hyd_IsolatedHYD2BSystem_Leak"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Hyd_IsolatedHYD2BSystem_Leak"]
		["Failure_Ctrl_FCS_Ch1"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Ctrl_FCS_Ch1"]
		["Failure_PP_LeftAMAD_OilLeak"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_PP_LeftAMAD_OilLeak"]
		["Failure_PP_EngR_Nozzle_CS"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_PP_EngR_Nozzle_CS"]
		["Failure_Elec_RightGenerator"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Elec_RightGenerator"]
		["Failure_Gear_WOW"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Gear_WOW"]
		["Failure_Ctrl_FCS_Ch2"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Ctrl_FCS_Ch2"]
		["Failure_Fuel_QuantityGaging"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Fuel_QuantityGaging"]
		["Failure_Fuel_Tank4Transfer"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Fuel_Tank4Transfer"]
		["Failure_Elec_EmergencyBattery"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Elec_EmergencyBattery"]
		["Failure_PP_EngR_OilLeak"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_PP_EngR_OilLeak"]
		["Failure_PP_LeftPTS"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_PP_LeftPTS"]
		["Failure_Hyd_HYD1B_Leak"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Hyd_HYD1B_Leak"]
		["Failure_Sens_LeftPitotHeater"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Sens_LeftPitotHeater"]
		["Failure_Fuel_ExtTankTransferC"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Fuel_ExtTankTransferC"]
		["Failure_PP_RightAMAD_OilLeak"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_PP_RightAMAD_OilLeak"]
		["Failure_Comp_MC1"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Comp_MC1"]
		["Failure_Ctrl_LEF"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Ctrl_LEF"]
		["Failure_ECS_OBOGS"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_ECS_OBOGS"]
		["Failure_Fuel_RightBoostPump"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Fuel_RightBoostPump"]
		["Failure_ECS_Valve"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_ECS_Valve"]
		["Failure_Ctrl_FCS_Ch4"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Ctrl_FCS_Ch4"]
		["Failure_Sens_RightPitotHeater"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Sens_RightPitotHeater"]
		["Failure_Hyd_HYD2B_Leak"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Hyd_HYD2B_Leak"]
		["Failure_Hyd_HYD1A_Leak"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Hyd_HYD1A_Leak"]
		["Failure_PP_EngR_AB_FFCS"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_PP_EngR_AB_FFCS"]
		["Failure_PP_EngL_Nozzle_CS"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_PP_EngL_Nozzle_CS"]
		["Failure_PP_EngL_Main_FFCS"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_PP_EngL_Main_FFCS"]
		["Failure_Elec_LeftTransformerRectifier"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Elec_LeftTransformerRectifier"]
		["Failure_Fuel_ExtTankTransferL"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Fuel_ExtTankTransferL"]
		["Failure_Elec_UtilityBattery"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Elec_UtilityBattery"]
		["Failure_Elec_RightTransformerRectifier"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Elec_RightTransformerRectifier"]
		["Failure_PP_EngL_AB_FFCS"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_PP_EngL_AB_FFCS"]
		["Failure_Fuel_ExtTankTransferR"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Fuel_ExtTankTransferR"]
		["Failure_Fuel_LeftBoostPump"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Fuel_LeftBoostPump"]
		["Failure_PP_EngL_OilLeak"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_PP_EngL_OilLeak"]
		["Failure_Hyd_HYD2A_Leak"] = 
		{
			["hh"] = 0,
			["prob"] = 100,
			["enable"] = false,
			["mmint"] = 1,
			["mm"] = 0,
		}, -- end of ["Failure_Hyd_HYD2A_Leak"]
	}, -- end of ["failures"]
	["forcedOptions"] = {},
	["start_time"] = 43200,
} -- end of mission
