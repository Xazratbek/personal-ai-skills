# phone-mcp

**Telefonni AI agentga bepul, to‘liq lokal boshqartirish:** iOS simulator, Android emulator va USB/Wi‑Fi orqali ulangan Android telefon. Hisob, API kalit yoki oylik to‘lov kerak emas.

**Let an AI agent drive phones for free, entirely on your Mac:** iOS simulators, Android emulators and Android phones over adb. No account, no API key, no subscription.

It is a drop-in local replacement for [Phone Harness MCP](https://github.com/phone-harness/mcp), which rents cloud phones. All 15 of its tools keep their names, parameters and meaning, and 26 more are added.

## Setup

You need Xcode for iOS, the Android SDK for Android, [uv](https://docs.astral.sh/uv/), and AXe for iOS touch:

```bash
brew install cameroncooke/axe/axe
```

Add it to Claude Code, for every project:

```bash
claude mcp add phone -s user -e ANDROID_HOME="$ANDROID_HOME" -- \
  uv --directory ~/programming/personal-ai-skills/mcp/phone-mcp run --quiet phone-mcp
```

Other MCP clients use the same command:

```json
{
  "mcpServers": {
    "phone": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/mcp/phone-mcp", "run", "--quiet", "phone-mcp"],
      "env": { "ANDROID_HOME": "/absolute/path/to/android/sdk" }
    }
  }
}
```

Then ask the agent to run `phone_doctor`, which reports anything missing and how to install it. `phone-mcp --port 8000` serves streamable HTTP instead. It has no sign-in, so it only ever binds to `127.0.0.1`.

## Tools

With one phone running, `device` can be left out. With several, pass its id or name.

### The same as Phone Harness

| Tool | Does |
| --- | --- |
| `phone_list_available_devices` | Running phones and their ids, and the phones you can start. |
| `phone_start_device` | Boot a simulator or emulator and wait until it is ready. `headless` runs it without a window. |
| `phone_stop_device` | Shut one down. |
| `phone_get_screen_size` | Screen size in tap coordinates. |
| `phone_take_screenshot` | JPEG of the screen. `annotate` numbers each element on it. |
| `phone_save_screenshot` | Write PNG, JPEG or WebP to a file. |
| `phone_list_elements_on_screen` | What is on screen, with centers to tap and refs. Falls back to reading the pixels. |
| `phone_click_on_screen_at_coordinates` | Tap. |
| `phone_long_press_on_screen_at_coordinates` | Press and hold. |
| `phone_swipe_on_screen` | Swipe in a direction. |
| `phone_type_keys` | Type into the focused field, in any language. `clear` empties it first. |
| `phone_press_button` | HOME, BACK, APP_SWITCHER, ENTER. |
| `phone_list_apps` | Installed apps. `include_system` adds the built-in ones. |
| `phone_launch_app` | Open by icon name or id. |
| `phone_get_foreground_app` | Which app is in front. |

### Added

| Group | Tools |
| --- | --- |
| Acting on elements | `phone_tap_element` (by text, id, type or ref), `phone_wait_for_element`, `phone_scroll_to_element`, `phone_wait_for_idle` |
| Gestures | `phone_double_tap`, `phone_drag` |
| Several steps at once | `phone_batch` |
| Apps | `phone_open_url` (web pages and deep links), `phone_install_app`, `phone_uninstall_app`, `phone_terminate_app`, `phone_clear_app_data`, `phone_set_permission` |
| Testing | `phone_get_logs`, `phone_start_recording`, `phone_stop_recording`, `phone_send_notification`, `phone_add_media` |
| The phone itself | `phone_set_appearance`, `phone_set_location`, `phone_set_orientation`, `phone_get_clipboard`, `phone_set_clipboard`, `phone_get_device_info` |
| Escape hatch and setup | `phone_shell`, `phone_doctor` |

## Where it differs from Phone Harness

**On purpose:**

- `device` is optional when only one phone is running.
- `minutes` on `phone_start_device` defaults to no limit. There is no bill to protect against, so a phone runs until it is stopped.
- `platform` no longer needs `kind`, and `ios`/`device` starts a simulator and says so.
- Taps on iOS use points and on Android pixels, the coordinate space each platform's own tools use.
- A screenshot is sized to the screen's coordinates whenever those fit in `max_size`, so what you see in the image is where to tap.
- iOS has a working `BACK` (the app's own back button, else the edge swipe), an app list and the foreground app.

**Defects in Phone Harness MCP that are fixed here**, found by reading its source at commit `b0572ff`:

| Where | Problem | Here |
| --- | --- | --- |
| `server.py:293`, `:308` | The docstring says a swipe starts at `(x, y)`, but the gesture is centered there, so a swipe from an edge travels half the distance. | It starts at `(x, y)`. |
| `server.py:296`, `:306` | With `x`, `y` and `distance` all given, the screen size is never fetched, so the upper bound is skipped and a swipe can leave the screen. | Both ends always stay on screen. |
| `server.py:249` | Any name not ending in `.png` gets JPEG bytes, so `shot.webp` holds a JPEG. | Real WebP, and an error for anything else. |
| `server.py:339`, `:343` | The system-app filter is hard-coded, so a phone full of built-in apps reports "No user apps are installed". | `include_system`. |
| `server.py:121` | Elements with no text are dropped, so icon buttons cannot be found. | They are listed, with their ids. |
| `screenshots.py:57` | The mapping factor is rounded to 3 digits, which is up to 4 px off at the bottom of a 2400 px screen. | 4 digits, and usually no factor at all. |

**Problems found while testing on real simulators**, which are handled here:

- iOS keystrokes change text: `'` becomes `’`, `--` becomes `—`, `...` becomes `…`. Anything keystrokes would alter is pasted, and the clipboard is restored. Read-back matches exactly.
- `adb shell input text` cannot send non-ASCII at all. A small helper keyboard (`android-helper/`, built from source here) commits Unicode and emoji. It is installed the first time it is needed and is enabled only for that one operation, and then the previous keyboard is restored.
- AXe's default tap misses SwiftUI toggles about half the time, and the middle of a toggle's row does nothing. Taps use real touch events, and `phone_tap_element` aims at the control itself.
- `simctl openurl` raises an `Open in "App"?` prompt on iOS 27 for custom schemes, which blocks the phone. It is accepted automatically.
- Each step of `axe batch` takes about 0.7 s to set up, which is past iOS's double-tap window. Two processes run side by side instead.
- Android's double tap has to land 40-300 ms apart, and `input tap` chained in one shell can land closer than that.
- `input text` reads `%s` as a space, so a literal `%s` is sent in two pieces.

## Limits

- **Real iPhones are not supported.** Driving one needs WebDriverAgent signed with an Apple developer account. Only Phone Harness's cloud iPhones cover this, and the simulator has no camera, cellular or real push service.
- **Real Android phones** go through the same adb code, but have only been tested against simulated `adb` output, as no phone was attached.
- **Simulators cannot be rotated** from outside Simulator.app, and `phone_set_orientation` says so.
- **Speed.** An Android element list takes about 3 s, because `uiautomator dump` waits for the screen to go idle. An iOS tap takes about 1 s, and an iOS list about 0.5 s.
- **`phone_shell`** runs anything the phone's shell can, so it can change or delete data on the phone.
- **Screens with no accessibility tree**, such as games, canvases, or on Android anything that never stops animating, fall back to Apple Vision OCR. That needs Xcode's command line tools and can misread a word.

## How it works

```
src/phone_mcp/
├── server.py        the tools
├── devices.py       which phones exist, starting and stopping them
├── elements.py      one element model, from either accessibility tree or OCR
├── screenshots.py   sizing, coordinate mapping, numbered boxes
├── ocr.py           Apple Vision, compiled on first use
└── drivers/
    ├── android.py   adb
    └── ios.py       simctl for the system, AXe for touch and the accessibility tree
android-helper/      the keyboard that types Unicode and reads the clipboard
```

The server runs one operation at a time per phone, since adb and AXe misbehave when they overlap, and every subprocess has a deadline.

## Testing

```bash
uv run pytest                     # no phone needed

bash scripts/build_fixtures.sh    # the test apps
uv run python tests/e2e/run_e2e.py --ios <udid> --android <serial> --lifecycle
```

The end-to-end run drives every tool through a real MCP client over stdio against a small test app, and checks each by reading the result back: the typed text from the field, the deep link from the app, the GPS fix from the app's own location listener. It installs and removes that app, so point it at a phone you do not mind changing. A failed step keeps a screenshot.

## License

Personal project, like the rest of this repository. [NOTICE](NOTICE) holds the MIT notice for what derives from Phone Harness MCP.
