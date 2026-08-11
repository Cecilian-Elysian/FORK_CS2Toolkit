# CS2Toolkit Features Design Document

## 1. Visual Settings: Random Flash Image from Directory
- **Goal:** Allow users to select a folder for the flash effect, and randomly pick an image from it when flashed.
- **UI Changes:** Add a "选择文件夹" (Select Folder) button next to the existing "选择图片" (Select Image) button in `VisualConfigDialog` (`app/ui/pages/visual_page.py`).
- **Logic Changes:**
  - Update `OverlayWindow._update_label_pixmap` or `set_flash_image` in `app/logic/visual_handler.py`.
  - When flashed, if `flash_path` is a directory, list valid images (`.png`, `.jpg`, `.jpeg`, `.bmp`) and use `random.choice` to pick one to display.

## 2. Sound Settings: "Grenade Thrown" Event
- **Goal:** Add a new event type for when a grenade is thrown, with specific grenade types.
- **UI Changes:**
  - Add "道具投出" (Grenade Thrown) to `event_items` in `AddEventDialog._setup_ui` (`app/ui/event_dialog.py`).
  - When selected, change the weapon combo box to a grenade selection combo box ("所有道具", "闪光弹", "烟雾弹", "高爆手雷", "燃烧弹/燃烧瓶", "诱饵弹").
- **Logic Changes:**
  - Track grenade ammo in `IntegratedSoundPage.process_game_state` or `_process_weapon_events` (`app/ui/integrated_sound_page.py`).
  - Compare previous weapon ammo with current weapon ammo. If ammo decreases for a grenade type (e.g., `weapon_flashbang`), trigger the `grenade_thrown` event.

## 3. Performance: Fix GSI Kill Reaction Delay
- **Goal:** Use `match_stats.kills` instead of `state.round_kills` for visual kill icons to reduce delay.
- **Logic Changes:**
  - In `VisualHandler.process_gsi` (`app/logic/visual_handler.py`), track `match_stats.kills`.
  - Maintain a round-start kill count to calculate current round kills. Reset this count at the start of a new round (e.g., `freezetime`).
  - Use the calculated round kills to trigger `show_kill_icon`.

## 4. New Feature: "GO Pet"
- **Goal:** Add a standalone desktop pet feature that reacts to GSI events.
- **Architecture:**
  - **Logic:** `app/logic/go_pet_manager.py` (handles GSI processing for the pet, priority logic).
  - **UI:**
    - `app/ui/pages/go_pet_page.py` (main settings page, added to left nav in `main_window.py`).
    - `app/ui/go_pet_overlay.py` (the transparent, draggable, resizable overlay window).
- **Features:**
  - Drag and drop pet window (when edit mode is on).
  - Resize pet (via slider in settings or mouse).
  - Event priority: Death > Flashed > Bomb Warning > Low Health > MVP > Win/Loss > Kill > Economy > Normal.
  - For each event, support single image/audio or folder for random selection.
