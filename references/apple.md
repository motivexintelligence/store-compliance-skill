# Apple App Review Guidelines: what to check in code

Rules as of **2026-10-18**. Source: https://developer.apple.com/app-store/review/guidelines/
and Apple Developer News. Guideline numbers as Apple writes them.

## 2026 changes at a glance

| Date | Change | Why it matters in code |
|---|---|---|
| 2026-02-06 | **1.2** now covers apps with random or anonymous chat | Chat apps need filter, report, block, contact info. "Chatroulette-style" apps may be removed without notice |
| 2026-06-08 | **4.3(a)/(b)** spam rewrite. Saturated categories (dating, flashlight, sound effects, wallpaper, simple timers, fortune telling) need a "meaningfully different or improved experience". Apple may remove live apps that are not updated, improved or used | Templated or white-label apps from one codebase are at risk. Repeated low-effort submissions risk the developer account |
| 2026-06-08 | Kid and teen safety guidance revised. **1.2** adds developer responsibility for violating content. **4.5.3** names Live Activities as a spam channel | |
| 2026-06-04 | Texas SB 2420 back in effect for new Texas accounts. Declared Age Range API and PermissionKit Significant Change API | Apps with age-sensitive features should read the age range, not ask for a birth date |
| 2026-07-09 | Age-rating questionnaire adds social-media capability questions, **required since September 2026** for new apps and updates | Any UGC, chat, profile or follow feature changes the answers and adds a Social Media descriptor |
| 2026-09-09 | From **April 2027** uploads must be built with the **iOS 27 / iPadOS 27 SDK** (Xcode 27) | Plan the CI toolchain bump |
| 2026-10-05 | From **April 2027** submissions must include **iPhone Duo** screenshots | Metadata, not code |
| 2026-10-16 | **1.2** explicitly covers nonconsensual intimate imagery (NCII), including AI-generated. Apps must proactively prevent and remove it | Any AI image generation or editing feature |
| 2026-10-16 | **New 2.5.19**: no hidden, dormant or undocumented features. Adding features that were not in the reviewed version means removal from the App Store **and the Developer Program** (moved from 2.3.1 and made much stricter) | Review-mode switches, remote-config gates, code push |
| 2026-10-16 | New **2.3.14** (creative assets). **3.1.1(a)** music streaming entitlement folded into the External Purchase Link entitlement. Section 5: trafficking and child-exploitation ban extended to alternative distribution | |

Still in force from earlier rounds and frequently hit: 5.1.2(i) third-party AI
disclosure (Nov 2025), 5.1.1(v) account deletion, 4.8 login services, privacy
manifests (ITMS-91053), 2.5.18 ads, 3.1.x payments, 4.7 mini apps and chatbots.

---

## Findings by scanner ID

### X-REVIEW-MODE-SWITCH, X-REMOTE-FEATURE-GATES, X-HIDDEN-FEATURE: 2.5.19, 2.3.1
- **Rule.** "Don't include any hidden, dormant, or undocumented features." Features not in the reviewed binary that appear later lead to removal from the App Store and the Apple Developer Program.
- **Verify.** Read the flag. Does it hide functionality during review (`isReviewMode`, a server flag set while "in review", a build-number check)? Does a remote-config bool enable a whole feature that is off by default? Is the hidden menu reachable in release (not behind `kDebugMode`, `__DEV__`, `#if DEBUG`)?
- **Risk.** CRITICAL for anything that changes behaviour for reviewers. Account-level consequences, not just a rejection.
- **Fix.** Remove review-mode logic entirely. Ship remote-config features **on** in the reviewed build (staged rollout is fine if the reviewer can reach the feature) and describe them in the App Review notes. Keep kill switches (turning a feature *off*) and A/B tests of existing features. Gate debug menus with `kDebugMode`/`__DEV__` so tree-shaking removes them.

### X-CODE-PUSH: 2.5.2, 3.3.1(b) (Developer Program License Agreement)
- **Rule.** Apps may not download code that "introduces or changes features or functionality". Interpreted code is allowed only if it does not change the app's primary purpose or add features.
- **Verify.** Which OTA tool (Shorebird, CodePush, expo-updates, server-driven UI such as rfw/stac). Has it been used for features in the past (git log of patch releases)?
- **Fix.** Use OTA only for bug fixes. Put new features through review. Combined with 2.5.19 this is now an account-level risk.

