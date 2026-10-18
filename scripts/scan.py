#!/usr/bin/env python3
"""Static fact gatherer for App Store and Google Play compliance audits.

Usage:
  scan.py <repo-or-app-dir> [--json out.json]   scan every mobile app in a repo
  scan.py --find [<dir> ...]                    list mobile app dirs under dirs

Stdlib only, read-only. Each finding is a lead the auditor verifies by reading
the cited code. It is never a verdict on its own.
Supports Flutter, React Native / Expo and native Android/iOS projects.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {
    "build", "Pods", "node_modules", "DerivedData", "dist", "coverage", "ephemeral",
    "Flutter", "test", "tests", "integration_test", "androidTest", "__tests__", "testing",
    "tool", "tools", "scripts", "web", "macos", "linux", "windows", "docs", "example",
}
CODE_EXT = {".dart", ".kt", ".java", ".swift", ".m", ".mm", ".ts", ".tsx", ".js", ".jsx"}
UI_EXT = CODE_EXT | {".arb", ".strings", ".xml", ".json"}
TEXT_EXT = UI_EXT | {".plist", ".yaml", ".yml"}
GENERATED = (".g.dart", ".freezed.dart", ".mocks.dart", ".gr.dart", ".config.dart")
MAX_FILE = 1_500_000
COMMENT = re.compile(r"^\s*(//|/\*|\*|#)")
MAX_EVIDENCE = 6
LEVELS = ("CRITICAL", "IMPORTANT", "SUGGESTION")
AD_NAME = re.compile(r"(^|[_-])ads?([_-]|$)|admob|levelplay|ironsource|applovin|vungle|liftoff|inmobi|chartboost|pangle|mintegral|bigo_ads|digital_turbine|fyber", re.I)

# ---------------------------------------------------------------- catalogs --
# Package names across pub.dev and npm. A category only says the capability is
# linked, the auditor still decides whether the app uses it.

ADS = {
    "google_mobile_ads", "ironsource_mediation", "unity_levelplay_mediation", "unity_ads_plugin",
    "applovin_max", "facebook_audience_network", "appodeal_flutter", "yandex_mobileads",
    "easy_ads_flutter", "gma_mediation_unity", "gma_mediation_applovin", "gma_mediation_meta",
    "gma_mediation_ironsource", "react-native-google-mobile-ads", "react-native-unity-ads",
    "react-native-applovin-max", "react-native-fbads",
}
TRACKING = {
    "appsflyer_sdk", "adjust_sdk", "facebook_app_events", "flutter_facebook_sdk", "flutter_branch_sdk",
    "singular_flutter_sdk", "kochava_tracker", "react-native-appsflyer", "react-native-adjust",
    "react-native-fbsdk-next", "react-native-branch",
}
ANALYTICS = {
    "firebase_analytics", "mixpanel_flutter", "amplitude_flutter", "posthog_flutter", "sentry_flutter",
    "firebase_crashlytics", "datadog_flutter_plugin", "clarity_flutter", "@react-native-firebase/analytics",
    "@amplitude/analytics-react-native", "mixpanel-react-native", "posthog-react-native", "@sentry/react-native",
}
ATT = {"app_tracking_transparency", "react-native-tracking-transparency", "expo-tracking-transparency"}
THIRD_PARTY_LOGIN = {
    "google_sign_in", "flutter_facebook_auth", "twitter_login", "flutter_line_sdk", "kakao_flutter_sdk",
    "firebase_ui_oauth_google", "firebase_ui_oauth_facebook", "@react-native-google-signin/google-signin",
}
APPLE_LOGIN = {
    "sign_in_with_apple", "the_apple_sign_in", "firebase_ui_oauth_apple",
    "@invertase/react-native-apple-authentication", "expo-apple-authentication",
}
ACCOUNT_BACKENDS = {
    "firebase_auth", "supabase_flutter", "amplify_auth_cognito", "appwrite", "pocketbase",
    "parse_server_sdk_flutter", "@react-native-firebase/auth", "@supabase/supabase-js",
}
IAP = {
    "purchases_flutter", "purchases_ui_flutter", "in_app_purchase", "flutter_inapp_purchase", "adapty_flutter",
    "qonversion_flutter", "superwallkit_flutter", "glassfy_flutter", "react-native-purchases",
    "react-native-iap", "expo-in-app-purchases", "react-native-adapty",
}
EXTERNAL_PAY = {
    "flutter_stripe", "iyzico", "iyzipay", "flutter_paypal", "razorpay_flutter", "flutter_braintree",
    "@stripe/stripe-react-native", "react-native-razorpay",
}
CHAT_UGC = {
    "stream_chat_flutter", "stream_chat", "flutter_chat_ui", "flutter_chat_core", "dash_chat_2",
    "sendbird_chat_sdk", "cometchat_chat_uikit", "zego_uikit_prebuilt_call", "agora_rtc_engine",
    "tencent_cloud_chat", "react-native-gifted-chat", "stream-chat-react-native",
}
AI = {
    "firebase_ai", "firebase_vertexai", "google_generative_ai", "dart_openai", "openai_dart", "langchain",
    "langchain_openai", "langchain_google", "anthropic_sdk_dart", "mistralai_dart", "flutter_gemini",
    "openai", "@google/generative-ai", "@google/genai", "@anthropic-ai/sdk", "replicate",
}
REMOTE_CODE = {
    "shorebird_code_push", "flutter_eval", "dart_eval", "flutter_dynamic_widget", "rfw", "stac", "mirai",
    "react-native-code-push", "expo-updates", "@hot-updater/react-native", "@revopush/react-native-code-push",
}
REMOTE_CONFIG = {"firebase_remote_config", "@react-native-firebase/remote-config", "flagsmith",
                 "launchdarkly_flutter_client_sdk", "statsig"}
WEBVIEW = {"webview_flutter", "flutter_inappwebview", "react-native-webview"}
PUSH = {"firebase_messaging", "onesignal_flutter", "flutter_local_notifications", "awesome_notifications",
        "@react-native-firebase/messaging", "react-native-onesignal", "expo-notifications", "@notifee/react-native"}
HEALTH = {"health", "flutter_health_connect", "react-native-health", "react-native-health-connect"}
RECORDERS = {"record", "flutter_sound", "audio_waveforms", "flutter_screen_recording",
             "react-native-audio-recorder-player"}
CONTACTS = {"flutter_contacts", "contacts_service", "fast_contacts", "react-native-contacts", "expo-contacts"}
LOCATION = {"geolocator", "location", "background_location", "flutter_background_geolocation",
            "react-native-geolocation-service", "expo-location", "react-native-background-geolocation"}

# plugin -> Info.plist keys it needs at runtime
PLIST_NEEDS = {
    "camera": ["NSCameraUsageDescription"],
    "mobile_scanner": ["NSCameraUsageDescription"],
    "qr_code_scanner_plus": ["NSCameraUsageDescription"],
    "image_picker": ["NSPhotoLibraryUsageDescription", "NSCameraUsageDescription"],
    "wechat_assets_picker": ["NSPhotoLibraryUsageDescription"],
    "photo_manager": ["NSPhotoLibraryUsageDescription"],
    "gal": ["NSPhotoLibraryAddUsageDescription"],
    "image_gallery_saver_plus": ["NSPhotoLibraryAddUsageDescription"],
    "geolocator": ["NSLocationWhenInUseUsageDescription"],
    "location": ["NSLocationWhenInUseUsageDescription"],
    "record": ["NSMicrophoneUsageDescription"],
    "flutter_sound": ["NSMicrophoneUsageDescription"],
    "audio_waveforms": ["NSMicrophoneUsageDescription"],
    "speech_to_text": ["NSSpeechRecognitionUsageDescription", "NSMicrophoneUsageDescription"],
    "flutter_contacts": ["NSContactsUsageDescription"],
    "contacts_service": ["NSContactsUsageDescription"],
    "fast_contacts": ["NSContactsUsageDescription"],
    "local_auth": ["NSFaceIDUsageDescription"],
    "flutter_blue_plus": ["NSBluetoothAlwaysUsageDescription"],
    "flutter_reactive_ble": ["NSBluetoothAlwaysUsageDescription"],
    "device_calendar": ["NSCalendarsFullAccessUsageDescription"],
    "health": ["NSHealthShareUsageDescription"],
    "app_tracking_transparency": ["NSUserTrackingUsageDescription"],
    "nfc_manager": ["NFCReaderUsageDescription"],
    "pedometer": ["NSMotionUsageDescription"],
}

# permission_handler Dart enum -> Podfile macro. Without the macro the iOS
# implementation is compiled out and request() always returns denied.
PH_MACROS = {
    "camera": "PERMISSION_CAMERA", "photos": "PERMISSION_PHOTOS", "photosAddOnly": "PERMISSION_PHOTOS_ADD_ONLY",
    "microphone": "PERMISSION_MICROPHONE", "location": "PERMISSION_LOCATION",
    "locationWhenInUse": "PERMISSION_LOCATION", "locationAlways": "PERMISSION_LOCATION",
    "contacts": "PERMISSION_CONTACTS", "calendar": "PERMISSION_EVENTS", "calendarFullAccess": "PERMISSION_EVENTS",
    "calendarWriteOnly": "PERMISSION_EVENTS", "reminders": "PERMISSION_REMINDERS",
    "speech": "PERMISSION_SPEECH_RECOGNIZER", "appTrackingTransparency": "PERMISSION_APP_TRACKING_TRANSPARENCY",
    "bluetooth": "PERMISSION_BLUETOOTH", "sensors": "PERMISSION_SENSORS", "notification": "PERMISSION_NOTIFICATIONS",
    "mediaLibrary": "PERMISSION_MEDIA_LIBRARY", "criticalAlerts": "PERMISSION_CRITICAL_ALERTS",
}

# Android permissions with a Play policy behind them: name -> (level, note)
ANDROID_RESTRICTED = {
    "READ_CALL_LOG": ("CRITICAL", "SMS and Call Log policy. Phone-call account verification stops being a permitted use on 2027-01-27"),
    "WRITE_CALL_LOG": ("CRITICAL", "SMS and Call Log policy. Rejected unless the app is the default dialer"),
    "PROCESS_OUTGOING_CALLS": ("CRITICAL", "SMS and Call Log policy"),
    "READ_SMS": ("CRITICAL", "SMS and Call Log policy. For OTP use the SMS Retriever or SMS User Consent API"),
    "RECEIVE_SMS": ("CRITICAL", "SMS and Call Log policy"),
    "SEND_SMS": ("CRITICAL", "SMS and Call Log policy"),
    "RECEIVE_MMS": ("CRITICAL", "SMS and Call Log policy"),
    "MANAGE_EXTERNAL_STORAGE": ("CRITICAL", "All files access. Only file managers, backup and antivirus apps. Use SAF or MediaStore"),
    "QUERY_ALL_PACKAGES": ("IMPORTANT", "Package visibility policy. Declare narrow <queries> instead"),
    "REQUEST_INSTALL_PACKAGES": ("IMPORTANT", "Only when installing packages is the core purpose"),
    "ACCESS_BACKGROUND_LOCATION": ("CRITICAL", "Background location needs a Console declaration, a video and a prominent disclosure"),
    "READ_MEDIA_IMAGES": ("IMPORTANT", "Photo and Video Permissions policy. One-off picks must use the Photo Picker"),
    "READ_MEDIA_VIDEO": ("IMPORTANT", "Photo and Video Permissions policy. One-off picks must use the Photo Picker"),
    "READ_EXTERNAL_STORAGE": ("SUGGESTION", "No effect on targetSdk 33+. Photo Picker or SAF"),
    "WRITE_EXTERNAL_STORAGE": ("SUGGESTION", "No effect on targetSdk 30+. MediaStore or app-specific dirs"),
    "READ_CONTACTS": ("IMPORTANT", "Contacts policy (2027-01-27): use the Android Contact Picker unless broad access is core"),
    "WRITE_CONTACTS": ("IMPORTANT", "Contacts policy (2027-01-27)"),
    "SCHEDULE_EXACT_ALARM": ("IMPORTANT", "Exact alarms: use inexact alarms unless timing is core functionality"),
    "USE_EXACT_ALARM": ("CRITICAL", "USE_EXACT_ALARM is only for alarm clock and calendar apps"),
    "USE_FULL_SCREEN_INTENT": ("IMPORTANT", "Full-screen intents are for calls and alarms. Others need a declaration and user grant"),
    "BIND_ACCESSIBILITY_SERVICE": ("CRITICAL", "Accessibility API policy: declaration and prominent disclosure"),
    "SYSTEM_ALERT_WINDOW": ("SUGGESTION", "Overlay permission needs a justification"),
    "ACCESS_FINE_LOCATION": ("SUGGESTION", "Is precise location needed? On Android 17 the location button is the recommended minimum scope"),
    "BLUETOOTH_SCAN": ("SUGGESTION", "Without neverForLocation the scan counts as location access"),
    "AD_ID": ("SUGGESTION", "Advertising ID: declare in Data safety, remove for child audiences"),
    "FOREGROUND_SERVICE_LOCATION": ("IMPORTANT", "FGS location needs a declaration. Geofencing is no longer an approved use on 2027-01-27"),
    "FOREGROUND_SERVICE_MEDIA_PROJECTION": ("IMPORTANT", "FGS declaration and demo video"),
    "FOREGROUND_SERVICE_CAMERA": ("IMPORTANT", "FGS declaration and demo video"),
    "FOREGROUND_SERVICE_MICROPHONE": ("IMPORTANT", "FGS declaration and demo video"),
    "FOREGROUND_SERVICE_DATA_SYNC": ("IMPORTANT", "FGS declaration. WorkManager is often enough"),
    "FOREGROUND_SERVICE_SPECIAL_USE": ("IMPORTANT", "FGS specialUse needs the subtype property and a declaration"),
    "FOREGROUND_SERVICE_HEALTH": ("IMPORTANT", "FGS declaration"),
    "FOREGROUND_SERVICE_CONNECTED_DEVICE": ("IMPORTANT", "FGS declaration"),
    "FOREGROUND_SERVICE_PHONE_CALL": ("IMPORTANT", "FGS declaration"),
    "FOREGROUND_SERVICE_REMOTE_MESSAGING": ("IMPORTANT", "FGS declaration"),
    "FOREGROUND_SERVICE_MEDIA_PLAYBACK": ("SUGGESTION", "FGS mediaPlayback: must play media the user started"),
    "BODY_SENSORS": ("IMPORTANT", "Health apps policy and Health Connect declaration"),
    "ACTIVITY_RECOGNITION": ("SUGGESTION", "Declare fitness data in Data safety"),
    "RECORD_AUDIO": ("SUGGESTION", "Declare audio in Data safety, prominent disclosure if not obvious"),
}

# ----------------------------------------------------------------- helpers --

def rel(p, root):
    try:
        return str(Path(p).relative_to(root))
    except ValueError:
        return str(p)


def read(p):
    try:
        if os.path.getsize(p) > MAX_FILE:
            return ""
        return Path(p).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def is_generated(name):
    return name.endswith(GENERATED) or re.match(r"app_localizations(_\w+)?\.dart$", name) or name == "strings.g.dart"


def walk(root, exts):
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in fns:
            if Path(fn).suffix in exts and not is_generated(fn):
                yield os.path.join(dp, fn)


def wanted_json(p):
    """Only translation dictionaries among .json files."""
    return bool(re.search(r"/(l10n|i18n|locales?|translations|lang)/", p))


class Corpus:
    """Source and UI-text files of one app, loaded once for grep."""

    def ordered(self):
        """Code before translations, the English/template locale before others."""
        def rank(item):
            p = item[0]
            l10n = Path(p).suffix not in CODE_EXT or bool(re.search(r"/(l10n|i18n|locales?|translations)/", p))
            return (l10n, not re.search(r"(_en|/en)\b|intl_en|app_en", p), p)
        if not hasattr(self, "_ordered"):
            self._ordered = sorted(self.files.items(), key=rank)
        return self._ordered

    def __init__(self, root):
        self.root = root
        self.files = {}
        for p in walk(root, TEXT_EXT):
            if "/functions/lib/" in p or (p.endswith(".json") and not wanted_json(p)):
                continue
            self.files[p] = read(p)

    def grep(self, pattern, exts=None, flags=re.I, limit=MAX_EVIDENCE):
        rx = re.compile(pattern, flags)
        hits = []
        for p, text in self.ordered():
            if exts and Path(p).suffix not in exts:
                continue
            if not rx.search(text):
                continue
            code = Path(p).suffix in CODE_EXT
            for i, line in enumerate(text.splitlines(), 1):
                if code and COMMENT.match(line):
                    continue
                if rx.search(line):
                    hits.append(f"{rel(p, self.root)}:{i}: {line.strip()[:160]}")
                    if len(hits) >= limit:
                        return hits
        return hits


def parse_pubspec_deps(text):
    deps, section = {}, None
    for line in text.splitlines():
        if re.match(r"^(dependencies|dev_dependencies|dependency_overrides):\s*$", line):
            section = line.split(":")[0]
            continue
        if re.match(r"^\S", line):
            section = None
            continue
        m = re.match(r"^  ([A-Za-z0-9_]+):", line)
        if section and m and section != "dev_dependencies":
            deps[m.group(1)] = section
    return deps


def parse_pubspec_lock(text):
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^  ([A-Za-z0-9_]+):\s*$", line)
        if m:
            cur = m.group(1)
            continue
        m = re.match(r'^    version: "([^"]+)"', line)
        if cur and m:
            out[cur] = m.group(1)
    return out


def ver_tuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v.split("+")[0])[:3]) or (0,)


def plist_keys(text):
    out = {}
    for m in re.finditer(r"<key>([^<]+)</key>\s*(<string>([^<]*)</string>|<string/>|<true/>|<false/>|<array>|<dict>)", text):
        k, raw, s = m.group(1), m.group(2), m.group(3)
        out[k] = s if s is not None else ("" if raw == "<string/>" else raw in ("<true/>", "<array>", "<dict>"))
    return out


def plist_array(text, key):
    m = re.search(rf"<key>{re.escape(key)}</key>\s*<array>(.*?)</array>", text, re.S)
    return re.findall(r"<string>([^<]+)</string>", m.group(1)) if m else []


def flutter_defaults(app_dir):
    """Resolve flutter.targetSdkVersion and friends from the pinned or global SDK."""
    roots = []
    for base in (app_dir, app_dir.parent):
        fvmrc = base / ".fvmrc"
        if fvmrc.exists():
            try:
                v = json.loads(read(fvmrc)).get("flutter")
                if v:
                    roots.append(Path.home() / "fvm" / "versions" / v)
            except ValueError:
                pass
        link = base / ".fvm" / "flutter_sdk"
        if link.exists():
            roots.append(link.resolve())
    fl = shutil.which("flutter")
    if fl:
        roots.append(Path(os.path.realpath(fl)).parent.parent)
    for r in roots:
        text = read(r / "packages/flutter_tools/gradle/src/main/kotlin/FlutterExtension.kt")
        if text:
            vals = {k: int(v) for k, v in re.findall(r"val (\w+SdkVersion): Int = (\d+)", text)}
            return {"sdk": str(r), "version": read(r / "version").strip() or r.name, **vals}
    return None


def billing_from_pub_cache(pkg, version):
    base = Path(os.environ.get("PUB_CACHE", Path.home() / ".pub-cache")) / "hosted" / "pub.dev" / f"{pkg}-{version}" / "android"
    for name in ("build.gradle", "build.gradle.kts"):
        m = re.search(r"com\.android\.billingclient:billing(?:-ktx)?:([\d.]+)", read(base / name))
        if m:
            return m.group(1)
    return None


def find_app_dirs(root):
    """A repo may be a monorepo. Return the dirs that look like mobile apps."""
    root = Path(root).resolve()
    found = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS and not d.startswith(".")]
        p = Path(dp)
        depth = len(p.relative_to(root).parts)
        if depth > 3:
            dns[:] = []
            continue
        has_native = (p / "ios").is_dir() or (p / "android").is_dir()
        is_flutter = "pubspec.yaml" in fns and has_native and re.search(r"^\s+flutter:\s*$", read(p / "pubspec.yaml"), re.M)
        is_rn = "package.json" in fns and re.search(r'"(react-native|expo)"\s*:', read(p / "package.json")) and (has_native or "app.json" in fns)
        is_android = (p / "app" / "src" / "main" / "AndroidManifest.xml").exists()
        if is_flutter or is_rn or is_android:
            found.append(p)
            dns[:] = []
    return found


# ------------------------------------------------------------------- scan ----

class Scan:
    def __init__(self, app_dir):
        self.dir = Path(app_dir).resolve()
        self.facts = {"app_dir": str(self.dir)}
        self.findings = []
        self.deps, self.locked = {}, {}

    def add(self, fid, platform, level, refs, title, evidence=None):
        self.findings.append({"id": fid, "platform": platform, "level": level, "refs": refs,
                              "title": title, "evidence": (evidence or [])[:MAX_EVIDENCE]})

    def has(self, names):
        return sorted(n for n in names if n in self.deps)

    def grep(self, *a, **kw):
        return self.corpus.grep(*a, **kw)

    def load(self):
        d = self.dir
        if (d / "pubspec.yaml").exists():
            text = read(d / "pubspec.yaml")
            self.facts["stack"] = "flutter"
            self.deps = parse_pubspec_deps(text)
            self.locked = parse_pubspec_lock(read(d / "pubspec.lock"))
            m = re.search(r"^name:\s*(\S+)", text, re.M)
            self.facts["name"] = m.group(1) if m else d.name
            m = re.search(r"^version:\s*(\S+)", text, re.M)
            self.facts["version"] = m.group(1) if m else None
        elif (d / "package.json").exists():
            try:
                j = json.loads(read(d / "package.json"))
            except ValueError:
                j = {}
            self.facts["stack"] = "expo" if "expo" in (j.get("dependencies") or {}) else "react-native"
            for k, v in (j.get("dependencies") or {}).items():
                self.deps[k] = "dependencies"
                self.locked[k] = str(v).lstrip("^~")
            self.facts["name"] = j.get("name", d.name)
            self.facts["version"] = j.get("version")
        else:
            self.facts["stack"] = "native"
            self.facts["name"] = d.name
        self.ios = d / "ios"
        self.android = d / "android" if (d / "android").is_dir() else d
        if self.android == d and not (d / "app" / "src" / "main" / "AndroidManifest.xml").exists():
            self.android = d / "android"  # no native Android project (e.g. managed Expo)
        self.facts["platforms"] = [p for p, ok in (("ios", self.ios.is_dir()),
                                                   ("android", (self.android / "app").is_dir())) if ok]
        self.corpus = Corpus(d)
        self.facts["source_files"] = sum(1 for p in self.corpus.files if Path(p).suffix in CODE_EXT)
        cats = {
            "ads": ADS, "tracking": TRACKING, "analytics": ANALYTICS, "att": ATT,
            "third_party_login": THIRD_PARTY_LOGIN, "apple_login": APPLE_LOGIN, "account_backend": ACCOUNT_BACKENDS,
            "iap": IAP, "external_pay": EXTERNAL_PAY, "chat_ugc": CHAT_UGC, "ai": AI, "remote_code": REMOTE_CODE,
            "remote_config": REMOTE_CONFIG, "webview": WEBVIEW, "push": PUSH, "health": HEALTH,
            "recording": RECORDERS, "contacts": CONTACTS, "location": LOCATION,
        }
        self.cat = {k: self.has(v) for k, v in cats.items()}
        # wrapper and mediation packages not in the catalogs
        self.cat["ads"] = sorted(set(self.cat["ads"]) | {n for n in self.deps if AD_NAME.search(n)})
        self.cat["tracking"] = sorted(set(self.cat["tracking"]) | {n for n in self.deps if "install_referrer" in n or "install-referrer" in n})
        self.facts["sdk_categories"] = {k: v for k, v in self.cat.items() if v}

    def expo_checks(self):
        """Managed Expo apps generate ios/ and android/ at build time from app.json."""
        if self.facts["stack"] != "expo" or self.facts["platforms"]:
            return
        cfg_path = self.dir / "app.json"
        try:
            cfg = json.loads(read(cfg_path)).get("expo", {})
        except ValueError:
            cfg = {}
        self.facts["platforms"] = ["ios", "android"]
        self.facts["expo_managed"] = True
        ios_cfg, and_cfg = cfg.get("ios", {}), cfg.get("android", {})
        self.facts["ios_usage_strings"] = {k: v for k, v in (ios_cfg.get("infoPlist") or {}).items() if k.endswith("UsageDescription")}
        self.facts["android_permissions"] = sorted(p.split(".")[-1] for p in and_cfg.get("permissions") or [])
        self.facts["ios_privacy_manifest"] = ["app.json expo.ios.privacyManifests"] if ios_cfg.get("privacyManifests") else []
        for name in self.facts["android_permissions"]:
            if name in ANDROID_RESTRICTED:
                level, note = ANDROID_RESTRICTED[name]
                self.add(f"AND-PERM-{name}", "android", level, ["Play: Permissions and APIs that Access Sensitive Information"],
                         f"{name}: {note}", ["app.json expo.android.permissions"])
        if (self.cat["ads"] or self.cat["tracking"]) and "NSUserTrackingUsageDescription" not in self.facts["ios_usage_strings"]:
            self.add("IOS-ATT", "ios", "CRITICAL", ["Apple 5.1.2(i)"],
                     "Ad or attribution SDK linked but app.json sets no NSUserTrackingUsageDescription", ["app.json expo.ios.infoPlist"])
        self.add("EXPO-MANAGED", "both", "SUGGESTION", ["scan coverage"],
                 "Managed Expo project: native files are generated at build. Run `npx expo prebuild --no-install` in a scratch copy for full iOS and Android checks, and confirm targetSdk 36 via expo-build-properties or the SDK default",
                 [rel(cfg_path, self.dir)])

    # -- iOS ----------------------------------------------------------------

    def ios_checks(self):
        if not self.ios.is_dir():
            return
        plists = sorted(self.ios.glob("*/Info.plist"), key=lambda p: p.parent.name != "Runner")
        plist = plists[0] if plists else None
        ptext = read(plist) if plist else ""
        pr = rel(plist, self.dir) if plist else "ios/Runner/Info.plist"
        keys = plist_keys(ptext)
        bg = plist_array(ptext, "UIBackgroundModes")
        pbx = read(next(iter(self.ios.glob("*.xcodeproj/project.pbxproj")), "")) if list(self.ios.glob("*.xcodeproj")) else ""
        podfile = read(self.ios / "Podfile")
        self.facts["ios_usage_strings"] = {k: v for k, v in keys.items() if k.endswith("UsageDescription")}
        self.facts["ios_background_modes"] = bg
        m = re.search(r"IPHONEOS_DEPLOYMENT_TARGET = ([\d.]+)", pbx)
        self.facts["ios_deployment_target"] = m.group(1) if m else None

        missing, weak = [], []
        for dep, need in PLIST_NEEDS.items():
            if dep not in self.deps:
                continue
            for k in need:
                v = keys.get(k)
                if v is None:
                    missing.append(f"{dep} needs {k}")
                elif isinstance(v, str) and (len(v.strip()) < 25 or re.search(
                        r"\$\(|^\s*(this )?app (needs|requires|wants) (access|permission)[^.]{0,40}\.?\s*$|^\s*(kamera|konum|mikrofon|fotoğraf)[^.]{0,20} (izni|erişimi) gerekli\.?\s*$", v, re.I)):
                    weak.append(f'{pr}: {k} = "{v}"')
        if "location" in bg and "NSLocationAlwaysAndWhenInUseUsageDescription" not in keys:
            missing.append("UIBackgroundModes location needs NSLocationAlwaysAndWhenInUseUsageDescription")
        if missing:
            self.add("IOS-USAGE-STRING-MISSING", "ios", "CRITICAL", ["Apple 5.1.1(ii)", "Apple 2.1"],
                     "A linked permission has no Info.plist purpose string. The app crashes when it asks", missing)
        if weak:
            self.add("IOS-USAGE-STRING-WEAK", "ios", "IMPORTANT", ["Apple 5.1.1(ii)"],
                     "Purpose string is short or generic. Apple wants what the data is used for, with an example", weak)

        if "permission_handler" in self.deps:
            used = sorted(set(re.findall(r"Permission\.(\w+)", " ".join(
                t for p, t in self.corpus.files.items() if p.endswith((".dart",))))))
            absent = sorted({PH_MACROS[u] for u in used if u in PH_MACROS and not re.search(PH_MACROS[u] + r"\w*\s*=\s*1", podfile)})
            if absent:
                self.add("IOS-PERMISSION-HANDLER-MACROS", "ios", "CRITICAL", ["Apple 2.1"],
                         "permission_handler is called for a permission whose Podfile macro is not set. iOS always answers denied, so review sees a broken feature",
                         [f"ios/Podfile: {m}=1 missing" for m in absent])

        manifests = [p for p in self.ios.rglob("PrivacyInfo.xcprivacy") if not {"Pods", ".symlinks", "build"} & set(p.parts)]
        self.facts["ios_privacy_manifest"] = [rel(p, self.dir) for p in manifests]
        if not manifests:
            cross = self.facts["stack"] in ("flutter", "react-native", "expo")
            self.add("IOS-PRIVACY-MANIFEST", "ios", "SUGGESTION" if cross else "CRITICAL", ["Apple 5.1.1", "ITMS-91053"],
                     "No PrivacyInfo.xcprivacy in the app target. Plugins ship their own, but native code in the app that calls required-reason APIs needs one, and it is where collected data types are declared"
                     if cross else "No PrivacyInfo.xcprivacy in the app target. Required-reason APIs (UserDefaults, file timestamps, boot time) get the upload rejected",
                     ["ios/Runner/PrivacyInfo.xcprivacy not found"])
        else:
            mtext = read(manifests[0])
            if pbx and "PrivacyInfo.xcprivacy" not in pbx:
                self.add("IOS-PRIVACY-MANIFEST-NOT-IN-TARGET", "ios", "IMPORTANT", ["ITMS-91053"],
                         "PrivacyInfo.xcprivacy exists but is not in the Xcode project, so it never reaches the bundle",
                         [rel(manifests[0], self.dir)])
            if (self.cat["ads"] or self.cat["tracking"]) and not re.search(r"<key>NSPrivacyTracking</key>\s*<true/>", mtext):
                self.add("IOS-PRIVACY-MANIFEST-TRACKING", "ios", "IMPORTANT", ["Apple 5.1.2", "App Privacy label"],
                         "Ad or attribution SDK linked but the app manifest does not set NSPrivacyTracking true",
                         [rel(manifests[0], self.dir)] + self.cat["ads"] + self.cat["tracking"])

        if self.cat["ads"] or self.cat["tracking"]:
            att_call = self.grep(r"requestTrackingAuthorization|Permission\.appTrackingTransparency|requestTrackingPermission", CODE_EXT)
            has_key = "NSUserTrackingUsageDescription" in keys
            if not att_call or not has_key:
                self.add("IOS-ATT", "ios", "CRITICAL", ["Apple 5.1.2(i)", "Apple 2.5.18"],
                         "Ad or attribution SDK linked but no ATT prompt or no NSUserTrackingUsageDescription",
                         [f"SDKs: {', '.join(self.cat['ads'] + self.cat['tracking'])}",
                          f"ATT call: {'found' if att_call else 'none'}", f"NSUserTrackingUsageDescription: {'set' if has_key else 'missing'}"] + att_call[:2])

        risky_bg = [m for m in bg if m in ("location", "audio", "voip", "bluetooth-central", "external-accessory")]
        if risky_bg:
            self.add("IOS-BACKGROUND-MODES", "ios", "SUGGESTION", ["Apple 2.5.4"],
                     "Background modes must serve their stated purpose. Justify them in the review notes",
                     [f"{pr}: UIBackgroundModes = {', '.join(bg)}"])

        ent = "\n".join(read(p) for p in self.ios.glob("*/*.entitlements"))
        if self.cat["apple_login"] and "com.apple.developer.applesignin" not in ent:
            self.add("IOS-SIWA-ENTITLEMENT", "ios", "CRITICAL", ["Apple 2.1", "Apple 4.8"],
                     "Sign in with Apple package linked but the entitlement is missing. Sign-in fails on the review device",
                     ["ios/Runner/*.entitlements"])

        if "ITSAppUsesNonExemptEncryption" not in keys:
            self.add("IOS-EXPORT-COMPLIANCE", "ios", "SUGGESTION", ["App Store Connect export compliance"],
                     "ITSAppUsesNonExemptEncryption is not set, so every upload waits on the encryption question", [pr])

    # -- Android ------------------------------------------------------------

    def android_checks(self):
        app = self.android / "app"
        if not app.is_dir():
            return
        perms, removed, where, fgs = {}, set(), {}, []
        for mp in sorted((app / "src").glob("*/AndroidManifest.xml")):
            text = read(mp)
            for i, line in enumerate(text.splitlines(), 1):
                m = re.search(r'<uses-permission(?:-sdk-23)?\s+[^>]*android:name="([^"]+)"', line)
                if m:
                    name = m.group(1).split(".")[-1]
                    if 'tools:node="remove"' in line:
                        removed.add(name)
                    else:
                        perms[name] = True
                        where.setdefault(name, f"{rel(mp, self.dir)}:{i}")
            fgs += re.findall(r'foregroundServiceType="([^"]+)"', text)
            if 'android:usesCleartextTraffic="true"' in text:
                self.add("AND-CLEARTEXT", "android", "SUGGESTION", ["Play Data safety: encryption in transit"],
                         "usesCleartextTraffic is true. Contradicts a Data safety claim that data is encrypted in transit",
                         [rel(mp, self.dir)])
        merged = next(iter(sorted(self.dir.glob("build/app/intermediates/merged_manifest*/release/**/AndroidManifest.xml"))), None)
        if merged:
            for name in re.findall(r'<uses-permission[^>]*android:name="[\w.]*?\.?([A-Z_]+)"', read(merged)):
                if name not in perms and name not in removed:
                    perms[name] = True
                    where.setdefault(name, f"{rel(merged, self.dir)} (merged from a plugin)")
        self.facts["android_permissions"] = sorted(perms)
        self.facts["android_permissions_removed"] = sorted(removed)
        self.facts["android_fgs_types"] = fgs
        self.facts["android_merged_manifest"] = rel(merged, self.dir) if merged else None

        for name in sorted(perms):
            if name in ANDROID_RESTRICTED:
                level, note = ANDROID_RESTRICTED[name]
                self.add(f"AND-PERM-{name}", "android", level, ["Play: Permissions and APIs that Access Sensitive Information"],
                         f"{name}: {note}", [where[name]])

        gfile = app / "build.gradle.kts" if (app / "build.gradle.kts").exists() else app / "build.gradle"
        gtext = read(gfile)
        levels = {}
        for key in ("targetSdk", "minSdk", "compileSdk"):
            m = re.search(rf"\b{key}(?:Version)?\s*=?\s*([\w.]+)", gtext)
            levels[key] = m.group(1) if m else None
        fd = flutter_defaults(self.dir) if self.facts["stack"] == "flutter" else None
        if fd:
            self.facts["flutter_sdk"] = fd.get("version")
            for key, val in levels.items():
                if val and val.startswith("flutter."):
                    levels[key] = str(fd.get(val.split(".")[1], val))
        self.facts["android_sdk_levels"] = levels
        t = levels.get("targetSdk")
        if t and t.isdigit() and int(t) < 36:
            self.add("AND-TARGET-SDK", "android", "CRITICAL", ["Play Target API level (2026-08-31)"],
                     f"targetSdk is {t}. New apps and updates need 36 (Android 16) since 2026-08-31", [rel(gfile, self.dir)])
        elif not (t and t.isdigit()):
            self.add("AND-TARGET-SDK-UNKNOWN", "android", "SUGGESTION", ["Play Target API level"],
                     f"targetSdk could not be resolved ({t}). Check by hand that it is 36", [rel(gfile, self.dir)])

        bills = [("app build.gradle", v) for v in re.findall(r"com\.android\.billingclient:billing(?:-ktx)?:([\d.]+)", gtext)]
        for pkg in ("in_app_purchase_android", "flutter_inapp_purchase"):
            if pkg in self.locked:
                b = billing_from_pub_cache(pkg, self.locked[pkg])
                if b:
                    bills.append((f"{pkg} {self.locked[pkg]}", b))
        rc = self.locked.get("purchases_flutter") or self.locked.get("react-native-purchases")
        if rc:
            # RevenueCat moved to purchases-android 9 (Play Billing 8) in its 9.0 Flutter and RN releases
            bills.append((f"RevenueCat {rc}", "8+" if ver_tuple(rc) >= (9,) else "7 or lower"))
        self.facts["play_billing"] = [f"{a}: PBL {b}" for a, b in bills]
        for src, b in bills:
            m = re.match(r"\d+", b)
            if b != "8+" and (int(m.group(0)) if m else 0) < 8:
                self.add("AND-BILLING-VERSION", "android", "CRITICAL", ["Play Billing Library deprecation (2026-08-31)"],
                         "Play Billing Library below 8. Updates are blocked since 2026-08-31 (extension at most to 2026-11-01)",
                         [f"{src}: PBL {b}"])

        if any("location" in s for s in fgs):
            self.add("AND-FGS-LOCATION", "android", "IMPORTANT", ["Play Foreground service policy (2027-01-27)"],
                     "Location-type foreground service. Geofencing stops being an approved use, move it to the Geofence API",
                     [f"foregroundServiceType: {', '.join(fgs)}"])

    # -- both stores --------------------------------------------------------

    def cross_checks(self):
        g = self.grep
        ios = "ios" in self.facts["platforms"]

        apple_code = g(r"AppleAuthProvider|signInWithApple|OAuthProvider\(\s*['\"]apple\.com|getAppleIDCredential|appleAuth\.", CODE_EXT, limit=2)
        if self.cat["third_party_login"] and ios and not self.cat["apple_login"] and not apple_code:
            self.add("X-SIGN-IN-WITH-APPLE", "ios", "CRITICAL", ["Apple 4.8"],
                     "Third-party login without an equivalent privacy-focused option such as Sign in with Apple",
                     [f"SDKs: {', '.join(self.cat['third_party_login'])}"])

        signup = g(r"createUserWithEmailAndPassword|\bsignUp\(|auth\.signUp|(?<!notifications)(?<!device)(?<!push)(?<!token)/(register|signup)([\x27\x22/?]|$)|kayıt ol|hesap oluştur|create (an )?account|sign up", UI_EXT, limit=3)
        has_account = bool(signup or self.cat["third_party_login"] or self.cat["apple_login"] or apple_code)
        self.facts["account_creation_evidence"] = signup
        if has_account or self.cat["account_backend"]:
            delete = g(r"delete.?account|deleteAccount|hesab(ı|im|ımı)\s*sil|hesap\s*silme|deleteUser|user\.delete\(|currentUser!?\??\.delete\(|/account/delete|accountDeletion|delete_user|hesabımı kapat", UI_EXT)
            if not delete:
                self.add("X-ACCOUNT-DELETION", "both", "CRITICAL" if has_account else "IMPORTANT",
                         ["Apple 5.1.1(v)", "Play User Data: account deletion"],
                         "Accounts can be created but no in-app account deletion was found. Play also wants a web deletion link"
                         if has_account else "Auth backend linked, no sign-up or deletion found. Confirm users cannot create accounts",
                         signup[:2] or [f"Auth: {', '.join(self.cat['account_backend'])}"])
            else:
                self.facts["account_deletion_evidence"] = delete[:3]
                if (self.cat["apple_login"] or apple_code) and not g(r"revoke\w*(apple|token)|auth/revoke|authorizationCode", CODE_EXT):
                    self.add("X-SIWA-REVOKE", "ios", "IMPORTANT", ["Apple 5.1.1(v)", "Sign in with Apple REST API"],
                             "Account deletion does not seem to revoke the Sign in with Apple token", delete[:2])

        if not g(r"https?://[^\s\x27\x22]*(privacy|gizlilik|kvkk|aydinlatma|datenschutz|privacidad)|[\x27\x22/](privacy|gizlilik|kvkk)[-\w]*/?[\x27\x22]|privacyPolicy(Url|Uri|Link|Page|Screen|Route)|PrivacyPolicy(Page|Screen|View)|privacy_policy_url", UI_EXT, limit=1):
            self.add("X-PRIVACY-POLICY-LINK", "both", "IMPORTANT", ["Apple 5.1.1(i)", "Play User Data: privacy policy"],
                     "No privacy policy link found inside the app", [])

        if self.cat["iap"]:
            if not g(r"restorePurchases|restoreTransactions|restore ?purchases|geri yükle|wiederherstellen|restaurar", UI_EXT, limit=2):
                self.add("X-IAP-RESTORE", "ios", "IMPORTANT", ["Apple 3.1.1"],
                         "In-app purchases without a Restore Purchases action", [f"SDKs: {', '.join(self.cat['iap'])}"])
            paywalls = [p for p in self.corpus.files if Path(p).suffix in CODE_EXT and re.search(r"paywall|subscription|abonelik|premium|upgrade", Path(p).name, re.I)]
            lacking = [rel(p, self.dir) for p in paywalls if not re.search(r"terms|eula|koşul|kosul|privacy|gizlilik|legal", self.corpus.files[p], re.I)]
            if paywalls and len(lacking) == len(paywalls):
                self.add("X-PAYWALL-TERMS", "both", "IMPORTANT", ["Apple 3.1.2(c)", "Play Subscriptions policy"],
                         "Paywall shows no Terms of Use or Privacy link. Price, period, renewal and cancellation must be clear", lacking)

        links = g(r"(buy|purchase|satın ?al|abone ol|subscribe)[^\n]{0,80}(https?://|launchUrl|openUrl|Linking\.openURL)|https?://[^\s'\"]*/(checkout|pricing|odeme|ödeme|satin-al)\b", CODE_EXT)
        if self.cat["external_pay"] or links:
            self.add("X-EXTERNAL-PAYMENT", "both", "IMPORTANT", ["Apple 3.1.1", "Apple 3.1.3", "Play Payments policy"],
                     "External payment or purchase link. Digital goods must use IAP or Play Billing unless a regional entitlement applies",
                     ([f"SDKs: {', '.join(self.cat['external_pay'])}"] if self.cat["external_pay"] else []) + links)

        ugc = g(r"collection(Group)?\(\s*[\w.$\x27\x22]*(message|chat|comment|post|conversation|room|feed|review|story)s?\w*[\x27\x22]?\s*\)|\b(publish|create|submit|share)(Post|Comment|Story|Review)\w*\(|postComment|anonymous chat|random chat", CODE_EXT)
        if self.cat["chat_ugc"] or ugc:
            self.facts["ugc"] = True
            report = g(r"\breport(Content|User|Post|Message|Comment|Abuse)\w*|\w+Report(s)?\(|[a-z]+Reports?\b(?<!crashReports)(?<!errorReports)|şikayet|şikâyet|\bflag(Content|Post)\b|kötüye kullanım|report (this|post|user|message)", CODE_EXT | {".arb"}, limit=2)
            block = g(r"\bblock\w*(User|Publisher|Author|Account|Profile)\w*|\w*(User|Publisher|Author)Blocked\w*|setBlocked|blockedUsers|engelle|block (this )?user", CODE_EXT | {".arb"}, limit=2)
            ev = ([f"SDKs: {', '.join(self.cat['chat_ugc'])}"] if self.cat["chat_ugc"] else []) + ugc[:3]
            if not report or not block:
                self.add("X-UGC-MODERATION", "both", "CRITICAL", ["Apple 1.2", "Play User Generated Content", "Play Child Safety Standards"],
                         f"User content or chat. Report: {'found' if report else 'MISSING'}, block: {'found' if block else 'MISSING'}. A filter and published contact info are also required",
                         ev)
            else:
                self.add("X-UGC-PRESENT", "both", "SUGGESTION", ["Apple 1.2", "Play Child Safety Standards", "App Store age rating: social media"],
                         "User content with report and block found. Check the filter, timely action, the CSAE standards page and the social-media age-rating answers",
                         ev + report[:1] + block[:1])
            anon = g(r"anonymous chat|anonim (sohbet|mesaj)|random chat|rastgele (biriyle|kişiyle|sohbet)|chatroulette|talk to strangers", UI_EXT)
            if anon:
                self.add("X-ANON-CHAT", "both", "CRITICAL", ["Apple 1.2 (2026-02-06)", "Play Families + Child Endangerment (2026-08-26)"],
                         "Anonymous or random chat. Apple may remove it without notice, Play forbids targeting children and applies Child Safety Standards",
                         anon)

        ai_calls = g(r"api\.openai\.com|generativelanguage\.googleapis\.com|aiplatform\.googleapis\.com|api\.anthropic\.com|openrouter\.ai|api\.groq\.com|api\.deepseek\.com|api\.mistral\.ai|api\.replicate\.com|fal\.run|api\.stability\.ai|api\.elevenlabs\.io|api\.suno|api\.udio|speech\.googleapis\.com|texttospeech\.googleapis\.com|vision\.googleapis\.com|api\.assemblyai\.com|api\.deepgram\.com|api\.cohere\.|api-inference\.huggingface\.co|router\.huggingface\.co|api\.together\.xyz|api\.fireworks\.ai|api\.x\.ai|api\.perplexity\.ai|api\.audd\.io|acrcloud\.com|FirebaseAI\.|GenerativeModel\(|ChatOpenAI\(|new OpenAI\(", CODE_EXT)
        if self.cat["ai"] or ai_calls:
            consent = g(r"(yapay zek|\bAI\b|third.?party AI|üçüncü taraf)[^\n]{0,80}(onay|consent|izin|agree|kabul)|aiConsent|ai_consent|ConsentService", UI_EXT, limit=2)
            ev = ([f"SDKs: {', '.join(self.cat['ai'])}"] if self.cat["ai"] else []) + ai_calls[:3]
            self.add("X-AI-DATA-SHARING", "both", "SUGGESTION" if consent else "CRITICAL",
                     ["Apple 5.1.2(i)", "Play User Data: third-party AI (2026-07-15)"],
                     "Personal data may reach a third-party AI. Apple and Play want a clear disclosure and explicit permission before sending"
                     + (". A consent trace exists, confirm it covers the AI calls" if consent else ""), ev + consent)
            gen = g(r"\bimage.?generation|generateImage|görsel üretici|yapay zek[aâ][^\n]{0,40}görsel|text.?to.?image|\bimg2img\b|\binpaint|face.?swap|yüz değiştir|stable.?diffusion|\bdall-?e\b|gpt-image|\bimagen-?\d|\bflux[-_.](1|dev|schnell|pro|kontext)|\bundress|nudif|deepfake|virtual try.?on", CODE_EXT | {".arb"})
            if gen:
                self.add("X-AI-IMAGERY", "both", "CRITICAL", ["Apple 1.2 (2026-10-16)", "Play AI-Generated Content"],
                         "AI image generation or editing. Must proactively prevent and remove nonconsensual intimate imagery and offer in-app reporting",
                         gen)

        review = g(r"\b(isReviewMode|reviewMode|review_mode|isAppleReview|appleReviewer|hideForReview|hideDuringReview|isInReview|inStoreReview|reviewerMode|isReviewer|isReviewBuild|is_review_mode|isUnderAppReview|storeReviewMode)\b", CODE_EXT | {".json"})
        if review:
            self.add("X-REVIEW-MODE-SWITCH", "both", "CRITICAL", ["Apple 2.5.19 (2026-10-16)", "Play Deceptive Behavior"],
                     "A switch that changes behaviour while the app is in review. Counts as bait-and-switch: removal from the store and the developer program",
                     review)
        hidden = g(r"secret ?menu|gizli ?menü|easter.?egg|\bgodMode\b|\bdevMenu\b|\bdebugMenu\b|\bhiddenFeature|\bunlockAll\b|_secretTap|_hiddenTap", CODE_EXT)
        if hidden:
            self.add("X-HIDDEN-FEATURE", "both", "IMPORTANT", ["Apple 2.5.19", "Apple 2.3.1"],
                     "Hidden menu or feature. Fine behind kDebugMode or __DEV__, otherwise document it in the review notes or remove it",
                     hidden)
        if self.cat["remote_config"]:
            gates = g(r"([Rr]emote[Cc]onfig[\w.()]*|\b_?rc|\bflags?)\.(getBool|getBoolean|isFeatureEnabled|getValue)\(\s*['\"][^'\"]*(enable|show|feature|_on\b|visible|unlock|beta|new_)[^'\"]*['\"]", CODE_EXT)
            gates += g(r"([Rr]emote[Cc]onfig[\w.()]*|\b_?rc|\bflags?)\.(getBool|getBoolean)\(\s*k?[A-Za-z_]*(Enable|enable|Show|show|Feature|feature|Visible|visible|Unlock|unlock)\w*\s*\)", CODE_EXT)
            gates = self.remote_defaults_off() + gates
            if gates:
                self.add("X-REMOTE-FEATURE-GATES", "both", "IMPORTANT", ["Apple 2.5.19", "Apple 2.5.2"],
                         "Features switched on by remote config. Anything off in review and on later is a 2.5.19 violation, so ship them on in the reviewed build",
                         gates)
        if self.cat["remote_code"] or (self.dir / "shorebird.yaml").exists():
            self.add("X-CODE-PUSH", "both", "IMPORTANT", ["Apple 2.5.2", "Apple 3.3.1(b)", "Play Device and Network Abuse"],
                     "Over-the-air code or UI updates. Bug fixes are fine, new features or a changed purpose are not",
                     self.cat["remote_code"] + (["shorebird.yaml"] if (self.dir / "shorebird.yaml").exists() else []))

        if self.cat["webview"]:
            wv = g(r"\bWebView\(|InAppWebView\(|WebViewWidget\(|loadRequest\(|initialUrlRequest|<WebView\b", CODE_EXT)
            if self.facts["source_files"] < 25 and wv:
                self.add("X-WEBVIEW-WRAPPER", "both", "CRITICAL", ["Apple 4.2", "Apple 4.2.2", "Play Webviews and Affiliate Spam"],
                         f"Few source files ({self.facts['source_files']}) and a WebView looks like the main content. Repackaged websites are rejected",
                         wv)

        ph = [h for h in g(r"lorem ipsum|coming soon|çok yakında|yakında gelecek|under construction|yapım aşamasında|placeholder text", UI_EXT, limit=20)
              if self.l10n_key_used(h)][:MAX_EVIDENCE]
        if ph:
            self.add("X-PLACEHOLDER", "both", "IMPORTANT", ["Apple 2.1(a)", "Play Minimum functionality"],
                     "Placeholder or unfinished text. If reachable in release it reads as an incomplete app", ph)

        if self.cat["push"]:
            mk = g(r"(kampanya|campaign|promo|marketing|pazarlama|indirim|discount)[^\n]{0,60}(notification|bildirim|push)", UI_EXT, limit=3)
            if mk:
                self.add("X-MARKETING-PUSH", "both", "SUGGESTION", ["Apple 4.5.4", "Apple 4.5.3"],
                         "Marketing notifications need a separate explicit opt-in and an in-app opt-out", mk)

        blob = f"{self.facts.get('name')} {self.dir.name}"
        if re.search(r"kid|child|çocuk|cocuk|bebek|baby|preschool|okuloncesi|masal|toddler", blob, re.I):
            ev = [f"Name: {blob}"] + ([f"SDKs: {', '.join(self.cat['ads'] + self.cat['tracking'] + self.cat['analytics'])}"]
                                      if self.cat["ads"] or self.cat["tracking"] or self.cat["analytics"] else [])
            self.add("X-KIDS-AUDIENCE", "both", "IMPORTANT", ["Apple 1.3", "Apple 5.1.4", "Play Families policy"],
                     "Looks child-directed. Kids Category forbids third-party ads and analytics, Play allows only Families-certified ad SDKs, parental gates on links and purchases",
                     ev)

        if self.cat["health"]:
            self.add("X-HEALTH-DATA", "both", "IMPORTANT", ["Apple 5.1.3", "Play Health apps / Health Connect"],
                     "Health data: no iCloud storage, no ad use, Health Connect declaration and a medical disclaimer",
                     self.cat["health"])
        if self.cat["recording"]:
            self.add("X-RECORDING", "both", "SUGGESTION", ["Apple 2.5.14"],
                     "Audio or screen recording needs explicit consent and a visible or audible indicator while recording",
                     g(r"AudioRecorder\(|FlutterSoundRecorder|RecorderController\(|startRecorder\(|\.start\(\s*(const )?RecordConfig|startRecording\(", CODE_EXT) or self.cat["recording"])
        sensing = []
        for p, t in self.corpus.files.items():
            if Path(p).suffix in CODE_EXT and re.search(r"Timer\.periodic|Stream\.periodic|setInterval\(|scheduleAtFixedRate|PeriodicWorkRequest", t) \
                    and re.search(r"AudioRecorder|startRecorder|\.startStream\(|record\.start|RecorderController|CameraController|getPositionStream|startLocationUpdates|AVAudioRecorder|SpeechRecognizer", t):
                sensing.append(rel(p, self.dir))
        if sensing:
            self.add("X-PERIODIC-SENSING", "both", "IMPORTANT", ["Apple 2.5.14", "Apple 5.1.1(ii)", "Play User Data: prominent disclosure"],
                     "A timer and the microphone, camera or location share a file. Sampling a sensor on a schedule without a visible indicator and disclosure is a removal-level privacy issue",
                     sensing[:MAX_EVIDENCE])

        if self.cat["ads"]:
            self.add("X-ADS-PRESENT", "both", "SUGGESTION", ["Apple 2.5.18", "Play Ads policy", "Play Families Ads"],
                     "Ads linked. Keep them in the main binary, never hide the close button, let users report ads, declare ad data in both privacy forms",
                     self.cat["ads"])

    def l10n_key_used(self, hit):
        """For a hit inside a translation file, keep it only if its key is referenced in code."""
        path = hit.split(":", 1)[0]
        if Path(path).suffix in CODE_EXT and not re.search(r"/(l10n|i18n|locales?|translations)/", path):
            return True
        m = re.search(r":\d+:\s*[\x27\x22]?(\w+)[\x27\x22]?\s*[:=]", hit)
        if not m:
            return True
        key = m.group(1)
        rx = re.compile(r"[.\x27\x22]" + re.escape(key) + r"\b")
        return any(rx.search(t) for p, t in self.corpus.files.items()
                   if Path(p).suffix in CODE_EXT and not re.search(r"/(l10n|i18n|locales?|translations)/", p))

    def remote_defaults_off(self):
        """Boolean flags that default to false in a Remote Config template or defaults file."""
        hits = []
        for p in list(self.dir.glob("remoteconfig*.json")) + list(self.dir.glob("**/remote_config_defaults.*"))[:5]:
            text = read(p)
            try:
                params = json.loads(text).get("parameters", {}) if p.suffix == ".json" else {}
            except ValueError:
                params = {}
            for key, spec in params.items():
                dv = str((spec.get("defaultValue") or {}).get("value", "")).lower()
                if dv == "false" and re.search(r"enable|show|feature|visible|unlock|_on$|beta|launch", key, re.I):
                    line = next((i for i, l in enumerate(text.splitlines(), 1) if f'"{key}"' in l), 0)
                    desc = (spec.get("description") or "")[:80]
                    hits.append(f"{rel(p, self.dir)}:{line}: {key} = false {('(' + desc + ')') if desc else ''}".strip())
        return hits[:4]

    def run(self):
        self.load()
        self.expo_checks()
        self.ios_checks()
        self.android_checks()
        self.cross_checks()
        order = {lvl: i for i, lvl in enumerate(LEVELS)}
        self.findings.sort(key=lambda f: (order.get(f["level"], 9), f["id"]))
        return {"facts": self.facts, "findings": self.findings}


def discover(dirs):
    out = []
    for d in dirs:
        base = Path(os.path.expanduser(d))
        if base.is_dir():
            for child in sorted(base.iterdir()):
                if child.is_dir() and not child.name.startswith(".") and not (child / ".git").is_file():
                    out += [str(a) for a in find_app_dirs(child)]
    return out


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--find":
        dirs = argv[1:] or ["~/IdeaProjects", "~/AndroidStudioProjects", "~/StudioProjects",
                            "~/ReactNativeProjects", "~/Projects", "~/Developer", "~/src", "~/code"]
        print(json.dumps(discover(dirs), indent=2, ensure_ascii=False))
        return 0
    target = Path(os.path.expanduser(argv[0])).resolve()
    out_path = argv[argv.index("--json") + 1] if "--json" in argv else None
    apps = find_app_dirs(target)
    if not apps:
        print(json.dumps({"error": f"no mobile app found under {target}"}))
        return 1
    result = {"repo": str(target), "git_head": None, "scanned_with": "store-compliance scan.py", "apps": []}
    try:
        result["git_head"] = subprocess.run(["git", "-C", str(target), "log", "-1", "--format=%h %cs %s"],
                                            capture_output=True, text=True, timeout=10).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        pass
    result["apps"] = [Scan(a).run() for a in apps]
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if out_path:
        Path(out_path).write_text(text, encoding="utf-8")
        summary = [{"app": a["facts"]["app_dir"], **{lvl: sum(f["level"] == lvl for f in a["findings"]) for lvl in LEVELS}}
                   for a in result["apps"]]
        print(json.dumps({"written": out_path, "summary": summary}, indent=2))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
