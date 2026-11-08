# Following CRT / ICT traders on X (no API)

## Approach: browser automation instead of the X API

We read traders' posts the way a person does, in a logged-in browser:

| Option | How | When |
|---|---|---|
| A. Claude computer use / Claude in Chrome | Claude opens each trader's profile in **your** browser on a schedule and reads new posts and chart images | Prototyping, a few traders |
| B. Playwright bot with your saved X session | A small script on your PC/VPS opens the profiles, takes screenshots and the post text, and sends them to the parser | Running all day |

Both options feed the same pipeline:

```
profile page -> new posts since last check -> text + chart screenshot
  -> LLM extracts {pair, direction, TF, entry, SL, TP, model (CRT/TS/OB...)}
  -> stored in trader_setups table
  -> scorecard checks it against real price afterwards
```

## Rules to keep the X account safe
X's terms prohibit automated scraping, and accounts that behave like bots get
rate-limited or suspended. To keep the risk low:

- Use a **separate X account**, not your main one.
- Check each profile at most every 15–30 minutes, and only during the
  London and New York sessions.
- Make it look human: random delays, no parallel tabs, a normal browser profile.
- Never post, like or follow from automation. Read only.
- Telegram/Discord channels are a backup. Many of these traders mirror their
  posts there, and those are much easier to read reliably.

## Trader signals are votes, not triggers
A trader's post can only confirm or reduce a trade that our own CRT engine
found. Before a trader's votes count at all, they must have **at least 30
tracked setups** with a verified hit rate. See `watchlist.md`.
