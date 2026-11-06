[app]
title = Тапалка-собачка
package.name = tapdog
package.domain = org.tapdog
source.dir = .
source.include_exts = py,json,png,jpg,kv,atlas
version = 1.0.0
requirements = python3,kivy
orientation = portrait
fullscreen = 1

# Поддержка обычных Android-телефонов, включая 32-битные ARM-устройства.
android.archs = armeabi-v7a, arm64-v8a
android.minapi = 23

# Разрешения игре не нужны: она работает офлайн.

[buildozer]
log_level = 2
warn_on_root = 1