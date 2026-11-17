# Platform rules — Malaysia social commerce (starting specs)

Verify field limits in the app before shipping; platforms change them without notice.
These are working defaults, not gospel.

## Shopee (MY)
- **Listing title:** up to ~255 chars; front-load 3 keywords buyers actually type. Practical: 100–150 chars readable.
- **Images:** up to 9. Image 1 must be product on clean/white background (algorithm + trust).
- **Video:** attach the 16s vertical render to the listing; it plays in search results.
- **Description:** structure as 5 bullets + spec table + CTA. Avoid emoji walls.
- **Price/stock/weight:** wrong weight = wrong shipping fee = bad reviews. Always confirm.
- **Category:** wrong category kills discovery. Beauty needs the correct sub-category.
- **Cosmetics:** must be **NPRA/KKM notified**. Ask supplier for the notification number and keep the certificate on file. No medical/therapeutic claims (no "sembuh", "hilang", "putih dalam X hari").
- **Harvesting data:** web search page is an SPA shell and `api/v4/search` is 403 — get numbers from Seller Centre → Analytics, or from links the user provides.

## TikTok
- **Caption:** ~2,200 chars. First line is the hook; keep it under ~100 chars visible.
- **Hashtags:** 3–5 relevant, mix 1 broad + 2 niche + 1 product. More than ~8 looks spammy.
- **Link:** Shopee link belongs in **bio**, not in the caption or on-screen ("klik link Shopee" can suppress reach).
- **Video:** 9:16, 1080×1920. Keep all text inside the safe zone (clear of top ~250 px and bottom ~320 px).
- **TikTok Shop cannot sell — check Account Health for:** business/SSM verification pending, beauty category requiring NPRA docs, account restricted for policy breach, shop not linked to the TikTok account, empty stock or pickup address.

## Facebook
- Long copy fine; first 2 lines decide whether "See more" is tapped.
- Put the Shopee link in the first comment as well as the post (edge-rank safe).
- Reels: same 9:16 file as TikTok works.

## Instagram
- **Caption:** ~2,200 chars; first line must stand alone.
- **Hashtags:** 8–12 in the caption or first comment, mix of size tiers. Avoid banned/spam tags.
- Link in **bio** only; captions are not clickable.
- Reels: same 9:16 file.

## YouTube (Shorts)
- **Title:** ≤100 chars, put the search keyword first; append `#Shorts`.
- **Description:** ≤5,000 chars; first 2 lines visible. Put the Shopee link high.
- Shorts up to 60s; 16s renders fine.

## Hashtag master list (per product)
Build one file with tiers so every platform draws from it:
1. **Broad** (high volume): `#racunshopee #tiktokmademebuyit #shopeemalaysia`
2. **Niche** (category): `#skincareroutine #sunscreenmalaysia #hijabstyle`
3. **Product/brand**: product name + own shop handle
4. **Problem-led**: what the buyer complains about (`#kulitberminyak`, `#jeragat`)
Rule: never reuse the exact same 10 tags on every post — rotate.
