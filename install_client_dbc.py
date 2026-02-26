#!/usr/bin/env python3
"""
Client DBC Install Script

Creates a client patch MPQ with custom DBC entries merged into the base data.

This script reads the WoW client's existing DBC files from its MPQ archives,
merges in custom entries from the custom_dbc/ directory, and produces a
numbered patch MPQ file. Your client's base data is not modified -- only
a new patch file is added.

Requires mpqcli (https://github.com/TheGrayDot/mpqcli) for MPQ operations.

Usage:
    python install_client_dbc.py <wow_data_directory> [--mpq-tool <path>]

Example:
    python install_client_dbc.py "C:\Games\WoW 3.3.5a\Data"
    python install_client_dbc.py /opt/wow/Data --mpq-tool /usr/local/bin/mpqcli
"""

import struct
import subprocess
import sys
import os
import shutil
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


DBC_MAGIC = b'WDBC'

# String field indices (same as install_server_dbc.py)
STRING_FIELDS = {
    'SkillLine.dbc': list(range(3, 19)) + list(range(20, 36)) + list(range(38, 54)),
    'Faction.dbc': list(range(23, 39)) + list(range(40, 56)),
    'SpellItemEnchantment.dbc': list(range(14, 30)),
    'Spell.dbc': (list(range(136, 152)) + list(range(153, 169))
                  + list(range(170, 186)) + list(range(187, 203))),
}


def read_dbc_file(filepath):
    """Read a DBC file and return header info, raw records, and string block."""
    with open(filepath, 'rb') as f:
        magic = f.read(4)
        if magic != DBC_MAGIC:
            raise ValueError(f"Invalid DBC magic in {filepath}: {magic}")
        record_count, field_count, record_size, string_block_size = (
            struct.unpack('<4I', f.read(16)))
        records = [f.read(record_size) for _ in range(record_count)]
        string_block = f.read(string_block_size)
    return {
        'record_count': record_count,
        'field_count': field_count,
        'record_size': record_size,
        'string_block_size': string_block_size,
    }, records, string_block


def write_dbc_file(filepath, header, records, string_block):
    """Write a DBC file."""
    with open(filepath, 'wb') as f:
        f.write(DBC_MAGIC)
        f.write(struct.pack('<I', len(records)))
        f.write(struct.pack('<I', header['field_count']))
        f.write(struct.pack('<I', header['record_size']))
        f.write(struct.pack('<I', len(string_block)))
        for record in records:
            f.write(record)
        f.write(string_block)


def find_mpq_tool(specified_path=None):
    """Find mpqcli executable."""
    if specified_path and os.path.exists(specified_path):
        return Path(specified_path)

    # Check same directory as this script
    script_dir = Path(__file__).parent
    for name in ['mpqcli.exe', 'mpqcli']:
        candidate = script_dir / name
        if candidate.exists():
            return candidate

    # Check PATH
    import shutil as sh
    found = sh.which('mpqcli')
    if found:
        return Path(found)

    return None


def find_locale_dir(data_dir):
    """Find the locale subdirectory (enUS, enGB, deDE, etc.)."""
    for entry in data_dir.iterdir():
        if entry.is_dir() and len(entry.name) == 4:
            # Check if it contains locale MPQ files
            if list(entry.glob('locale-*.MPQ')) or list(entry.glob('patch-*.MPQ')):
                return entry
    return None


def extract_dbc_from_mpq(mpq_path, dbc_name, output_dir, mpq_tool):
    """Extract a single DBC from an MPQ archive."""
    output_path = output_dir / 'DBFilesClient' / dbc_name
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(mpq_tool), 'extract', str(mpq_path),
        '-f', f'DBFilesClient\\{dbc_name}',
        '-o', str(output_dir),
        '-k'
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0 and output_path.exists()
    except Exception:
        return False


