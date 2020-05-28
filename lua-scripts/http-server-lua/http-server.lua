pin = 4
dht_pin = 5
status = gpio.HIGH

-- Initialising pin
function setupLED()
    print("Setup LED")
    gpio.mode(pin, gpio.OUTPUT)
    gpio.write(pin, status)
end
--

-- Setup Server
function receiver(sck, data)
    print("Request received")

    local buf = "";
    local _, _, method, path, vars = string.find(data, "([A-Z]+) (.+)?(.+) HTTP");
    if(method == nil)then
        _, _, method, path = string.find(data, "([A-Z]+) (.+) HTTP");
    end
    -- local _GET = {}
    -- if (vars ~= nil)then
    --     for k, v in string.gmatch(vars, "(%w+)=(%w+)&*") do
    --         _GET[k] = v
    --     end
    -- end

    local response = {"HTTP/1.0 200 OK\r\nServer: NodeMCU on ESP8266\r\nContent-Type: text/json\r\n\r\n"}
    print(path)
    if method == "POST" and path == "/led"  then
        if status == gpio.LOW then
            status = gpio.HIGH
        else
            status = gpio.LOW 
        end
        gpio.write(pin, status)
        response[#response + 1] = "{ led: "..status.."}"
    elseif method == "GET" and path == "/readings" then
        local status, temp, humi, temp_dec, humi_dec = dht.read(dht_pin)
        response[#response + 1] = "{temp:"..temp..","
        response[#response + 1] = "hum:"..humi.."}"
    elseif method == "GET" and path == "/" then
        response[#response + 1] = "Hello!"
    end

    local function send(localSocket)
        if #response > 0 then
            localSocket:send(table.remove(response, 1))
        else
            localSocket:close()
            response = nil
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
        end)
    end
end

function startup()
    setupLED()
    setupServer()
end


-- Define WiFi station event callbacks
wifi_connect_event = function(T)
  print("Connection to AP("..T.SSID..") established!")
  print("Waiting for IP address...")
  if disconnect_ct ~= nil then disconnect_ct = nil end
end

wifi_got_ip_event = function(T)
  -- Note: Having an IP address does not mean there is internet access!
  -- Internet connectivity can be determined with net.dns.resolve().
  print("Wifi connection is ready! IP address is: "..T.IP)
  print("Startup will resume momentarily, you have 3 seconds to abort.")
  print("Waiting...")
  tmr.create():alarm(3000, tmr.ALARM_SINGLE, startup)
end

wifi_disconnect_event = function(T)
  if T.reason == wifi.eventmon.reason.ASSOC_LEAVE then
    --the station has disassociated from a previously connected AP
    return
  end
  -- total_tries: how many times the station will attempt to connect to the AP. Should consider AP reboot duration.
  local total_tries = 75
  print("\nWiFi connection to AP("..T.SSID..") has failed!")

  --There are many possible disconnect reasons, the following iterates through
  --the list and returns the string corresponding to the disconnect reason.
  for key,val in pairs(wifi.eventmon.reason) do
    if val == T.reason then
      print("Disconnect reason: "..val.."("..key..")")
      break
    end
  end

  if disconnect_ct == nil then
    disconnect_ct = 1
  else
    disconnect_ct = disconnect_ct + 1
  end
  if disconnect_ct < total_tries then
    print("Retrying connection...(attempt "..(disconnect_ct+1).." of "..total_tries..")")
  else
    wifi.sta.disconnect()
    print("Aborting connection to AP!")
    disconnect_ct = nil
  end
end

-- Register WiFi Station event callbacks
wifi.eventmon.register(wifi.eventmon.STA_CONNECTED, wifi_connect_event)
wifi.eventmon.register(wifi.eventmon.STA_GOT_IP, wifi_got_ip_event)
wifi.eventmon.register(wifi.eventmon.STA_DISCONNECTED, wifi_disconnect_event)

print("Connecting to WiFi access point...")
wifi.setmode(wifi.STATION)
wifi.sta.config({ssid="-", pwd="-"})
