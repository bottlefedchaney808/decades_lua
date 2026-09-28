-- inventory: bag + bank item-count rollups. Bank read only while the frame is open.
-- Classic/Forever 1.60: no wipe(), no BAG_UPDATE_DELAYED. BAG_UPDATE fires a
-- lot, so we dirty-flag and scan at most once per SCAN_GAP seconds.
local SCAN_GAP = 0.5
local BANK_CONTAINER = -1 -- vanilla main bank slots
local mod = Decades:RegisterModule("inventory", { bags = {}, bank = {}, scannedAt = 0 })

local function clear(tbl)
  for k in pairs(tbl) do tbl[k] = nil end
end

local function scanBags(tbl, bagIds)
  clear(tbl)
  for _, bag in ipairs(bagIds) do
    local slots = GetContainerNumSlots(bag)
    if slots and slots > 0 then
      for slot = 1, slots do
        local link = GetContainerItemLink(bag, slot)
        if link then
          local _, count = GetContainerItemInfo(bag, slot)
          local itemID = link:match("item:(%d+)")
          if itemID then
            tbl[itemID] = (tbl[itemID] or 0) + (count or 1)
          end
        end
      end
    end
  end
end

local dirty, acc, bankOpen = false, 0, false
local BANK_BAGS = {BANK_CONTAINER, 5, 6, 7, 8, 9, 10}
local CHAR_BAGS = {0, 1, 2, 3, 4}
local f = CreateFrame("Frame")
f:RegisterEvent("BAG_UPDATE")
f:RegisterEvent("BANKFRAME_OPENED")
f:RegisterEvent("BANKFRAME_CLOSED")
f:RegisterEvent("PLAYER_ENTERING_WORLD")
f:SetScript("OnEvent", function(_, event)
  if not mod.db then return end
  if event == "BANKFRAME_OPENED" then
    bankOpen = true
    scanBags(mod.db.bank, BANK_BAGS)
    scanBags(mod.db.bags, CHAR_BAGS)
    mod.db.scannedAt = time()
    dirty = false
  elseif event == "BANKFRAME_CLOSED" then
    -- last scan while slots are still readable
    scanBags(mod.db.bank, BANK_BAGS)
    scanBags(mod.db.bags, CHAR_BAGS)
    mod.db.scannedAt = time()
    bankOpen = false
    dirty = false
  elseif event == "PLAYER_ENTERING_WORLD" then
    scanBags(mod.db.bags, CHAR_BAGS)
    mod.db.scannedAt = time()
  else
    dirty = true -- BAG_UPDATE
  end
end)
f:SetScript("OnUpdate", function(_, elapsed)
  if not dirty or not mod.db then return end
  acc = acc + elapsed
  if acc < SCAN_GAP then return end
  acc = 0
  dirty = false
  scanBags(mod.db.bags, CHAR_BAGS)
  if bankOpen then
    scanBags(mod.db.bank, BANK_BAGS)
  end
  mod.db.scannedAt = time()
end)
