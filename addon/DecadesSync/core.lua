-- DecadesSync core: namespace, module registry, SavedVariables bootstrap.
Decades = Decades or {}
Decades.VERSION = "0.1.0"

Decades.modules = Decades.modules or {}

-- Register a module: defaults merged under DecadesSyncDB[name] on login.
-- mod.OnEvent(frame, event, ...) and mod.OnUpdate(elapsed) are optional.
function Decades:RegisterModule(name, defaults)
  local mod = { name = name, defaults = defaults or {} }
  self.modules[name] = mod
  return mod
end

local frame = CreateFrame("Frame")

local function initCharDB()
  DecadesSyncDB = DecadesSyncDB or {}
  for name, mod in pairs(Decades.modules) do
    local db = DecadesSyncDB[name]
    if db == nil then
      db = {}
      DecadesSyncDB[name] = db
    end
    mod.db = db
    for k, v in pairs(mod.defaults) do
      if db[k] == nil then db[k] = v end
    end
  end
end

frame:RegisterEvent("ADDON_LOADED")
frame:RegisterEvent("PLAYER_LOGIN")
frame:SetScript("OnEvent", function(self, event, arg1)
  if event == "ADDON_LOADED" and arg1 == "DecadesSync" then
    initCharDB()
  elseif event == "PLAYER_LOGIN" then
    -- core facts, refreshed every login
    local _, class = UnitClass("player")
    local db = DecadesSyncDB and DecadesSyncDB.core
    if db then
      db.name = UnitName("player")
      db.realm = GetRealmName()
      db.class = class
      db.level = UnitLevel("player")
      db.guild, _, db.guildRankIndex = GetGuildInfo("player")
      db.addonVersion = Decades.VERSION
      db.lastLogin = date("%Y-%m-%dT%H:%M:%S")
    end
  end
end)
