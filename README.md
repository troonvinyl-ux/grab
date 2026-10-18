# MyGab TV

MyGab TV is a Fire TV / Fire Stick-friendly, web-served video feed. This repository packages the existing MyGab TV prototype as a standalone app so it can be maintained and deployed independently.

## Features
- TV-first, remote-friendly video feed
- Admin controls protected by PIN `1802`
- Search and source/category configuration
- Import video links from URLs, including supported public video pages and direct media URLs
- Provider-hosted playback; this app does not host video files

## Run locally
Open `index.html` in a browser or serve this folder with any static web server.

## Publish with GitHub Pages
1. In repository Settings → Pages, choose **GitHub Actions** as the build/deployment source.
2. Pushes to `main` trigger the included deployment workflow.
3. Once the workflow succeeds, open the Pages URL shown under Settings → Pages.

For Fire Stick, open the published URL in the Silk browser and add it to bookmarks. This is the web-app route; an Android APK build is not included yet.
