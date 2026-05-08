package.path = "lua_libs/luasocket/?.lua;"
package.cpath = "lua_libs/socket/core.dll;" .. "lua_libs/mime/core.dll;"
local socket = require('socket')

-- TODO: 
--      - create file name that encodes characters and supers (ideally quarkid but dont know how to get it) maybe chid1-supid1_chid2-supid2_gamenumber_roundNumber_quarkid?
--      - change stun detection so that a stunned character is encoded as stun = bignumber and it doesnt reset to 0 instantly
--      - Decide if I want an additional state value for stunned character or if I want to set the stun meter to its max until stun is over (Im afraid that the second will give the RL model the idea that having stun high is better than attacking while the opponent is stunned)
Frame_counter = 1
Buff_size = 100
Turbo = false
StunnedP1, StunnedP2 = false, false
CanRecoverFromStunP1, CanRecoverFromStunP2 = false, false
RoundNumber = 0

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

function StateData:new (chid, suid, posx, posy, health, super, stun, hit, inputs)
    local o = {}
    setmetatable(o, {__index = self})
    o.characterId = chid or ""
    o.superId = suid or ""
    o.posX = posx or {}
    o.posY = posy or {}
    o.health = health or {}
    o.super = super or {}
    o.stun = stun or {}
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
    self.hit = {}
    self.inputs = {}
end

-- Initialize buffer classes
P1 = StateData:new()
P2 = StateData:new()

-- Might have to change the order in this not sure if right
ChIdToName = {"Akuma", "Yun", "Ryu", "Urien", "Remy", "Oro","Necro", "Q", "Dudley","Ibuki","ChunLi", "Elena","Sean", "Makoto", "Hugo",  "Alex", "Twelve", "Ken", "Yang"}

-- Get quarkid from TCP socket with main python script
QuarkId = ""
local Host, Port = "127.0.0.1", 42069
local Tcp = assert(socket.tcp())
Tcp:connect(Host, Port)
Tcp:send("open!\n")
QuarkId = Tcp:receive(1024)
Tcp:send("received quarkid")
PlayerSide = Tcp:receive(1024)
Tcp:close()

--Formatting Functions
function FormatInputs(inputs)
    local bToN = { [true] = 1, [false] = 0} -- damn what a language
    return bToN[inputs["Left"]] .. "," .. bToN[inputs["Up"]] .. "," .. bToN[inputs["Right"]].. "," .. bToN[inputs["Down"]].. "," .. bToN[inputs["Weak Punch"]].. "," .. bToN[inputs["Medium Punch"]].. "," .. bToN[inputs["Strong Punch"]].. "," .. bToN[inputs["Weak Kick"]].. "," .. bToN[inputs["Medium Kick"]].. "," .. bToN[inputs["Strong Kick"]].. "," .. bToN[inputs["Start"]].. "," .. bToN[inputs["Coin"]]
end

function FormatValues(posX, posY, health, super, stun, hit, inputs)
    return tostring(posX) .. ";" .. tostring(posY) .. "," .. tostring(health) .. "," .. tostring(super) .. "," .. tostring(stun) .. "," .. tostring(hit) .. "," .. FormatInputs(inputs)
end

-- Writing to file function
function WriteToFile(p1, p2)
    local formatted_data = ""
    for i=1,Buff_size
    do
        formatted_data = formatted_data .. tostring(Frame_counter-Buff_size+i) .. ",P1," .. FormatValues(p1.posX[i], p1.posY[i], p1.health[i], p1.super[i], p1.stun[i], p1.hit[i], p1.inputs[i]) .. "\n" .. tostring(Frame_counter-Buff_size+i) .. ",P2," .. FormatValues(p2.posX[i], p2.posY[i], p2.health[i], p2.super[i], p2.stun[i], p2.hit[i], p2.inputs[i]) .. "\n"
    end
    local file = assert(io.open("fe_test.csv", "a+"))
    file:write(formatted_data)
    io.close(file)
end