### X-AI-IMAGERY: 1.2 (2026-10-16)
- **Rule.** Apps must proactively prevent and remove nonconsensual intimate imagery, including AI-generated. Failure to act after notice means removal.
- **Verify.** What does the generator accept (user photos of real people, face swap, "try on", undress-style edits)? Is there a prompt filter and an output classifier? Can users report a generated image?
- **Fix.** Block sexual or nude edits of real-person photos at the prompt and the output (provider safety settings plus your own classifier). Add in-app reporting on every generated image, a takedown process with a response time, and published contact info. Document the safeguards in the review notes.

### X-AI-DATA-SHARING: 5.1.2(i)
- **Rule.** "You must clearly disclose where personal data will be shared with third parties, including with third-party AI, and obtain explicit permission before doing so."
- **Verify.** What reaches the AI provider (user text, photos, voice, profile)? Is there a consent screen **before** the first call that names the provider or "third-party AI", and is the choice stored? Server-side calls count too.
- **Fix.** A one-time consent sheet before the first AI request: what is sent, to whom, why, with Accept and Not now. Block the feature until accepted, allow withdrawal in settings, and update the privacy policy and the App Privacy label.

### X-UGC-MODERATION, X-UGC-PRESENT, X-ANON-CHAT: 1.2, 1.2.1
- **Rule.** UGC apps (including AI content apps and random or anonymous chat) need: a filter for objectionable material, a report mechanism with timely response, the ability to block abusive users, and published contact information. Creator apps need age-restriction for content above the app's rating (1.2.1(a)).
- **Verify.** Find report and block UI on every UGC surface (posts, comments, profiles, messages). Is there server-side filtering? Does blocking actually hide content?
- **Fix.** Add Report and Block on each item and profile, a profanity or ML filter at write time, an admin queue with action inside 24 hours, a contact email in settings and on the listing. Also update the age-rating questionnaire (social-media questions).

### X-SIGN-IN-WITH-APPLE: 4.8
- **Rule.** If the app uses a third-party or social login for the primary account, it must also offer a login that limits data to name and email, lets the user hide their email, and does not track without consent. Sign in with Apple satisfies this.
- **Exempt.** Only your own account system, education or enterprise accounts, government or industry ID, clients for a specific third-party service.
- **Fix.** Add `sign_in_with_apple` (Flutter), `expo-apple-authentication` / `@invertase/react-native-apple-authentication` (RN), with equal prominence on the login screen.

### IOS-SIWA-ENTITLEMENT, X-SIWA-REVOKE: 2.1, 5.1.1(v)
- **Verify.** `com.apple.developer.applesignin` in the entitlements. On account deletion, the backend calls `https://appleid.apple.com/auth/revoke` with the user's refresh token or authorization code.
- **Fix.** Revoke at deletion time with a fresh authorization code. Flutter + Firebase: run a new `SignInWithApple.getAppleIDCredential(...)` (package `sign_in_with_apple`) in the delete flow and pass `credential.authorizationCode` to `FirebaseAuth.instance.revokeTokenWithAuthorizationCode(...)`, then delete the user. Do not take the code from `reauthenticateWithProvider(AppleAuthProvider())`: a cancelled sheet there can leave the provider stuck. Custom backends: exchange the code at `/auth/token` for a refresh token and call `/auth/revoke`.

### X-ACCOUNT-DELETION: 5.1.1(v)
- **Rule.** "If your app supports account creation, you must also offer account deletion within the app." Deactivation alone is not enough. Asking users to email or call is only acceptable for highly regulated industries.
- **Verify.** A reachable Delete Account action (usually Settings, Profile, Account) that deletes server data, not just signs out. Institution-provisioned accounts (SSO, school, employer) with no sign-up are exempt, so downgrade if you see none.
- **Fix.** Settings → Delete account → confirm → backend deletes or anonymises user data, revokes Sign in with Apple, cancels nothing automatically but tells the user how to cancel subscriptions.

