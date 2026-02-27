-- =============================================================================
-- GM Command: .gemsocket
-- Teaches the Add Socket spell to the targeted player (or self if no target).
-- =============================================================================

local ADD_SOCKET_SPELL = 102126
local PRISMATIC_SLOT = 6

RegisterPlayerEvent(42, function(event, player, command)
    if command ~= "gemsocket" then return end

    if not player:IsGM() then
        player:SendBroadcastMessage("|cffff0000[GemSocket]|r GM only.")
        return false
    end

    local target = player:GetSelection()
    if not target or not target:IsPlayer() then
        target = player
    end

    local targetPlayer = target:ToPlayer()
    if not targetPlayer:HasSpell(ADD_SOCKET_SPELL) then
        targetPlayer:LearnSpell(ADD_SOCKET_SPELL)
        player:SendBroadcastMessage("|cff00ff00[GemSocket]|r Taught Add Socket to " .. targetPlayer:GetName() .. ".")
    else
        player:SendBroadcastMessage("|cff00ff00[GemSocket]|r " .. targetPlayer:GetName() .. " already knows Add Socket.")
    end

    return false
end)

-- =============================================================================
-- Spell hook: enforce 3-socket limit on Add Socket casts
-- =============================================================================

RegisterSpellEvent(ADD_SOCKET_SPELL, 1, function(event, spell)
    local item = spell:GetTarget()
    if not item then return end

    local baseCount = 0
    local entry = item:GetEntry()
    local q = WorldDBQuery("SELECT socketColor_1, socketColor_2, socketColor_3 FROM item_template WHERE entry = " .. entry)
    if q then
        for i = 0, 2 do
            if q:GetUInt32(i) > 0 then
                baseCount = baseCount + 1
            end
        end
    end
    local existingPrismatic = item:GetEnchantmentId(PRISMATIC_SLOT)
    if existingPrismatic and existingPrismatic > 0 then
        baseCount = baseCount + 1
    end

    if baseCount >= 3 then
        local caster = spell:GetCaster()
        if caster then
            caster:SendBroadcastMessage(
                "|cffff0000[GemSocket]|r " .. item:GetName() .. " already has " .. baseCount .. " sockets (max 3)."
            )
        end
        spell:Cancel()
    end
end)

print("[GemSocket] .gemsocket command and socket validation loaded.")
