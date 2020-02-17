-- Setup WiFi
wifi.setmode(wifi.STATION)
config = {}
config.ssid = "Vodafone-ADF518"
config.pwd = "KNR8kkzetW"
-- wifi.sta.config({ssid = "raspberrypi", pwd = "UJr2016#"})
wifi.sta.config(config)

-- config_ip = {}  -- set IP,netmask, gateway
-- config_ip.ip = "192.168.1.0"
-- config_ip.netmask = "255.255.255.0"
-- config_ip.gateway = "192.168.1.0"
-- wifi.ap.setip(config_ip)

wifi.sta.connect();
print(wifi.sta.getip())
-- 

-- Initialising pin
local pin = 4
local status = gpio.HIGH
gpio.mode(pin, gpio.OUTPUT)
gpio.write(pin, status)
--

-- Setup Server
server = net.createServer(net.TCP, 30) -- 30s timeout

function receiver(sck, data)
    -- if string.find(data, "POST /led")  then
    --     if status == gpio.LOW then
    --         status = gpio.HIGH
    --     else
    --         status = gpio.LOW 
    --     end
    --     print(status)
    --     gpio.write(pin, status)
    -- elseif string.find(data, "GET /") then
    --     sck:send("Hello!")    
    -- end
    sck:send(dht.read(5))
    sck:on("sent", function(conn) conn:close() end)
end

if sv then
sv:listen(80, function(conn)
    conn:on("receive", receiver)
end)
end
--