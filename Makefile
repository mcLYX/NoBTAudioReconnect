THEOS_PACKAGE_SCHEME = rootless
TARGET := iphone:clang:16.5:16.0
INSTALL_TARGET_PROCESSES = Client HTGame-IOS-Shipping

include $(THEOS)/makefiles/common.mk

TWEAK_NAME = NoBTAudioReconnect
NoBTAudioReconnect_FILES = Tweak.x
NoBTAudioReconnect_CFLAGS = -fobjc-arc
NoBTAudioReconnect_LDFLAGS = -undefined dynamic_lookup

include $(THEOS_MAKE_PATH)/tweak.mk
