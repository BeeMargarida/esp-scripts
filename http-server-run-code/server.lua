dofile("wifi.lua")

filename = "script.lua"

-- Setup Server
function receiver(sck, data)
    print("Request received")

    local buf = "";
    local _, _, method, path, vars = string.find(data, "([A-Z]+) (.+)?(.+) HTTP");
    if(method == nil)then
        _, _, method, path = string.find(data, "([A-Z]+) (.+) HTTP");
    end

    local response = {"HTTP/1.0 200 OK\r\nServer: NodeMCU on ESP8266\r\nContent-Type: text/html\r\n\r\n"}
    
    local payloadFound = false

    if method == "POST" and path == "/execute"  then
        file.remove(filename)
        file.open(filename, "w+")

        if (payloadFound == true) then
            file.write(data)
        else 
            local payloadOffset = string.find(data, "\r\n\r\n")
            local str = string.sub(data, payloadOffset + 4)

            if(payloadOffset ~= nil and string.len(str) ~= 0) then
                file.write(str)
                file.flush()
                payloadFound = true
                print("File written")
                collectgarbage()
            else 
                response[#response + 1] = "No file received."
            end
        end
    end

    local function send(localSocket)
        if #response > 0 then
            localSocket:send(table.remove(response, 1))
        else
            localSocket:close()
            response = nil
            file.close()
            dofile(filename)
            collectgarbage()
        end
    end
    sck:on("sent", send)

    send(sck)
    
end

function setupServer()
    print("Setup Server")
    print(wifi.sta.getip())

    server = net.createServer(net.TCP)
    if server then
        server:listen(80, function(conn)
            print("Server Listening")
            conn:on("receive", receiver)
            collectgarbage()
        end)
    end
end

function startup()
    setupServer()
end