### X-PRIVACY-POLICY-LINK: 5.1.1(i)
- **Rule.** Privacy policy link in App Store Connect **and inside the app**, easy to reach.
- **Fix.** A Privacy Policy row in settings and on the sign-up and paywall screens.

### IOS-USAGE-STRING-MISSING, IOS-USAGE-STRING-WEAK: 5.1.1(ii), 2.1
- **Rule.** Purpose strings must say clearly why the data is needed, ideally with an example. A missing key crashes the app at the permission call. Generic text ("This app needs camera access") is a common rejection.
- **Incomplete strings.** A string that is specific but leaves out a real use (it names voice notes but the app also listens for song recognition) is also a 5.1.1(ii) problem. Check every call site of the API against the text.
- **Fix.** "Camera is used to scan the QR code on your ticket." Cover every use. Localise the strings (`InfoPlist.strings`). Do not request a permission before the user reaches the feature.

### IOS-PERMISSION-HANDLER-MACROS: 2.1
- **Rule.** Not a guideline by itself, but the reviewer sees a feature that never works. `permission_handler` compiles each iOS permission out unless the matching `PERMISSION_*=1` macro is set in the Podfile `post_install`.
- **Fix.** In `ios/Podfile` → `post_install` → `GCC_PREPROCESSOR_DEFINITIONS`, add `'PERMISSION_CAMERA=1'` etc. for every `Permission.x` the Dart code requests.

### IOS-ATT, IOS-PRIVACY-MANIFEST-TRACKING: 5.1.2(i), 2.5.18
- **Rule.** Tracking (linking data with third parties for ads or measurement, IDFA) requires the App Tracking Transparency prompt. You may not gate features or rewards on accepting.
- **Verify.** Ad or attribution SDK present (wrapper packages count), the prompt is shown before the SDK initialises or loads ads (`requestTrackingAuthorization` natively, `AppTrackingTransparency.requestTrackingAuthorization()` or `Permission.appTrackingTransparency.request()` in Flutter, `requestTrackingPermissionsAsync()` in Expo), `NSUserTrackingUsageDescription` set, `NSPrivacyTracking` and `NSPrivacyTrackingDomains` in the privacy manifest.
- **Fix.** Call ATT once after the first screen is visible and before initialising ads. Without consent, ads must still work as non-personalised. The purpose string and any pre-prompt may not offer rewards ("allow tracking to earn credits" is a 5.1.1(iv)/3.2.2 rejection).
- **NSPrivacyTracking.** `true` (with `NSPrivacyTrackingDomains`) when the app or its SDKs track in Apple's sense: linking app data with third-party data for targeted ads or ad measurement, or sharing it with a data broker. Ad SDKs that use IDFA after ATT consent do. `false` is only correct when nothing tracks, for example ads served contextually without IDFA. If the file says `false` on purpose, check the reason against this definition and the App Privacy label.

### IOS-PRIVACY-MANIFEST, IOS-PRIVACY-MANIFEST-NOT-IN-TARGET: 5.1.1, ITMS-91053
- **Rule.** Required-reason APIs (UserDefaults, file timestamps, system boot time, disk space, active keyboards) need a declared reason in a privacy manifest. Third-party SDKs bring their own. Missing reasons block the upload.
- **Fix.** `ios/Runner/PrivacyInfo.xcprivacy`, added to the Runner target, declaring the app's own API reasons and collected data types. Keep SDKs updated so their manifests are current.

### IOS-BACKGROUND-MODES: 2.5.4
- **Rule.** Background audio only for audible playback, location only for navigation or fitness-type features, VoIP only for calls.
- **Fix.** Remove unused modes. Explain the used ones in the review notes.

### X-IAP-RESTORE, X-PAYWALL-TERMS, X-EXTERNAL-PAYMENT: 3.1.1, 3.1.2, 3.1.3
- **Rule.** Digital content and features must be sold through IAP. Purchased credits must not expire. A restore mechanism is required for restorable products. Subscriptions: at least 7 days, available on all the user's devices, and the paywall must state what the user gets, the price, the period and auto-renewal, with Terms of Use (EULA) and Privacy links. External purchase links only with the StoreKit External Purchase Link entitlement in eligible storefronts (US and EU rules differ).
- **Fix.** Restore Purchases on the paywall and in settings. Show price per period from StoreKit, renewal text, Terms and Privacy links. Remove "buy on our website" buttons for digital goods, or apply for the entitlement and show Apple's required disclosure sheet.

