# Northstar Onboarding Desk — shared A2A agent for LAB-1439

A small, **read-only, synthetic** onboarding specialist for the IBM watsonx Orchestrate Project Orion lab. It implements the A2A **0.3.0 JSON-RPC** message/send protocol, serves an agent card at both well-known locations, requires a Bearer token for requests, and returns a six-control onboarding checklist for proposed Java developer hires.

No IBM credentials, HR-system credentials, language-model API keys, or databases are needed. It **never creates employees or provisions accounts**. It is a workshop interoperability example, not a production HR service.

## 1. Put the files into a private GitHub repository (website only)

1. Download `Northstar_Onboarding_Desk_GitHub_Repo.zip` and extract it on your laptop.
2. Go to https://github.com/new and sign in (or create a GitHub account).
3. Set **Repository name** to `northstar-onboarding-desk-a2a`.
4. Select **Private**. You may leave the README / .gitignore initialization unchecked, because this package already contains them.
5. Select **Create repository**.
6. On the empty repository page choose **uploading an existing file** (or **Add file → Upload files**).
7. Drag the **extracted files**, not the `.zip`, into GitHub. Required items must be in the repo root: `app.py`, `requirements.txt`, `render.yaml`, `README.md`, `test_a2a.py`, `verify_remote.py`, `.gitignore`, `.env.example`.
8. Select **Commit changes** and confirm that `app.py`, `requirements.txt` and `render.yaml` appear at the top level (not inside an extra folder).

**Security:** Never commit an actual A2A token, IBM password, `.env` file, or client keys to GitHub.

## 2. Deploy on Render (website only)

