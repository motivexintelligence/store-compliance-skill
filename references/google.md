# Google Play Developer Policies: what to check in code

Rules as of **2026-10-18**. Sources: Play Console Help policy announcements
(15 July 2026, 15 April 2026), the Policy deadlines table
(support.google.com/googleplay/android-developer/table/12921780), the Play
Policy Center.

## Deadlines

| Date | Policy | Status on 2026-10-18 |
|---|---|---|
| 2026-08-26 | Anonymous and random chat apps: Families policy forbids targeting children. Child Endangerment (Child Safety Standards) and Age-Restricted Content policies apply to them | **In force** |
| 2026-08-31 | **Target API level 36** (Android 16) for new apps and updates | **In force.** Extension to 2026-11-01 only if requested in Play Console |
| 2026-08-31 | **Play Billing Library 8+** for new apps and updates | **In force.** Extension to 2026-11-01 only if requested |
| 2026-09-30 | Register every Play app in Play Console for Android developer verification, or face global removal | **In force.** Console task |
| 2026-07-15 (+30 days) | User Data policy covers **third-party AI** integrations: limited use, disclosure, consent. Unrated apps not allowed. New Data safety guidance for precise and approximate location | **In force** |
| 2027-01-27 | **Contacts**: apps that do not need broad access must use the Android Contact Picker | Upcoming |
| 2027-01-27 | **Location**: the location button is the recommended minimum scope for precise location | Upcoming |
| 2027-01-27 | **READ_CALL_LOG** no longer allowed for phone-call account verification. Use the Digital Credentials API or the SMS Retriever API | Upcoming |
| 2027-01-27 | **Foreground services**: geofencing removed as an approved use case. Use the Geofence API | Upcoming |

Still in force from earlier rounds and frequently hit: account deletion (in-app
and web link), Data safety accuracy, Photo and Video Permissions (Photo
Picker), exact alarm, foreground service types, 16 KB page size for apps
targeting Android 15+, AI-Generated Content (in-app reporting), Child Safety
Standards (published CSAE standards for social apps), Families ads.

---

## Findings by scanner ID

### AND-TARGET-SDK, AND-TARGET-SDK-UNKNOWN: Target API level
- **Rule.** New apps and updates must target API 36. Existing apps below the bar get hidden from new users on newer devices.
- **Verify.** `facts.android_sdk_levels.targetSdk`. For Flutter `flutter.targetSdkVersion` is resolved from the pinned SDK (`.fvmrc`) or the global one.
- **Fix.** `targetSdk = 36`, then test edge-to-edge, predictive back and the behaviour changes for Android 15 and 16.

### AND-BILLING-VERSION: Play Billing Library deprecation
- **Rule.** PBL 8+ since 2026-08-31. Older versions block every update (security fixes included). Already published binaries keep billing.
- **Verify.** `facts.play_billing`. RevenueCat Flutter/RN 9.0+ ships PBL 8. `in_app_purchase_android` is read from its Gradle file in the pub cache.
- **Fix.** Upgrade the plugin (`purchases_flutter` ≥ 9, `in_app_purchase` latest), migrate removed APIs (`querySkuDetailsAsync`, the no-arg `enablePendingPurchases()`).

### AND-PERM-*: Permissions and APIs that Access Sensitive Information
Check each against the app's **core** purpose. Ads, analytics or "nice to have" never justify a restricted permission.

