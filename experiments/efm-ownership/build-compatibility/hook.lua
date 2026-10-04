-- One-shot read-only compatibility capture in the dedicated stock-aircraft fixture.
local pending=false
local function emit(text)log.write('DCSR_BUILD_CAPTURE',log.INFO,text)end
DCS.setUserCallbacks({
    onSimulationStart=function()
        pending=not not (DCS.getMissionFilename() or ''):find('045%-Build%-Compatibility')
        if pending then emit('WAITING_FOR_STOCK_PLAYER')end
    end,
    onSimulationStop=function()pending=false end,
    onSimulationFrame=function()
        if not pending then return end
        local ok,own=pcall(Export.LoGetSelfData)
        if not ok or not own or own.Name~='FA-18C_hornet' then return end
        pending=false
        local ok,result=pcall(function()
            local fn,err=package.loadlib(lfs.writedir()..'Scripts/DCSRecorderBuildCapture/BuildCompatibilityCapture.dll','dcs_build_capture')
            assert(fn,err);return fn()
        end)
        emit((ok and '' or 'ERROR,')..tostring(result))
    end,
})
emit('INSTALLED read_only=true')