1. Visit https://dashboard.render.com and sign in or sign up, using GitHub if convenient.
2. Choose **New → Web Service**.
3. Connect GitHub and grant access to `northstar-onboarding-desk-a2a` (for a private repo, authorize Render's access).
4. Choose this repository and click **Connect**.
5. Fill the Render form as follows:

| Render field | Value |
|---|---|
| Name | `northstar-onboarding-desk` (or another available unique name) |
| Language / Runtime | `Python` |
| Branch | `main` |
| Root Directory | leave blank |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app:app --host 0.0.0.0 --port $PORT` |
| Instance Type | `Free` for initial testing; `Starter` is better for a time-critical event |
| Health Check Path (if offered) | `/health` |

6. In **Advanced → Environment Variables**, create:

| Key | Value |
|---|---|
| `A2A_BEARER_TOKEN` | A unique long random string (32+ characters). Copy this to your password manager; **do not put it in GitHub**. |

Optionally set `PUBLIC_BASE_URL` after Render assigns the service URL. Example: `https://northstar-onboarding-desk.onrender.com` (no trailing slash). It normally derives the public URL from Render's `RENDER_EXTERNAL_HOSTNAME` automatically.

7. Select **Create Web Service**. Watch Logs/Deploys until the status is **Live**.
8. Copy the actual URL shown by Render, e.g. `https://YOUR-SERVICE.onrender.com` (this is an example, not a guaranteed assigned URL).

**Alternative:** the included `render.yaml` supports **New → Blueprint** instead of Web Service and will prompt you for `A2A_BEARER_TOKEN`. The free plan is specified in that file. Do not configure both methods; use one or the other.

## 3. Check deployment before registering with Orchestrate

Open these URLs in your browser, substituting the actual Render service address:

- `https://YOUR-SERVICE.onrender.com/health` — expects `"status":"ok"`
- `https://YOUR-SERVICE.onrender.com/.well-known/agent-card.json` — expects `"protocolVersion":"0.3.0"`, and `"url":"https://YOUR-SERVICE.onrender.com/a2a"`
- `https://YOUR-SERVICE.onrender.com/.well-known/agent.json` — compatibility alias; same agent card.

The browser can read the Agent Card **without** credentials. Actual agent requests are protected with a bearer token.

To verify the real A2A JSON-RPC request from your computer (Python 3 required):

```bash
# macOS/Linux shell, in the extracted project folder:
export A2A_BASE_URL="https://YOUR-SERVICE.onrender.com"
export A2A_BEARER_TOKEN="<your-token-from-render>"
python verify_remote.py
```

On Windows PowerShell:

```powershell
$env:A2A_BASE_URL="https://YOUR-SERVICE.onrender.com"
$env:A2A_BEARER_TOKEN="<your-token-from-render>"
python verify_remote.py
```

The script should print **PASS** and a six-control checklist. If the service is on the Free plan, the first request after idle may take approximately a minute to wake up.

## 4. Register it as a shared external A2A agent in watsonx Orchestrate

The organizer does this **once**, not per attendee.

1. Open the Orchestrate event tenant: https://ap-south-1.dl.watson-orchestrate.ibm.com/home
2. Open a native coordinator agent, or create the organizer's testing coordinator.
3. Go to **Agents / Toolset → Add agent → Import from external sources → External agent**. UI naming varies slightly by version.
4. Under **External protocol**, choose **External agent via A2A standard**.
5. Fill fields:

| Orchestrate field | Value |
|---|---|
| Protocol version | `0.3.0` |
| External agent URL | `https://YOUR-SERVICE.onrender.com/a2a` (actual address; use the URL published by the Agent Card) |
| Display name | `Northstar Onboarding Desk (Shared A2A)` |
| Description | `Fictional Project Orion onboarding specialist. Produces six required checks and owners for proposed Java developer hires: hiring approval, right-to-work validation, security induction, role-based access, device provisioning and manager sign-off. Advises only; does not create records or grant access.` |
| Supports streaming | **Off** |
| Push notifications | **Off** |
| Send conversation history | **Off** for this stateless demo |

6. On the **Connect** step select **Add A2A agent connection**. Configure a **Bearer token** authentication method with the exact `A2A_BEARER_TOKEN` from Render. Set the same token for **Draft and Live**, as supported by the UI. Do not paste it into a description or chat.
7. Complete registration, then test the external agent in Draft Preview with:

> Prepare the standard onboarding checklist for two proposed Java developers joining Project Orion. List six controls, the responsible teams, and clarify whether any onboarding actions have been executed.

Expected: Six controls with owners, an approximate first-week order, and an explicit statement that **no action was executed**.

8. Ensure the external agent is available as a collaborator for the participant coordinators. Repeat a Live test through a published coordinator to confirm both the connection and runtime are working.

**A2A URL note:** The published Agent Card's `url` points to `/a2a`, where JSON-RPC requests are accepted. This service also accepts POST requests at `/` as a compatibility alias and exposes both legacy and current Agent Card paths. If registration rejects the address, inspect the exact URL requested in your Orchestrate build and the Render logs before changing the configuration.

## 5. Workshop-ready participant instruction (copy into Part B)

> Open **Agents** on your Project Orion coordinator. Search for **Northstar Onboarding Desk (Shared A2A)**. Confirm its origin is External / A2A. Add it as a collaborator. Then run: “Prepare a checklist for onboarding two Java developers to Project Orion. Show six checks with owners. What has actually been executed?” Check that the response lists six controls and explicitly says no live HR action was performed. **Do not register the external agent again.**

## 6. Local development and tests (optional)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
pip install httpx  # only for tests
export A2A_BEARER_TOKEN="local-test-secret-at-least-32-characters"
export PUBLIC_BASE_URL="http://localhost:8000"
uvicorn app:app --host 0.0.0.0 --port 8000
```

In another terminal: `python -m unittest test_a2a.py`.

## 7. Troubleshooting and operating limits

- **Render Build failed:** ensure the `.py`, `requirements.txt`, `render.yaml` are in the repo root. Inspect Deploy logs.
- **Render Live but `/health` fails:** check the Start Command includes `--host 0.0.0.0 --port $PORT`.
- **Agent Card URL contains localhost:** set `PUBLIC_BASE_URL=https://YOUR-SERVICE.onrender.com`, then redeploy.
- **401 unauthorized on A2A invocation:** the Orchestrate Bearer token must exactly match the Render secret; ensure Draft and Live are both configured.
- **A2A import fails:** confirm you selected protocol `0.3.0`, the endpoint shown in the Agent Card, and streaming is OFF. Verify `/a2a` directly with `verify_remote.py`.
- **First response slow:** Render Free sleeps after 15 minutes idle. Use Starter for the workshop or warm it before the session; do not promise zero cold-start.
- **Cannot find external agent in participant's collaborator list:** organizer must first register and share/publish the external agent; then refresh the catalog.
- **Unexpected task/get after restart:** this demo keeps tasks only in memory. It supports immediate completed responses; historical task IDs are not durable across redeploys. Use one instance for the workshop.
- **No LLM reasoning:** checklist is deterministic synthetic data. It demonstrates A2A and orchestration, not autonomous hiring workflows.

## Protocol and product references

- IBM: https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=platforms-adding-agents-from-third-party
- IBM connections: https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=center-adding-agent-agent-connection
- A2A 0.3 specification: https://a2a-protocol.org/v0.3.0/specification/
- Render Web Service: https://render.com/docs/web-services
- Render Free limitations: https://render.com/docs/free