-- General function that gets run every frame
function FeatureExtraction()
    -- P1 and P2 state values
    local posXP1, posYP1, posXP2, posYP2
    local healthP1, healthP2
    local superP1, superP2
    local stunP1, stunP2
    local hitP1, hitP2
    local stateP1, stateP2
    local previousStunP1, previousStunP2 = P1.stun[Frame_counter-2] or 0, P2.stun[Frame_counter-2] or 0

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

        -- Create csv file and set headers
        local filename = PlayerSide .. "-" .. ChIdToName[P1.characterId.tointeger()] .. P1.superId .. "-" .. ChIdToName[P2.characterId.tointeger()] .. P2.superId .. "-" .. QuarkId .. "-" .. RoundNumber .. ".csv"
        local file = assert(io.open(filename, "w"))
        file:write("Frame,Player,Position,Health,Meter,Stun,Hit,Left,Up,Right,Down,Lp,Mp,Hp,Lk,Mk,Hk,Start,Coin\n")
        io.close(file)

        print("ch.ID P1: " .. P1.characterId, "- ch.ID P2: " .. P2.characterId)
        print("super ID P1: " .. P1.superId, "- super ID P2: " .. P2.superId)
    elseif in_match == 2 -- after round start
    then
        if Turbo then emu.speedmode("normal") Turbo = false end
        -- Extract P1 and P2 state values
        posXP1, posYP1 = memory.readword(0x02068CD0), memory.readword(0x02068CD4)
        posXP2, posYP2 = memory.readword(0x02069168), memory.readword(0x0206916C) 
        healthP1, healthP2 = memory.readbyte(0x02028655), memory. readbyte(0x0202866D)
        superP1, superP2 = memory.readbyte(0x020286A5), memory.readbyte(0x020286D9) -- saBarContent1 -> 0x020286A5   saBarCount1 -> 0x020286AB    bar1 -> 0x020695B5

        -- Stun management hell
        stunP1 = bit.rshift(memory.readdword(0x020695F7 + 0x6), 24) -- stun -> 0x02028805  stunstatus -> 0x020695FD
        stunP2 = memory.readbyte(0x02028829)
        stateP1, stateP2 = memory.readbyte(0x02068E75), memory.readbyte(0x020691B3) -- state = 70 means stunned lets go
        if (stunP1 == 0 and previousStunP1 > 10) or (not StunnedP1 and stateP1 == 70)
        then
            StunnedP1 = true
        end
        if (stunP2 == 0 and previousStunP2 > 10) or (not StunnedP1 and stateP1 == 70)
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
            else
                stunP1 = 1000
            end
        end

        if StunnedP2
        then
            if (stateP2 ~= 70 and CanRecoverFromStunP1) or (stunP2 > 0) 
            then
                StunnedP2 = false
                CanRecoverFromStunP2 = false
            else
                stunP2 = 1000
            end
        end

        -- hit returns 2 sometimes for some reason and doesnt seem to return 1 when character is hit
        hitP1 = memory.readbyte(0x0202884D) or memory.readbyte(0x0202884F) or memory.readbyte(0x02028859) or memory.readbyte(0x02028855)
        hitP2 = memory.readbyte(0x02028861) or memory.readbyte(0x02028863) or memory.readbyte(0x02028869) or memory.readbyte(0x0202886D)
        
        table.insert(P1.posX, posXP1)
        table.insert(P1.posY, posYP1)
        table.insert(P2.posX, posXP2)
        table.insert(P2.posY, posYP2)
        table.insert(P1.health, healthP1)
        table.insert(P2.health, healthP2)
        table.insert(P1.super, superP1)
        table.insert(P2.super, superP2)
        table.insert(P1.stun, stunP1)
        table.insert(P2.stun, stunP2)
        table.insert(P1.hit, hitP1)
        table.insert(P2.hit, hitP2)
        
        -- DEBUG
        -- print("position P1: " .. posXP1 .. ", " .. posYP1)
        -- print("position P2: " .. posXP2 .. ", " .. posYP2)
        -- print("health P1: " .. healthP1)
        -- print("health P2: " .. healthP2)
        -- print("super P1: " .. superP1)
        -- print("super P2: " .. superP2)
        print("previousStunP1: " .. previousStunP1)
        print("previousStunP2: " .. previousStunP2)
        print("stun P1: " .. stunP1)
        print("stun P2: " .. stunP2)
        print("hit P1: " .. hitP1)
        print("hit P2: " .. hitP2)
        print("state P1: " .. stateP1)
        print("state P2: " .. stateP2)

        -- Extract environment info (whether an enemy projectile is on the screen and its position)
        -- skip for now because it requires scanning through hitboxes and likely we can't have only one projectile but we need all of them (30 max) which means
        -- making the state variable much bigger to accomodate for all of them. They would need to be represented by position and character they belong to
        
        -- INPUT TABLE EXAMPLE
        --{P2 Right=false, P2 Medium Punch=false, Service=false, P2 Coin=false, P1 Coin=false, P1 Down=false, P1 Strong Punch=false, P2 Weak Punch=false, P1 Weak Punch=true, P1 Medium Punch=false, P1 Start=false, P1 Medium Kick=false, P1 Right=true, P2 Up=false, P1 Strong Kick=false, Diagnostic=false, Region=1, P2 Down=false, P2 Left=false, P1 Left=false, P2 Medium Kick=false, Fake Dip=0, P2 Strong Punch=false, P1 Weak Kick=false, P2 Weak Kick=false, P1 Up=false, P2 Strong Kick=false, P2 Start=false, Reset=false}
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
        
        table.insert(P1.inputs, local_p1_input)
        table.insert(P2.inputs, local_p2_input)

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
        WriteToFile(P1, P2)
        P1:wipe()
        P2:wipe()
        P1.characterId = ""
        P1.superId = ""
        P2.characterId = ""
        P2.superId = ""
        RoundNumber = RoundNumber + 1
    else
        return nil
    end
end

emu.registerafter(FeatureExtraction)