[app]
title = GENESIS Lite
package.name = genesislite
package.domain = com.genesis
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0

requirements = python3,kivy,aiohttp,asyncio

orientation = portrait
fullscreen = 0

android.permissions = CAMERA, RECORD_AUDIO, INTERNET, MODIFY_AUDIO_SETTINGS, ACCESS_NETWORK_STATE
android.features = android.hardware.usb.host
android.api = 33
android.minapi = 21
android.ndk_api = 21

[buildozer]
log_level = 2
warn_on_root = 1
