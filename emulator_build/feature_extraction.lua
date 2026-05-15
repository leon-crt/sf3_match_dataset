package.path = "lua_libs/luasocket/?.lua;"
package.cpath = "lua_libs/socket/core.dll;" .. "lua_libs/mime/core.dll;"
local socket = require('socket')

-- TODO: 
--      - Fix end of round buff size frame indexing error [test]
--      - Fix previousstun logic that misses a frame every time the buffers are emptied
--      - Change the position field in the csv to be two separate columns

Frame_counter = 1
Buff_size = 100
Turbo = false
StunnedP1, StunnedP2 = false, false
CanRecoverFromStunP1, CanRecoverFromStunP2 = false, false
RoundNumber = 0
Filename = ""

StateData = 
{
    characterId = "",
    superId = "",
    posX = {},
    posY = {},
    health = {},
    super = {},
    stun = {},
    hit = {},
    inputs = {}
}

function StateData:new (chid, suid, posx, posy, health, super, maxSuperBar, stun, isStunned, hit, inputs)
    local o = {}
    setmetatable(o, {__index = self})
    o.characterId = chid or ""
    o.superId = suid or ""
    o.superBarLength = maxSuperBar or 0
    o.posX = posx or {}
    o.posY = posy or {}
    o.health = health or {}
    o.super = super or {}
    o.stun = stun or {}
    o.isStunned = isStunned or {}
    o.hit = hit or {}
    o.inputs = inputs or {}
    return o
end

function StateData:wipe()
    self.posX = {}
    self.posY = {}
    self.health = {}
    self.super = {}
    self.stun = {}
    self.isStunned = {}
    self.hit = {}
    self.inputs = {}
end

function StateData:update(posx, posy, health, super, stun, isStunned, hit, inputs)
    table.insert(self.posX, posx)
    table.insert(self.posY, posy)
    table.insert(self.health, health)
    table.insert(self.super, super)
    table.insert(self.stun, stun)
    table.insert(self.isStunned, isStunned)
    table.insert(self.hit, hit)
    table.insert(self.inputs, inputs)
end

-- Initialize buffer classes
P1 = StateData:new()
P2 = StateData:new()

-- Translates Character Id to their name
ChIdToName = {"Alex", "Ryu", "Yun", "Dudley", "Necro", "Hugo", "Ibuki", "Elena", "Oro","Yang","Ken", "Sean","Urien", "Akuma", "Gill",  "ChunLi", "Makoto", "Q", "Twelve", "Remy"}

--Formatting Functions
function FormatInputs(inputs)
    local bToN = { [true] = 1, [false] = 0} -- damn what a language
    return bToN[inputs["Left"]] .. "," .. bToN[inputs["Up"]] .. "," .. bToN[inputs["Right"]].. "," .. bToN[inputs["Down"]].. "," .. bToN[inputs["Weak Punch"]].. "," .. bToN[inputs["Medium Punch"]].. "," .. bToN[inputs["Strong Punch"]].. "," .. bToN[inputs["Weak Kick"]].. "," .. bToN[inputs["Medium Kick"]].. "," .. bToN[inputs["Strong Kick"]].. "," .. bToN[inputs["Start"]].. "," .. bToN[inputs["Coin"]]
end

function FormatValues(posX, posY, health, super, stun, isStunned, hit, inputs)
    return tostring(posX) .. ";" .. tostring(posY) .. "," .. tostring(health) .. "," .. tostring(super) .. "," .. tostring(stun) .. "," .. tostring(isStunned) .. "," .. tostring(hit) .. "," .. FormatInputs(inputs)
end

