-- inventory: bag + bank item-count rollups. Bank read only while the frame is open.
local mod = Decades:RegisterModule("inventory", { bags = {}, bank = {}, scannedAt = 0 })

local function scanBags(tbl, bagIds)
  wipe(tbl)
  for _, bag in ipairs(bagIds) do
    for slot = 1, GetContainerNumSlots(bag) do
      local link = GetContainerItemLink(bag, slot)
      if link then
        local _, count = GetContainerItemInfo(bag, slot)
        local itemID = link:match("item:(%d+)")
        if itemID then
          local key = itemID
          tbl[key] = (tbl[key] or 0) + (count or 1)
        end
      end
    end
  end
end

local f = CreateFrame("Frame")
f:RegisterEvent("BAG_UPDATE_DELAYED")
f:RegisterEvent("BANKFRAME_OPENED")
f:SetScript("OnEvent", function(_, event)
  if event == "BAG_UPDATE_DELAYED" then
    scanBags(mod.db.bags, {0,1,2,3,4})
    mod.db.scannedAt = time()
  elseif event == "BANKFRAME_OPENED" then
    scanBags(mod.db.bank, {5,6,7,8,9,10}) -- bank bags + reagent; bags keyring 11 on clients that have it
    scanBags(mod.db.bags, {0,1,2,3,4})
    mod.db.scannedAt = time()
  end
end)
