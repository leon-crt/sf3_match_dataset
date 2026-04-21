
-- import luasocket library
package.path = "lua_libs/luasocket/?.lua;"
package.cpath = "lua_libs/socket/core.dll;" .. "lua_libs/mime/core.dll;"
local socket = require('socket')

-- Speed up the emulation
emu.speedmode("turbo")

-- Send TCP message while recording and then when no more messages are sent timeout goes off on server side that kills the process
local function check_emu_state()
    if emu.framecount() % 120 == 0
    then
        local Host, Port = "127.0.0.1", 42069
        local Tcp = assert(socket.tcp())
        Tcp:connect(Host, Port)
        Tcp:send("still recording!\n")
        Tcp:close()
    end
end

-- Function is called every frame but when emulation has finished it isnt, emu.registerexit also doesnt get called yet cause the emulator is still technically running
emu.registerafter(check_emu_state)