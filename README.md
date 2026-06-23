# Nate's AI Assistant

---

## 1. What this project is

This is AI assistant for a CPA / realtor specializing in **real estate tax strategy**. Clients ask questions in a chat window, and the assistant answers using the firm's own material:

- **Knowledge Base** — uploaded PDFs and Word documents (guides, scripts, research).
- **Q&A library** — real advisor answers extracted from past client chats and meeting transcripts.

It is one web app with a login screen, a chat interface, an admin area to **upload/manage documents**, and an area to **invite users**.

---

## 2. Repository map (high level)


| Folder          | What lives there                                                                              |
| --------------- | --------------------------------------------------------------------------------------------- |
| `backend/`      | The server — handles chat, search, document upload, logins, and talks to all outside services |
| `frontend/`     | The website users see — login, chat, document management, user invites                        |
| `llm_pipeline/` | Offline tool that turns past conversations into the Q&A library                               |
| `scripts/`      | One-off maintenance utilities                                                                 |
| `deploy/`       | Deployment configuration (auto-publishes the app to the cloud)                                |
| `docs/`         | Internal documentation (this file, plus technical pipeline docs)                              |
| `data/`         | Local working data                                                                            |


---

## 3. External services used

The system depends on **4 outside services** (plus the code host). Most run on **free tiers**; the only guaranteed monthly costs are hosting and AI usage.

### 3.1 OpenRouter — AI models  *(paid, usage-based)*

- **What it does:** Provides the AI brains. One account gives access to the models used: **GPT-5.1** (writes the answers), **GPT-4.1-mini** (refines questions & double-checks answers), and a **text-embedding** model (lets the system "understand" documents for search).
- **Cost:** Pay only for what you use — no monthly fee, no free tier.
  - GPT-5.1: ~$1.25 per million words-in, ~$10 per million words-out.
  - GPT-4.1-mini: ~$0.40 / ~$1.60 per million (much cheaper).
  - Embeddings: ~$0.13 per million.
  - *In practice, light real-world usage typically runs **~$5–30/month**.*
- **Link:** [https://openrouter.ai/pricing](https://openrouter.ai/pricing)

### 3.2 Qdrant Cloud — search database  *(FREE tier)*

- **What it does:** Stores documents in a way the AI can search by meaning, not just keywords.
- **Cost:** **Free** — 1 GB cluster, no credit card. Holds roughly 1 million document chunks; enough for this project. (Note: free clusters pause after ~1 week of no activity.)
- **Link:** [https://qdrant.tech/pricing/](https://qdrant.tech/pricing/)

### 3.3 Clerk — login & user management  *(FREE tier)*

- **What it does:** Handles sign-in, user accounts, admin vs. client roles, and the "invite a user" emails.
- **Cost:** **Free** up to **50,000 active users**. Paid plans start at $20/month only if you exceed that or need advanced features.
- **Link:** [https://clerk.com/pricing](https://clerk.com/pricing)

### 3.4 DigitalOcean App Platform — hosting + database  *(paid)*

- **What it does:** Runs the live website and server in the cloud, and hosts the **PostgreSQL database** (conversations, user settings, system prompt). Re-publishes automatically whenever code is updated.
- **Cost:** **~$17/month** total (app server + managed database). This is the main fixed cost.
- **Link:** [https://www.digitalocean.com/pricing/app-platform](https://www.digitalocean.com/pricing/app-platform)

### 3.5 GitHub — code storage  *(FREE)*

- **What it does:** Stores the source code (`AxonBuild/nate-rag`) and triggers the automatic re-publish on DigitalOcean.
- **Cost:** **Free.**

---

## 4. Cost summary


| Service             | Purpose                 | Monthly cost                 |
| ------------------- | ----------------------- | ---------------------------- |
| OpenRouter          | AI models          | Usage-based (~$5–30 typical) |
| Qdrant Cloud        | Search database    | **Free**                     |
| Clerk               | Login / users      | **Free** (under 50k users)   |
| DigitalOcean        | Hosting + database | ~$17                         |
| GitHub              | Code storage       | **Free**                     |
| **Estimated total** |                    | **~$22–47 / month**          |


*Figures are indicative (checked June 2026); always confirm on each provider's pricing page.*

---

## 5. Setup checklist

To stand up a fresh copy of the system, create an account on each service and plug its keys into the configuration. **Keys are secrets — never share them publicly.**

1. **OpenRouter** → sign up, add credit, create an API key → set `OPENAI_API_KEY` (base URL `https://openrouter.ai/api/v1`).
2. **Qdrant Cloud** → create a free cluster → copy its URL and API key → set `QDRANT_URL`, `QDRANT_API_KEY`.
3. **Clerk** → create an application → copy the Publishable + Secret keys → set `CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, and `VITE_CLERK_PUBLISHABLE_KEY`. Mark admins in Clerk via *Users → Public metadata → `{ "role": "admin" }`*.
4. **DigitalOcean** → connect the GitHub repo, apply the deployment config in `deploy/`, add a managed **PostgreSQL** database (set `DATABASE_URL`), and paste the keys above into the app's environment settings.
6. **GitHub** → pushing to the `main` branch automatically re-publishes the live app.

Settings are stored in environment files (`backend/app/.env` and `frontend/.env`); examples are provided in the repo. A technical walkthrough lives in `docs/PIPELINE_DOCUMENTATION.md`.



