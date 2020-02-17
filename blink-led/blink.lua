-- Pin definition 
local pin = 4
local status = gpio.HIGH
local duration = 1000    -- 1 second duration for timer

-- Initialising pin
gpio.mode(pin, gpio.OUTPUT)
gpio.write(pin, status)

-- Create an interval
tmr.create():alarm(duration, tmr.ALARM_AUTO, function()
    if status == gpio.LOW then
        status = gpio.HIGH
    else
        status = gpio.LOW
    end
    print(status)
    gpio.write(pin, status)
end)