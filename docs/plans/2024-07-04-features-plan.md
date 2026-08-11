# Implementation Plan: CS2Toolkit Features

## Task 1: Random Flash Image from Directory
- **Goal**: Support selecting a directory for flash images and randomly displaying one.
- **Files**: `app/ui/pages/visual_page.py`, `app/logic/visual_handler.py`
- **Steps**:
  1. Add `browse_flash_folder` method to `VisualConfigDialog` and a UI button for it.
  2. Update `VisualHandler._update_config` to read the path.
  3. Modify `OverlayWindow.set_flash_image` or `OverlayWindow.update_flash` to check if `path` is a directory. If so, `os.listdir`, filter by image extensions, and `random.choice`.
- **Verify**: Select a folder, simulate GSI `flashed` event, verify different images appear.

## Task 2: "Grenade Thrown" Event
- **Goal**: Add "道具投出" event and track grenade ammo usage to trigger sounds.
- **Files**: `app/ui/event_dialog.py`, `app/ui/integrated_sound_page.py`
- **Steps**:
  1. Add "道具投出" to `event_items` in `AddEventDialog`.
  2. When selected, show grenade options ("所有道具", "闪光弹" (`weapon_flashbang`), etc.).
  3. In `IntegratedSoundPage.process_game_state` or `_process_weapon_events`, track grenade ammo. If ammo drops from N to N-1 (and state isn't just dropping the weapon), trigger `grenade_thrown` event with the specific grenade type.
- **Verify**: Configure sound for flashbang throw, simulate ammo decrease in GSI, verify sound plays.

## Task 3: Fix GSI Kill Reaction Delay
- **Goal**: Use `match_stats.kills` for visual kill icons.
- **Files**: `app/logic/visual_handler.py`
- **Steps**:
  1. In `VisualHandler.process_gsi`, replace `state.get('round_kills')` logic with `match_stats.get('kills')`.
  2. Maintain `_round_start_kills` which updates at `freezetime`.
  3. Calculate `current_round_kills = match_stats.kills - _round_start_kills`.
- **Verify**: Simulate kills via `match_stats` in GSI, verify kill icon appears immediately.

## Task 4: "GO Pet" Core & UI
- **Goal**: Create the GO Pet page and overlay.
- **Files**: `app/ui/pages/go_pet_page.py` (new), `app/ui/go_pet_overlay.py` (new), `app/main_window.py`
- **Steps**:
  1. Create `GoPetOverlay` (transparent, frameless) with dragging/resizing logic.
  2. Create `GoPetPage` UI with event configuration list and "Edit Mode" toggle.
  3. Register `GoPetPage` in `main_window.py` navigation.
- **Verify**: UI shows up in sidebar, overlay can be dragged and resized.

## Task 5: "GO Pet" Logic & Integration
- **Goal**: Hook GO Pet up to GSI events.
- **Files**: `app/logic/go_pet_manager.py` (new), `app/main_window.py`
- **Steps**:
  1. Create `GoPetManager` that receives GSI data.
  2. Implement priority queue for events (Death > Flash > etc.).
  3. Process GSI data to trigger state changes.
  4. Pass state changes to `GoPetOverlay` to update image/play sound.
- **Verify**: Simulate various GSI events, verify pet changes image and plays sound according to priority.
