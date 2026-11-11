# Macro template — MacroDroid webhook → accessibility actions

Hand these specs to the human; every macro is built by tapping. Package `com.arlosoft.macrodroid`
(launcher `com.arlosoft.macrodroid.intro.IntroActivity`), free tier = 5 macros, ads.

| Macro | Trigger | Action 1 | Action 2 (optional) |
|---|---|---|---|
| `SHOT` | Connectivity → **Webhook (URL)** | Device Actions → **Take Screenshot** → `Download/hermes/shot.png` | Applications → **Shell Script** → `touch /sdcard/Download/hermes/shot.done` (completion marker) |
| `TAP` | Connectivity → **Webhook (URL)**, separate URL | Device Actions → **UI Interaction** → **Click**, `Text content` = magic text of the incoming `text` parameter | wait 500 ms → Take Screenshot |
| `SWIPE` / `KEY` | Connectivity → **Webhook (URL)**, third URL | UI Interaction → **Swipe** (`dir`) or **Press Key** (`back` / `home`) | — |

After each trigger is created the app **prints the full URL**. The human screenshots it; the agent
copies it into `webhook.conf` as `BASE=`. Never invent the URL — the path and secret are app-generated.

Prerequisites the human must complete (agent cannot):

1. Install from Play Store (`https://play.google.com/store/apps/details?id=com.arlosoft.macrodroid`).
2. Phone `Tetapan` → bottom → `Kebolehaksesan` → `Apl yang dimuat turun` → MacroDroid → on → `Benarkan`.
3. Build the macros above.

Acceptance test (agent runs):

```bash
cd ~/phone_bridge && ./mdr.sh shot          # expect ~/storage/downloads/hermes/shot.png > 10 KB
./mdr.sh tap "Tetapan"                      # expect the screen to change
```

Pass = the PNG exists **and** the agent can read text inside it. Anything less = not proven.
The screenshot action needs a one-time MediaProjection consent granted on the phone.
