# Phone Troubleshooter

A small local web app that searches the supplied troubleshooting dataset. It uses Python's standard library only: no Node.js, npm, API key, or pip installation is required.

## Windows quick start

1. Install Python 3.10 or newer if it is not already installed. Check with `py --version`.
2. Extract the ZIP file.
3. Open the extracted `phone-troubleshooter` folder.
4. Double-click `start_windows.bat`.
5. The app opens at <http://127.0.0.1:8000>. Leave the black server window open while using it. Press Ctrl+C in that window to stop.

If the browser opens before the app is ready, wait a few seconds and refresh. If the app says port 8000 is in use, close another running copy first.

## What it does

The app compares the user's description with all 20 supplied issue examples and the titled sections throughout their SIIS responses (105 sections total, including repeated headings). It then shows relevant text from the closest guide. It never generates a fix outside the supplied content. If it cannot find a close match, it says so and asks for more detail. The start page initially shows six examples and has a button to reveal all 20.

The dataset includes 578 deeplink catalog entries, but their URIs are masked placeholders. The app shows related link descriptions as previews; they cannot open actual Samsung settings screens. The sample data also uses TechCorp/Nexa names. Replace these with verified Samsung data and working links before presenting the app as official or phone-ready.

## Conversation and language helpers

- Multi-turn chat keeps the recent messages on screen and carries a detected phone model into follow-up searches. Search still comes only from the local dataset; it does not generate free-form answers.
- Severity is a small keyword estimate (low / routine / high). It is not a diagnostic assessment. For high wording, the app moves matching service/support sections earlier when the source article contains them.
- Device names are detected, but the supplied dataset contains TechCorp/Nexa examples rather than verified Galaxy S24/A14 guides. The app warns when it cannot find that exact model in the selected record.
- A small phrase map handles a few typed Hinglish phrases such as “battery jaldi khatam” and “phone on nahi ho raha.” This is not full Hindi translation or voice transcription. Battery issues currently return a clear missing-data message because the files do not include battery-drain guidance.

## Files

- `server.py`: local search and web server.
- `web/`: browser interface.
- `data/`: supplied SIIS, deeplink, and example-query data.
- `reference/`: supplied response schema and sample output.

The server binds only to `127.0.0.1` on this computer. Search queries stay local; no OpenAI API is called.

## Always-on public hosting (Render)

The repository includes `render.yaml` for Render. It uses the paid Starter web-service plan so the service does not use the free-tier inactivity spin-down. Render pricing and plans can change; check the current service price before creating it. No hosting provider can promise a service will exist forever, but a paid always-on service stays public while its account, billing, and deployment remain active.

1. Put the contents of this project folder in a GitHub repository. Use a private source repository if the dataset is not approved for public redistribution; the deployed app itself is public.
2. Sign in to Render, connect GitHub, and create a Blueprint from that repository. Render reads `render.yaml`, builds the service, and provides an `onrender.com` URL.
3. Keep the Render account and billing active. Add a custom domain only if desired.

The server reads Render's `PORT` and binds to `0.0.0.0` when deployed. The local Windows launch behavior remains on `127.0.0.1:8000`.

## Vercel deployment

The project includes `app.py`, a FastAPI adapter that exposes the existing Python troubleshooting engine through Vercel's Python runtime. It uses the same `search()` implementation as the local app; it is not the simplified browser-only Netlify version. Vercel's Python runtime is currently in Beta and runs the app through serverless functions rather than as a permanently running server.

1. Create a GitHub repository and upload the contents of this project folder.
2. Sign in to Vercel, choose **Add New → Project**, and import that GitHub repository.
3. Keep the project root at this folder. Vercel should detect FastAPI from `requirements.txt`; leave the build command empty.
4. Select **Deploy**. The site is served from `public/`, and the `/api/...` endpoints use the Python app.

No OpenAI key is needed for the current dataset search. This project does not yet use an AI model to generate ChatGPT-style answers. Add that separately only after the model provider and key are configured securely in Vercel. Vercel Functions have plan-dependent usage and duration limits, so hosting is not guaranteed forever. The supplied deeplinks remain masked placeholders and cannot open real Samsung settings screens.
