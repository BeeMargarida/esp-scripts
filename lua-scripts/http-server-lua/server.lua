-- Setup WiFi
wifi.setmode(wifi.STATION)
-- wifi.sta.config({ssid = "raspberrypi", pwd = "UJr2016#"})
wifi.sta.config({ ssid = "Vodafone-ADF518", pwd = "KNR8kkzetW"})
wifi.sta.connect();
print(wifi.sta.getip())
-- 

-- Setup LEDs
led = 4
gpio.mode(led, gpio.OUTPUT)
--

-- Utils 
function parseHeader(req, res)
	local _, _, method, path, vars = string.find(req.source, '([A-Z]+) (.+)?(.*) HTTP')
	if method == nil then
		_, _, method, path = string.find(req.source, '([A-Z]+) (.+) HTTP')
	end
	local _GET = {}
	if (vars ~= nil and vars ~= '') then
		-- vars = urlDecode(vars)
		for k, v in string.gmatch(vars, '([^&]+)=([^&]*)&*') do
			_GET[k] = v
		end
	end
	
	req.method = method
	req.query = _GET
	req.path = path
	
	return true
end
--

-- Setup HTTP Server
Server = {
    _server = nil,
    _middleware = {{
        url = ".*",
        cb = parseHeader
    }}
}

function Server:use(url, cb)
    table.insert(self._middleware, #self._middleware, {
        url = url,
        cb = cb
    })
end

function Server:close()
    self._server:close()
    self._server = nil
end

function Server:listen(80)
    srv=net.createServer(net.TCP)
    srv:listen(80,function(conn)
        conn:on("receive", function(client, message)
            local res = Response:new(client)

            collectgarbage();
        end)
    end)
end
--

-- Setup Response
Response = {
    _client = nil,
    _status = nil,
    _type = nil
}

function Response:new(client)
    local table = {}
    setmetatable(table, self)
    self.__index = self
    table._client = client
    return table
end

function Response:status(status)
    self._status = status
end

function Response:send(body)
    self._status = self._status or 200
    self._type = self._type or "text/html"
    local buf = 'HTTP/1.1 ' .. self._status .. '\r\n'
    .. 'Content-Type: ' .. self._type .. '\r\n'
    .. 'Content-Length:' .. string.len(body) .. '\r\n' .. body

    self._client:send(string.sub(buf, 1, 512))
end
--

-- Setup Info
Info = {
    _path = nil,
    _method = nil,
    _query = nil
}

function Info:new(info)

end
--

-- Setup Endpoints
httpServer:use('/blink', function(req, res)
    -- local request = 
    if(_GET.pin == "ON")then
        gpio.write(led, gpio.HIGH);
    elseif(_GET.pin == "OFF")then
        gpio.write(led, gpio.LOW);
    end
	res:send('Blink ' .. gpio.read(led))
end)

--