-- Writing to file function
function WriteToFile(p1, p2)
    local formatted_data = ""
    for i=1, #p1.posX
    do
        formatted_data = formatted_data .. tostring(Frame_counter - #p1.posX + i) .. ",P1," .. FormatValues(p1.posX[i], p1.posY[i], p1.health[i], p1.super[i], p1.stun[i], p1.isStunned[i], p1.hit[i], p1.inputs[i]) .. "\n" .. tostring(Frame_counter - Buff_size+i) .. ",P2," .. FormatValues(p2.posX[i], p2.posY[i], p2.health[i], p2.super[i], p2.stun[i], p2.isStunned[i], p2.hit[i], p2.inputs[i]) .. "\n"
    end
    local file = assert(io.open("../features/" .. Filename, "a+"))
    file:write(formatted_data)
    io.close(file)
end

-- General function that gets run every frame
function FeatureExtraction()
    -- P1 and P2 state values
    local posXP1, posYP1, posXP2, posYP2
    local healthP1, healthP2
    local superP1, superP2
    local superCountP1, superCountP2
    local stunP1, stunP2
    local isStunnedP1, isStunnedP2 = 0, 0
    local hitP1, hitP2
    local stateP1, stateP2
    local previousStunP1, previousStunP2 = P1.stun[Frame_counter % Buff_size - 1] or 0, P2.stun[Frame_counter % Buff_size - 1] or 0

    -- Get current game phase
    local in_match = memory.readbyte(0x020154A7)  -- 1 = match intro, 2 = after round start, 9 = character select, 6 = end of round, 8 = transition between rounds

    if in_match == 9 and not Turbo
    then
        emu.speedmode("turbo")
        Turbo=true
    end
    if in_match == 1 and P1.characterId == "" -- pre-match
    then
        -- Extract P1 and P2 character and super IDs
        P1.characterId, P2.characterId = memory.readbyte(0x02011387), memory.readbyte(0x02011388)
        P1.superId, P2.superId = memory.readbyte(0x0201138B), memory.readbyte(0x0201138C)
        P1.superBarLength, P2.superBarLength = memory.readbyte(0x020695B3), memory.readbyte(0x020695DF)

        print("ch.ID P1: " .. P1.characterId, "- ch.ID P2: " .. P2.characterId)
        print("super ID P1: " .. P1.superId, "- super ID P2: " .. P2.superId)
        -- Create csv file and set headers
        Filename = PlayerSide .. "-" .. ChIdToName[tonumber(P1.characterId)] .. tostring(P1.superId+1) .. "-" .. ChIdToName[tonumber(P2.characterId)] .. tostring(P2.superId+1) .. "-" .. QuarkId .. "-" .. RoundNumber .. ".csv"
        local file = assert(io.open("../features/" .. Filename, "w"))
        file:write("Frame,Player,Position,Health,Meter,Stun,isStunned,Hit,Left,Up,Right,Down,Lp,Mp,Hp,Lk,Mk,Hk,Start,Coin\n")
        io.close(file)

    elseif in_match == 2 -- after round start
    then
        -- Extract P1 and P2 state values
        posXP1, posYP1 = memory.readwordsigned(0x02068CD0), memory.readwordsigned(0x02068CD4)
        posXP2, posYP2 = memory.readwordsigned(0x02069168), memory.readwordsigned(0x0206916C) 
        -- Summing 1 to health value because we want 0 health to mean dead instead of still alive but one pixel left
        healthP1, healthP2 = memory.readbyte(0x02028655) + 1, memory.readbyte(0x0202866D) + 1
        superP1, superP2 = memory.readbyte(0x020286A5), memory.readbyte(0x020286D9) -- saBarContent1 -> 0x020286A5   saBarCount1 -> 0x020286AB    bar1 -> 0x020695B5
        superCountP1, superCountP2 = memory.readbyte(0x020695BF), memory.readbyte(0x020695EB)
        superP1 = superP1 + superCountP1 * P1.superBarLength
        superP2 = superP2 + superCountP2 * P2.superBarLength
        -- Stun management hell
        stunP1 = bit.rshift(memory.readdword(0x020695F7 + 0x6), 24) -- stun -> 0x02028805  stunstatus -> 0x020695FD
        stunP2 = memory.readbyte(0x02028829)
        stateP1, stateP2 = memory.readbyte(0x02068E75), memory.readbyte(0x020691B3) -- state = 70 means stunned lets go
        if (stunP1 == 0 and previousStunP1 > 10) or (not StunnedP1 and stateP1 == 70)
        then
            StunnedP1 = true
        end
        if (stunP2 == 0 and previousStunP2 > 10) or (not StunnedP2 and stateP2 == 70)
        then
            StunnedP2 = true
        end
        
        if stateP1 == 70
        then
            CanRecoverFromStunP1 = true
        end
        if stateP2 == 70
        then
            CanRecoverFromStunP2 = true
        end
        
        if StunnedP1
        then
            -- First condition means that at one point the character was stunned and now it's not anymore. second means the character was hit while stunned which causes them to not be stunned anymore
            if (stateP1 ~= 70 and CanRecoverFromStunP1) or (stunP1 > 0) 
            then
                StunnedP1 = false
                CanRecoverFromStunP1 = false
                isStunnedP1 = 0
            else
                isStunnedP1 = 1
            end
        end
        
        if StunnedP2
        then
            if (stateP2 ~= 70 and CanRecoverFromStunP1) or (stunP2 > 0) 
            then
                StunnedP2 = false
                CanRecoverFromStunP2 = false
                isStunnedP2 = 0
            else
                isStunnedP2 = 1
            end
        end
        
        -- hitstun detection
        local hitByNP1, hitBySP1, hitBySAP1, hitByOtherP1 = memory.readbyte(0x0202884D), memory.readbyte(0x0202884F), memory.readbyte(0x02028859), memory.readbyte(0x02028855)
        if hitByNP1 + hitBySP1 + hitBySAP1 + hitByOtherP1 > 0 then hitP1 = 1 else hitP1 = 0 end
        
        local hitByNP2, hitBySP2, hitBySAP2, hitByOtherP2 = memory.readbyte(0x02028861), memory.readbyte(0x02028863), memory.readbyte(0x02028869), memory.readbyte(0x0202886D)
        if hitByNP2 + hitBySP2 + hitBySAP2 + hitByOtherP2 > 0 then hitP2 = 1 else hitP2 = 0 end
        
        -- DEBUG
        -- if Turbo then emu.speedmode("normal") Turbo = false end
        -- print("position P1: " .. posXP1 .. ", " .. posYP1)
        -- print("position P2: " .. posXP2 .. ", " .. posYP2)
        -- print("health P1: " .. healthP1)
        -- print("health P2: " .. healthP2)
        -- print("super P1: " .. superP1)
        -- print("super P2: " .. superP2)
        -- print("previousStunP1: " .. previousStunP1)
        -- print("previousStunP2: " .. previousStunP2)
        -- print("stun P1: " .. stunP1)
        -- print("stun P2: " .. stunP2)
        -- print("isStunnedP1: " .. isStunnedP1)
        -- print("isStunnedP2: " .. isStunnedP2)
        -- print("hit P1: " .. hitP1)
        -- print("hit P2: " .. hitP2)
        -- print("state P1: " .. stateP1)
        -- print("state P2: " .. stateP2)

        -- Extract environment info (whether an enemy projectile is on the screen and its position)
        -- skip for now because it requires scanning through hitboxes and likely we can't have only one projectile but we need all of them (30 max) which means
        -- making the state variable much bigger to accomodate for all of them. They would need to be represented by position and character they belong to
        
        -- Extract P1 and P2 input
        local combined_input = joypad.get()
        local local_p1_input = {}
        local local_p2_input = {}
        
        for input, value in pairs(combined_input)
        do
            -- separate inputs from different players
            local prefix = string.sub(input,1,2)
            if prefix == "P1"
            then
                local_p1_input[string.sub(input,4,-1)] = value
            elseif prefix == "P2"
            then
                local_p2_input[string.sub(input,4,-1)] = value
            end
        end
        
        -- Update class buffers with current frame state values
        P1:update(posXP1, posYP1, healthP1, superP1, stunP1, isStunnedP1, hitP1, local_p1_input)
        P2:update(posXP2, posYP2, healthP2, superP2, stunP2, isStunnedP2, hitP2, local_p2_input)

        -- Format everything and write to file
        if Frame_counter % Buff_size == 0
        then
            print("writing to file, frame: " .. Frame_counter)
            WriteToFile(P1, P2)
            -- empty out the buffer classes so it doesnt slow everything down
            P1:wipe()
            P2:wipe()
        end

        -- Increase homemade framecounter
        Frame_counter = Frame_counter + 1

    elseif in_match == 6 and P1.posX[1] ~= nil -- if round has just ended and classes are not empty just write them to file
    then
        print("end of round: writing to file")
        -- make sure that the player that lost has their health reduced to 0
        local finalHealthP1, finalHealthP2 = P1.health[#P1.health], P2.health[#P2.health]
        if finalHealthP1 < finalHealthP2
        then
            finalHealthP1 = 0
            hitP1 = 1
            hitP2 = 0
        elseif finalHealthP1 == finalHealthP2
        then
            finalHealthP1, finalHealthP2 = 0, 0
            hitP1, hitP2 = 1, 1
        else
            finalHealthP2 = 0
            hitP2 = 1
            hitP1 = 0
        end

        -- update the classes one last time for the end of match result (inputs are the same as previous frame for convenience)
        P1:update(P1.posX[#P1.posX], P1.posY[#P1.posY], finalHealthP1, P1.super[#P1.super], P1.stun[#P1.stun], P1.isStunned[#P1.isStunned], hitP1, P1.inputs[#P1.inputs])
        P2:update(P2.posX[#P2.posX], P2.posY[#P2.posY], finalHealthP2, P2.super[#P2.super], P2.stun[#P2.stun], P2.isStunned[#P2.isStunned], hitP2, P2.inputs[#P2.inputs])

        WriteToFile(P1, P2)

        -- Reset global round specific variables
        P1:wipe()
        P2:wipe()
        P1.characterId = ""
        P1.superId = ""
        P2.characterId = ""
        P2.superId = ""
        P1.maxSuperBar = 0
        P2.maxSuperBar = 0
        RoundNumber = RoundNumber + 1
        Frame_counter = 1
    else
        return nil
    end

    -- Ping python handler to let it know the extraction is still running
    if emu.framecount() % 320 == 0
    then
        local bytes = Tcp:send("still recording!\n")
        if bytes == nil
        then
            Tcp = assert(socket.tcp())
            Tcp:settimeout(0) -- make pings non blocking so that the emulator doesnt crash
            Tcp:connect(Host, Port)
            Tcp:send("still recording!\n")
        end
    end
end

-- Get quarkid from TCP socket with main python script
QuarkId = ""
Host, Port = "127.0.0.1", 42069
Tcp = assert(socket.tcp())
Tcp:connect(Host, Port)
Tcp:send("open!\n")
QuarkId = Tcp:receive('*l')
Tcp:send("received quarkid")
PlayerSide = Tcp:receive(1)

emu.registerafter(FeatureExtraction)