-- pos: live position via /chatlog bridge + "typically found in" accumulator.
local MOV_GATE, TICK = 5, 0.5
local mod = Decades:RegisterModule("pos", { zoneTime = {}, home = "", lastZone = "", lastSub = "" })

local frame, acc = CreateFrame("Frame"), 0
local lastX, lastY

local function emit()
  local x, y, z = UnitPosition("player")
  if not x or not y then return end
  local zone, sub = GetZoneText(), (GetSubZoneText() or "")
  local moved = lastX == nil or (math.abs(x-lastX) + math.abs(y-lastY) > MOV_GATE)
  local zc = zone ~= mod.db.lastZone or sub ~= mod.db.lastSub
  -- zone-time accumulator (rollup, not events)
  local key = zone .. "/" .. sub
  mod.db.zoneTime[key] = (mod.db.zoneTime[key] or 0) + TICK
  if zc then
    mod.db.lastZone, mod.db.lastSub = zone, sub
    mod.db.home = GetBindLocation() or mod.db.home
  end
  if not (moved or zc) then return end
  lastX, lastY = x, y
  DEFAULT_CHAT_FRAME:AddMessage(string.format(
    "[DEC] POS|%s|%s|%d|%d|%d", zone, sub, math.floor(x), math.floor(y), math.floor(z or 0)))
end

frame:SetScript("OnUpdate", function(_, elapsed)
  acc = acc + elapsed
  if acc >= TICK then acc = 0; emit() end
end)
