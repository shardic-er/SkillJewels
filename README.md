# Skill Jewels

Version 0.1.279 | TrinityCore 3.3.5a + Eluna Lua Engine

Cross-class spell learning through gem socketing. Players socket gem items into
gear to learn spells from other WoW classes. Removing the gem or unequipping the
item revokes the spell -- no permanent class blending.

**607 rank-chain gems** cover all 10 classes (Druid, Shaman, Paladin, Hunter,
Warlock, Priest, Warrior, Death Knight, Mage, Rogue). Each gem teaches the
highest spell rank available for the player's level and auto-upgrades on
level-up. Gems use real vanilla spell IDs, so talents, cooldowns, and C++
spell scripts all work correctly.

- **Trainer gems** (Rare/blue quality, 426 gems): Spells normally learned from
  class trainers
- **Talent gems** (Epic/purple quality, 170 gems): Spells from talent trees
- **Multi-spell gems** (Legendary quality, 2 gems): Hunter Pets (5 spells) and
  Warlock Metamorphosis (5 spells)

**Spell dependencies** are handled automatically. Gems that require a form,
stance, or reagent-producing spell (e.g. Maul needs Bear Form, Taunt needs
Defensive Stance, Soul Fire needs Drain Soul) auto-teach the dependency
alongside the gem spell and auto-remove it when no longer needed.

**Same-class blocking** prevents players from socketing gems for their own class.
Level requirements are enforced at socket time via a Lua packet hook.

Cross-class spells appear on a dedicated **Skill Jewels** spellbook tab (requires
client DBC patch). The tab is visible whenever at least one cross-class gem is
equipped.

#### Compatibility

This module is self-contained and installable on any stock TrinityCore 3.3.5a
server with Eluna (including ChromieCraft). Custom content uses ID ranges
starting at 100,000+ for items and 5,000+ for enchantments/gem properties --
well above vanilla maximums, so there are no conflicts with base game data.
The DBC install scripts merge custom entries into your server's existing DBC
files without modifying base records.

If you run other custom content mods that also use the 100,000+ ID range,
check `id_manifest.yaml` for the exact IDs used by this module.

#### Chat Commands

- `.randomgem` -- Adds a random gem to bags (testing)
- `.cleanspells` -- Removes orphaned cross-class spells not backed by equipped gems
- `.dirtyspells` -- Teaches all cross-class spells at best rank (testing; cleaned up on next equip/unequip)

## Requirements

- TrinityCore 3.3.5a with [Eluna Lua Engine](https://github.com/ElunaLuaEngine/Eluna)
- MySQL/MariaDB (world database)
- Python 3.8+ with PyYAML (for DBC install/uninstall scripts)
- WoW 3.3.5a client (for the client patch)

## Contents

- `install.sql` - Database installation script
- `uninstall.sql` - Database uninstallation script
- `server_dbc/` - Server-side DBC files
- `patch-6.MPQ` - Client patch
- `uninstall_server_dbc.py` - Removes custom entries from server DBCs
- `lua_scripts/` - Eluna Lua scripts
- `lua_manifest.txt` - List of installed Lua scripts (for uninstall)
- `id_manifest.yaml` - ID assignments for this version

## Installation

Follow these steps in order:

### 1. Install Database Content

Run the SQL installation script against your TrinityCore world database:

```bash
mysql -u root -p world < install.sql
```

Or use your preferred MySQL client to execute `install.sql`.

### 2. Install Server DBCs

Copy the server DBC files to your TrinityCore server's dbc folder:

```bash
# Example (adjust paths for your setup):
copy server_dbc\FactionTemplate.dbc <path_to_server>\dbc\
```

The server must be restarted to load the new DBC files.

### 3. Install Client Patch

Copy the client patch to your WoW client's Data folder:

```bash
# Example (adjust paths for your setup):
copy patch-6.MPQ <path_to_wow>\Data\
```

Clear the WoW client cache folder before launching.

### Install Lua Scripts (Eluna)

Copy the lua_scripts folder contents to your server's lua_scripts directory:

```bash
xcopy /E /Y lua_scripts\* <path_to_server>\lua_scripts\
```

The server must be restarted (or use `.reload eluna`) to load new scripts.

### Restart

- Restart the TrinityCore worldserver
- Clear client cache and restart WoW client

## Uninstallation

Follow these steps in reverse order:

### 1. Run Database Uninstall

```bash
mysql -u root -p world < uninstall.sql
```

### 2. Remove Server DBC Entries

Run the uninstall script against your server's dbc folder:

```bash
python uninstall_server_dbc.py <path_to_server>\dbc
```

This removes only our custom entries, preserving all base game data.

### 3. Remove Client Patch

Delete the client patch from your WoW Data folder:

```bash
del <path_to_wow>\Data\patch-6.MPQ
```

### Remove Lua Scripts

Delete the installed Lua scripts listed in lua_manifest.txt from your server's
lua_scripts directory.

### Restart

- Restart the TrinityCore worldserver
- Clear client cache and restart WoW client

## ID Assignments

See `id_manifest.yaml` for the complete list of IDs assigned in this version.
These IDs are stable across builds - once assigned, an ID is never reused.