### X-WEBVIEW-WRAPPER: 4.2, 4.2.2
- **Rule.** Apps that are mainly a repackaged website, or offer no lasting value, are rejected. 4.3 saturated categories need a clear differentiator.
- **Fix.** Native navigation, offline state, push, device features. Or ship as a web app.

### X-PLACEHOLDER: 2.1(a), 2.3.3
- **Rule.** No placeholder text, empty screens or "coming soon" features in the submitted build.
- **Fix.** Hide unfinished entries (they can come back in an update that goes through review).

### X-KIDS-AUDIENCE: 1.3, 5.1.4
- **Rule.** Kids Category apps: no third-party analytics or ads (narrow exceptions), parental gate before links, purchases and permission prompts. Apps "for kids" outside the category still have to follow COPPA, GDPR-K and local law. Names may only say "For Kids" or "For Children" inside the Kids Category.
- **Fix.** Remove ad and analytics SDKs or move to first-party, add a parental gate, check the age range.

### X-HEALTH-DATA: 5.1.3, 1.4.1
- **Rule.** HealthKit data may not be used for ads or stored in iCloud. Medical apps must remind users to consult a doctor. Vitals measured with device sensors alone are not allowed.

### X-PERIODIC-SENSING: 2.5.14, 5.1.1(ii)
- **Rule.** Recording or sampling the microphone, camera or location must be something the user started, with consent and a visible or audible indicator. Opening the mic on a timer (ambient listening, "shake or hum to search") without a clear opt-in looks like covert surveillance.
- **Verify.** Read the file: what starts the timer, how long the sensor stays open, is there an opt-in setting and an on-screen indicator, does the purpose string mention it.
- **Fix.** Make it opt-in from a settings toggle that explains it, show an indicator while listening, stop when the screen is not visible, mention it in the purpose string and the review notes. If it is not essential, remove it.

### X-RECORDING: 2.5.14
- **Rule.** Explicit consent and a clear visual or audible indicator while recording audio, video or the screen.

### X-MARKETING-PUSH: 4.5.4, 4.5.3
- **Rule.** Push for marketing needs explicit opt-in and an in-app way to opt out. Live Activities and push may not be used to spam.

### X-ADS-PRESENT: 2.5.18
- **Rule.** Ads only in the main app binary (not in extensions, widgets, keyboards). Users must be able to see the targeting info and report inappropriate ads. No ads that are hard to close or mimic system UI.

### IOS-EXPORT-COMPLIANCE
- Set `ITSAppUsesNonExemptEncryption` to `false` if the app only uses HTTPS and OS crypto, so uploads skip the manual question.

---

## Beyond the scanner (always list under Manual checks if relevant)

- **4.3 spam.** Is this app one of several near-identical apps from the same codebase or account (white-label, templated)? Is the category saturated? What makes it different?
- **2.1 review access.** Demo account in the review notes, backend live, any region or institution lock explained.
- **2.3 metadata.** Screenshots show the real app, name ≤ 30 characters, no prices or other platforms in the name, keywords not stuffed. New 2.3.14 creative assets rules. iPhone Duo screenshots from April 2027.
- **Age rating.** Questionnaire answered with the new social-media questions (required since September 2026). UGC, chat, AI generation and gambling-like mechanics all change the answers.
- **App Privacy label** matches the SDK list in `facts.sdk_categories` (ads → identifiers and usage data, crash reporting → diagnostics, AI → user content).
- **Declared Age Range / Texas.** Age-gated or social features for US users.
- **Toolchain.** Xcode 27 / iOS 27 SDK from April 2027.
- **4.7** mini apps, mini games, chatbots, emulators: content must be within the app's rating and moderation rules.
- **5.1.1(iv)** no forcing users to enable tracking, notifications or reviews to unlock features.
