# Banner source

`banner.js` draws the README banner as SVG. `banner.html` renders it with the
web fonts (Inter, Geist Mono) so the PNG looks the same everywhere.

Rebuild both PNGs from this folder:

```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for mode in light dark; do
  "$CHROME" --headless=new --hide-scrollbars --force-device-scale-factor=2 \
    --virtual-time-budget=6000 --window-size=1280,420 \
    --screenshot="$PWD/../banner-$mode.png" "file://$PWD/banner.html#$mode"
done
```

Store icons come from Wikimedia Commons (`Google_Play_2022_icon.svg`,
`App_Store_(iOS).svg`, `Huawei_AppGallery.svg`). App Store is a trademark of
Apple Inc., Google Play of Google LLC and AppGallery of Huawei Technologies.