def find_base_dbc(dbc_name, data_dir, locale_dir, mpq_tool, temp_dir):
    """
    Find and extract a base DBC from client MPQ archives.

    Searches in priority order (highest patch wins):
    1. Locale patches (patch-enUS-3, patch-enUS-2, etc.)
    2. Main patches (patch-3, patch-2, patch)
    3. Locale base (locale-enUS.MPQ)
    4. Main base (common.MPQ, common-2.MPQ)
    """
    output_path = temp_dir / 'DBFilesClient' / dbc_name

    # Search locale patches first (highest number first)
    if locale_dir:
        locale_name = locale_dir.name  # e.g., "enUS"
        for i in range(5, -1, -1):
            if i > 0:
                mpq_name = f'patch-{locale_name}-{i}.MPQ'
            else:
                mpq_name = f'patch-{locale_name}.MPQ'
            mpq_path = locale_dir / mpq_name
            if mpq_path.exists():
                # Clean any previous extraction
                if output_path.exists():
                    output_path.unlink()
                if extract_dbc_from_mpq(mpq_path, dbc_name, temp_dir, mpq_tool):
                    return output_path

    # Search main patches
    for i in range(5, -1, -1):
        if i > 0:
            mpq_name = f'patch-{i}.MPQ'
        else:
            mpq_name = 'patch.MPQ'
        mpq_path = data_dir / mpq_name
        if mpq_path.exists():
            if output_path.exists():
                output_path.unlink()
            if extract_dbc_from_mpq(mpq_path, dbc_name, temp_dir, mpq_tool):
                return output_path

    # Search locale base
    if locale_dir:
        locale_name = locale_dir.name
        locale_mpq = locale_dir / f'locale-{locale_name}.MPQ'
        if locale_mpq.exists():
            if output_path.exists():
                output_path.unlink()
            if extract_dbc_from_mpq(locale_mpq, dbc_name, temp_dir, mpq_tool):
                return output_path

    # Search common MPQs
    for mpq_name in ['common-2.MPQ', 'common.MPQ']:
        mpq_path = data_dir / mpq_name
        if mpq_path.exists():
            if output_path.exists():
                output_path.unlink()
            if extract_dbc_from_mpq(mpq_path, dbc_name, temp_dir, mpq_tool):
                return output_path

    return None


def merge_custom_records(base_dbc_path, custom_dbc_path, output_path, dbc_filename):
    """Merge custom records into a base DBC and write the result."""
    base_header, base_records, base_strings = read_dbc_file(base_dbc_path)
    custom_header, custom_records, custom_strings = read_dbc_file(custom_dbc_path)

    if base_header['record_size'] != custom_header['record_size']:
        print(f"  ERROR: Record size mismatch for {dbc_filename}")
        return 0

    record_size = base_header['record_size']
    fields_per_record = record_size // 4
    string_fields = STRING_FIELDS.get(dbc_filename, [])
    base_string_len = len(base_strings)

    existing_ids = set()
    for record in base_records:
        existing_ids.add(struct.unpack('<I', record[:4])[0])

    merged_records = list(base_records)
    added = 0

    for record in custom_records:
        record_id = struct.unpack('<I', record[:4])[0]
        if record_id in existing_ids:
            continue

        if string_fields:
            fields = list(struct.unpack(f'<{fields_per_record}I', record))
            for fi in string_fields:
                if fi < fields_per_record and fields[fi] != 0:
                    fields[fi] += base_string_len
            record = struct.pack(f'<{fields_per_record}I', *fields)

        merged_records.append(record)
        added += 1

    merged_strings = base_strings + custom_strings
    write_dbc_file(output_path, base_header, merged_records, merged_strings)
    return added


