---
purpose: Work for the administrators: alerts, requests waiting for approval, the ban list, and the log of DMs sent to users.
topic: Handle the posts that mention the admins | Ban list: the pinned message | DM log: one thread a day
title: Admin channel guide
bookmark: :books: | User docs | index.md
bookmark: :newspaper: | Notices | news/index.md
---
# Admin channel

Posts that mention [[admins]] need an administrator. The rest are kept as a record.

- **Alert (Alertmanager)**: check what the alert says. The same alert posts again when it resolves.
- **Request waiting for approval (bot)**: approve or reject with the buttons. The bot tells the requester by DM.
- **New ban (bot)**: the pinned ban list picks it up. A user asks for an unban with `[[/cluster]] unban`.
- **Admin note in a usage report**: look into what the report names, such as a job leaving its GPUs idle.
- **DM log (a thread a day)**: what the bot and the tools sent to users. When a user asks, check here what they got.

## Pinned message

- The current ban list, pinned once; the bot keeps it up to date.
