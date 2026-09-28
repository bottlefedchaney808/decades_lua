-- data.lua: loads hub-pushed data and exposes it as Decades.Data.
Decades.Data = DecadesData or { generatedAt = "never" }

SLASH_DECSYNC1 = "/dec"
SlashCmdList["DECSYNC"] = function(msg)
  local db = DecadesSyncDB and DecadesSyncDB.core or {}
  DEFAULT_CHAT_FRAME:AddMessage(string.format(
    "DecadesSync v%s | %s-%s %s | data: %s (%d keys)",
    Decades.VERSION, db.name or "?", db.realm or "?", db.class or "?",
    tostring(Decades.Data.generatedAt),
    (function() local n = 0; for _ in pairs(Decades.Data) do n = n + 1 end return n end)()))
end