| Permission | Rule | Fix |
|---|---|---|
| `READ_SMS`, `RECEIVE_SMS`, `SEND_SMS`, `READ_CALL_LOG`, `WRITE_CALL_LOG`, `PROCESS_OUTGOING_CALLS` | Only default SMS/dialer handlers or approved exceptions with a Permissions Declaration. Call-log verification ends 2027-01-27 | SMS Retriever API, SMS User Consent API, Digital Credentials API. Remove with `tools:node="remove"` if a plugin adds it |
| `MANAGE_EXTERNAL_STORAGE` | All files access only for file managers, backup, antivirus, document managers | SAF (`ACTION_OPEN_DOCUMENT`), MediaStore, app-specific dirs |
| `READ_MEDIA_IMAGES`, `READ_MEDIA_VIDEO` | Only for apps whose core use is broad media access (gallery, editor managing the library). One-off picks must use the Photo Picker. Needs a declaration | `image_picker` ≥ 1.0 on Android uses the Photo Picker, so drop the permission |
| `ACCESS_BACKGROUND_LOCATION` | Declaration, demo video, prominent disclosure that says "location" and "when the app is closed or not in use" | Foreground-only, or a WorkManager/Geofence API design |
| `ACCESS_FINE_LOCATION` | Minimum scope. Location button recommended for precise location (2027-01-27) | `ACCESS_COARSE_LOCATION` if city level is enough |
| `READ_CONTACTS`, `WRITE_CONTACTS` | Contact Picker for apps without a core need (2027-01-27) | Android Contact Picker intent |
| `QUERY_ALL_PACKAGES` | Only with core need and a declaration | `<queries>` with specific packages or intents |
| `REQUEST_INSTALL_PACKAGES` | Only if installing packages is the core function | Remove (often added by an OTA or file plugin) |
| `USE_EXACT_ALARM` | Only alarm clocks and calendars | `SCHEDULE_EXACT_ALARM` with the runtime grant, or inexact alarms |
| `SCHEDULE_EXACT_ALARM` | User-granted, denied by default on Android 14+. Must degrade gracefully | Check `canScheduleExactAlarms()`, fall back to inexact |
| `USE_FULL_SCREEN_INTENT` | Calls and alarms only, otherwise a declaration and a user grant | Normal high-priority notification |
| `BIND_ACCESSIBILITY_SERVICE` | Accessibility API declaration, prominent disclosure, no data collection beyond the stated use | |
| `FOREGROUND_SERVICE_*` | Declare each type in Play Console with a video. `dataSync` often belongs in WorkManager. Location FGS for geofencing ends 2027-01-27 | Geofence API, WorkManager, Media3 for playback |
| `AD_ID` | Declare in Data safety. Must be removed when the target audience is children only | `tools:node="remove"` |
| `RECORD_AUDIO`, `CAMERA`, `ACTIVITY_RECOGNITION` | Not restricted, but must be in Data safety, and a prominent disclosure is needed when use is not obvious | |

Plugins add permissions through manifest merging. If `facts.android_merged_manifest` is null, say so and ask for a release build's merged manifest (`build/app/intermediates/merged_manifest/release/`) or read the plugins' manifests.

### AND-FGS-LOCATION: Foreground service policy
See the table. Plan the Geofence API migration before 2027-01-27.

### AND-CLEARTEXT: Data safety
Data safety's "data is encrypted in transit" answer is false with cleartext traffic. Use a network security config that allows only the hosts that need it.

### X-ACCOUNT-DELETION: User Data policy, account deletion
- **Rule.** Apps that let users create accounts must offer deletion **inside the app** and through a **web link** declared in the Data safety form, which works without reinstalling. The data must be deleted (or the retention explained).
- **Fix.** In-app flow plus a public page (`https://<domain>/delete-account`) that takes a request without the app.

### X-AI-DATA-SHARING: User Data policy (2026-07-15 clarification)
- **Rule.** The developer is responsible for data sent to third-party AI: limited use, prominent disclosure, consent, Data safety declaration (shared with third parties).
- **Fix.** Same consent sheet as for Apple 5.1.2(i). Declare "User content → shared" in Data safety. Check the provider's data-use terms (no training on user data).

### X-AI-IMAGERY: AI-Generated Content policy, Inappropriate Content
- **Rule.** Generative AI apps must prevent restricted content (sexual content, NCII, CSAM, deceptive deepfakes of real people) and give users an in-app way to report or flag offensive output, and use those reports to improve filtering.
- **Fix.** Prompt and output filtering, an in-app report button on each output, a review process. Check the app does not market "undress" or "face swap anyone".

