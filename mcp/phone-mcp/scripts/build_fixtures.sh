#!/usr/bin/env bash
# Builds the helper IME (shipped with the package) and the two test apps used by tests/e2e.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/tests/fixtures/build"
mkdir -p "$BUILD"

bash "$ROOT/scripts/build_android.sh" "$ROOT/android-helper" "$ROOT/src/phone_mcp/assets/phone_mcp_ime.apk"
bash "$ROOT/scripts/build_android.sh" "$ROOT/tests/fixtures/android" "$BUILD/fixture.apk"

APP="$BUILD/PhoneMcpFixture.app"
rm -rf "$APP"
mkdir -p "$APP"
cp "$ROOT/tests/fixtures/ios/Info.plist" "$APP/Info.plist"
xcrun --sdk iphonesimulator swiftc -parse-as-library \
  -target arm64-apple-ios17.0-simulator \
  -sdk "$(xcrun --sdk iphonesimulator --show-sdk-path)" \
  "$ROOT/tests/fixtures/ios/App.swift" -o "$APP/PhoneMcpFixture"
codesign --force --sign - "$APP" >/dev/null 2>&1
echo "built $APP"