def get_next_patch_number(data_dir):
    """Find the next available patch-N.MPQ number."""
    max_num = 3  # Blizzard patches go up to patch-3
    for mpq in data_dir.glob('patch-*.MPQ'):
        name = mpq.stem.lower()
        if name.startswith('patch-'):
            try:
                num = int(name.replace('patch-', ''))
                max_num = max(max_num, num)
            except ValueError:
                continue
    return max_num + 1


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Install client-side DBC patches for WoW 3.3.5a')
    parser.add_argument('data_dir', help='Path to WoW client Data directory')
    parser.add_argument('--mpq-tool', help='Path to mpqcli executable')
    parser.add_argument('--patch-name', help='Output patch filename (e.g., patch-6)')
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"ERROR: Data directory does not exist: {data_dir}")
        sys.exit(1)

    mpq_tool = find_mpq_tool(args.mpq_tool)
    if not mpq_tool:
        print("ERROR: mpqcli not found.")
        print("Download from: https://github.com/TheGrayDot/mpqcli")
        print("Place mpqcli in the same directory as this script, or use --mpq-tool")
        sys.exit(1)
    print(f"Using MPQ tool: {mpq_tool}")

    locale_dir = find_locale_dir(data_dir)
    if locale_dir:
        print(f"Found locale: {locale_dir.name}")
    else:
        print("Warning: No locale directory found, some DBCs may not be available")

    # Load manifest
    script_dir = Path(__file__).parent
    manifest_path = script_dir / 'id_manifest.yaml'
    if not manifest_path.exists():
        print(f"ERROR: id_manifest.yaml not found at {manifest_path}")
        sys.exit(1)

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = yaml.safe_load(f)

    dbc_entries = manifest.get('dbc_entries', {})
    if not dbc_entries:
        print("No dbc_entries found in manifest. Nothing to install.")
        return

    custom_dbc_dir = script_dir / 'custom_dbc'
    if not custom_dbc_dir.exists():
        print(f"ERROR: custom_dbc/ directory not found at {custom_dbc_dir}")
        sys.exit(1)

    # Create temp directory for extraction and staging
    temp_root = tempfile.mkdtemp(prefix='wow_dbc_install_')
    extract_dir = Path(temp_root) / 'extract'
    staging_dir = Path(temp_root) / 'staging' / 'DBFilesClient'
    staging_dir.mkdir(parents=True)

    try:
        print(f"\nMerging custom DBC entries...")
        total_added = 0

        for dbc_filename in sorted(dbc_entries.keys()):
            custom_ids = dbc_entries[dbc_filename]
            if not custom_ids:
                continue

            custom_dbc_path = custom_dbc_dir / dbc_filename
            if not custom_dbc_path.exists():
                print(f"  Warning: {dbc_filename} not found in custom_dbc/, skipping")
                continue

            print(f"  {dbc_filename}: {len(custom_ids)} custom entries")

            # Extract base DBC from client MPQs
            base_path = find_base_dbc(
                dbc_filename, data_dir, locale_dir, mpq_tool, extract_dir)

            if not base_path:
                print(f"    Warning: Base {dbc_filename} not found in client MPQs")
                print(f"    Copying custom-only DBC (may not work without base data)")
                shutil.copy2(str(custom_dbc_path), str(staging_dir / dbc_filename))
                continue

            # Merge custom records into base
            output_path = staging_dir / dbc_filename
            added = merge_custom_records(
                base_path, custom_dbc_path, output_path, dbc_filename)
            total_added += added
            print(f"    Added {added} custom entries")

        if not any(staging_dir.glob('*.dbc')):
            print("\nNo DBC files to pack. Nothing to install.")
            return

        # Determine patch name
        if args.patch_name:
            patch_name = args.patch_name
        else:
            next_num = get_next_patch_number(data_dir)
            patch_name = f'patch-{next_num}'

        mpq_output = data_dir / f'{patch_name}.MPQ'
        print(f"\nCreating client patch: {mpq_output}")

        # Remove existing if present
        if mpq_output.exists():
            mpq_output.unlink()

        # Create MPQ using mpqcli
        staging_root = staging_dir.parent
        cmd = [str(mpq_tool), 'create', '-o', str(mpq_output), str(staging_root)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"ERROR: Failed to create MPQ: {result.stderr}")
            sys.exit(1)

        print(f"Created {mpq_output.name}")
        print(f"\nInstall complete. Added {total_added} total custom entries.")
        print(f"\nNext steps:")
        print(f"  1. Delete the WoW client's Cache/ folder")
        print(f"  2. Restart the WoW client")

    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == '__main__':
    main()