### X-UGC-MODERATION, X-UGC-PRESENT, X-ANON-CHAT: User Generated Content, Child Safety Standards, Families
- **Rule.** UGC apps need terms that forbid objectionable content, in-app reporting of content and users, blocking, and real moderation. Social and dating apps must publish **Child Safety Standards** (CSAE) and a contact in Play Console, offer in-app feedback, and act on CSAM. Since 2026-08-26 anonymous and random chat apps fall under Child Endangerment and Age-Restricted Content rules and may not target children.
- **Fix.** Report and block on every UGC surface, a moderation queue, a public CSAE standards page linked in Play Console, and the target audience set to 18+ (or 13+ with age-appropriate controls) for anonymous chat.

### X-IAP-RESTORE, X-PAYWALL-TERMS, X-EXTERNAL-PAYMENT: Payments, Subscriptions
- **Rule.** Digital goods through Play Billing (user-choice and alternative billing only in eligible programmes and regions, plus the new US programmes since 2026). Subscription offers must state price, period, renewal and how to cancel. No misleading free-trial UI.
- **Fix.** Show the base plan price and period from `ProductDetails`, trial length and what happens after it, a Manage subscription link (`https://play.google.com/store/account/subscriptions`).

### X-REVIEW-MODE-SWITCH, X-HIDDEN-FEATURE, X-REMOTE-FEATURE-GATES, X-CODE-PUSH: Deceptive Behavior, Device and Network Abuse
- **Rule.** Apps may not behave differently during review, hide functionality or download executable code from outside Google Play that changes the app (interpreted code in a sandbox, e.g. JS in a WebView, is allowed).
- **Fix.** As for Apple 2.5.19. OTA patches only for fixes.

### X-WEBVIEW-WRAPPER, X-PLACEHOLDER: Minimum functionality, Webviews and Affiliate Spam
- **Rule.** Apps must offer a stable, responsive, engaging experience. Apps whose main purpose is to show a website you do not own are spam.

### X-KIDS-AUDIENCE: Families policy
- **Rule.** If children are in the target audience: only Families Self-Certified ad SDKs, no AD_ID or device identifiers from children, no precise location, teacher-approved/parental-gated purchases and links, content and ads suitable for children. The target audience and content declaration must match the app.

### X-HEALTH-DATA: Health apps, Health Connect
- **Rule.** Health apps declaration in Play Console, Health Connect permission declaration with a privacy policy that covers health data, medical disclaimers, no ad use.

### X-PERIODIC-SENSING: User Data, prominent disclosure
- **Rule.** Collecting audio, camera or location data in a way the user would not expect needs a prominent in-app disclosure and consent before collection, and the Data safety form must list it. Background microphone use also requires a `microphone` foreground service type on Android 14+.
- **Fix.** Opt-in setting with a disclosure, visible indicator, stop when not in the foreground, declare in Data safety.

### X-ADS-PRESENT: Ads policy
- **Rule.** No ads that interfere with use, hidden close buttons, full-screen interstitials on app launch or exit without a natural break, ads on lock screens, or ads disguised as app content. Ad SDK data goes into Data safety (Device or other IDs, App activity, shared for advertising).

---

### EXPO-MANAGED: scan coverage
Managed Expo apps have no `ios/` or `android/` until build time, so only `app.json` was read. For a full check run `npx expo prebuild --no-install` in a scratch copy and scan that copy. `targetSdk` comes from the Expo SDK default or `expo-build-properties`.

---

## Beyond the scanner (always list under Manual checks if relevant)

- **Data safety form** matches `facts.sdk_categories` and the permissions: ads → device IDs shared, analytics → app activity, crash reporting → diagnostics, AI → user content shared, location → precise or approximate (new guidance from July 2026).
- **Content rating** questionnaire done (unrated apps are not allowed) and consistent with UGC and AI features.
- **Target audience and content**, Families self-certification if under 13.
- **Developer verification**: all apps registered in Play Console (deadline 2026-09-30 has passed).
- **App access**: demo credentials for login-gated apps, in the App content page.
- **16 KB page size**: apps targeting Android 15+ must ship native libraries aligned to 16 KB. Check the AAB in App bundle explorer, update plugins with native code.
- **Account deletion web link** filled in Data safety.
- **Store listing**: no misleading claims, no ranking or "best" claims, screenshots of the real app, AI features labelled honestly.
- **Native Java/Kotlin apps**: Google's `play-policy-insights` skill (github.com/android/skills) adds deeper Data-safety source/sink tracing.
