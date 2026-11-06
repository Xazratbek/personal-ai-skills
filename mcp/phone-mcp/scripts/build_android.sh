#!/usr/bin/env bash
# Builds an APK from a directory holding AndroidManifest.xml, src/ and res/, without Gradle.
# Usage: build_android.sh <source dir> <output apk>
set -euo pipefail

SRC="$1"
OUT="$2"
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}}"
BT="$(ls -d "$SDK"/build-tools/* | sort -V | tail -1)"
JAR="$SDK/platforms/android-34/android.jar"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KS="$ROOT/android-helper/debug.keystore"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

if [ ! -f "$KS" ]; then
  keytool -genkeypair -keystore "$KS" -storepass android -keypass android -alias phonemcp \
    -keyalg RSA -keysize 2048 -validity 36500 -dname "CN=Phone MCP Debug" >/dev/null 2>&1
fi

"$BT/aapt2" compile --dir "$SRC/res" -o "$WORK/res.zip"
"$BT/aapt2" link "$WORK/res.zip" -I "$JAR" --manifest "$SRC/AndroidManifest.xml" \
  --java "$WORK/gen" --min-sdk-version 26 --target-sdk-version 34 -o "$WORK/base.apk"

mkdir -p "$WORK/classes" "$WORK/dex"
find "$SRC/src" "$WORK/gen" -name '*.java' > "$WORK/sources.txt"
javac --release 11 -nowarn -classpath "$JAR" -d "$WORK/classes" @"$WORK/sources.txt" 2>/dev/null
"$BT/d8" --release --min-api 26 --lib "$JAR" --output "$WORK/dex" $(find "$WORK/classes" -name '*.class')
(cd "$WORK/dex" && zip -q -j "$WORK/base.apk" classes.dex)

"$BT/zipalign" -f 4 "$WORK/base.apk" "$WORK/aligned.apk"
"$BT/apksigner" sign --ks "$KS" --ks-pass pass:android --key-pass pass:android \
  --out "$OUT" "$WORK/aligned.apk"
rm -f "$OUT.idsig"
echo "built $OUT"
