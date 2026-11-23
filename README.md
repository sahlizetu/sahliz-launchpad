# Sahliz Launchpad

Sahliz Launchpad helps startups create crowdfunding campaigns and mint ERC-20
tokens on Ethereum Sepolia. Startups set a funding goal, token price, and supply.
After administrator approval, the startup deploys the campaign through MetaMask.
Contributors use test ETH to participate, then claim tokens if the goal is met
or request a refund if the campaign falls short.

Built with Django, Solidity, and ethers.js. The interface defaults to English
and offers French, Arabic with right-to-left layout, and light and dark themes.

## Local setup

Use Python 3.12 or 3.13. Install Node.js to compile or test the smart contracts.

In PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DEBUG = "1"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Open http://127.0.0.1:8000/. On Linux, use `python3 -m venv .venv`,
`.venv/bin/python`, and `export DEBUG=1`.

## Update an existing installation

Stop the server and copy the release files into the directory containing
`manage.py`. The release contains the source code. Keep your existing
SQLite database and virtual environment. In PowerShell, with the virtual
environment active, run:

```powershell
$env:DEBUG = "1"
python manage.py migrate
python manage.py seed_startups
python manage.py runserver
```

If the original catalog accounts exist, the seed command reuses their two
public wallets for the four startups and hides the two original catalog
campaigns. For a fresh installation, pass two or four distinct public wallet
addresses to `seed_startups` in this order: AtlasAI, GreenBox, AquaNorth,
MedRoute. With two addresses, AtlasAI and AquaNorth share the first, and
GreenBox and MedRoute share the second. Rerunning the seed command preserves
existing campaign records and configured wallets.

## Contribution flow on Sepolia

1. Fund the issuer and contributor wallets with test ETH.
2. Sign in as an administrator and open `/installation/`. Deploy the campaign
   factory if needed. Copy its public address, set
   `$env:FACTORY_ADDRESS = "0x..."` in PowerShell, and restart Django.
   You can reuse an existing Sepolia factory.
3. Set passwords for the issuer accounts using
   `python manage.py changepassword atlas-ai` and
   `python manage.py changepassword greenbox-ventures`. Each startup signs
   in and deploys its campaign with its assigned wallet. The seeded campaigns
   run for 15 minutes from deployment.
4. From a contributor wallet, reserve **100 ATLS** for **0.001 test ETH** to
   meet AtlasAI's goal and **10 GBX** for **0.0001 test ETH** to leave
   GreenBox below its goal.
5. After both campaigns close, refresh their pages. The contributor can claim
   the 100 ATLS and request a refund from GreenBox. The AtlasAI issuer can
   withdraw the funds raised. The transaction links open Sepolia Etherscan.

The other issuer accounts are `aquanorth` and `medroute`.

To launch a new campaign, submit it from the startup dashboard, approve it
in `/admin/`, and deploy it from the campaign page using the startup wallet.
The factory identifies the campaign by its UUID and the issuer's public
wallet address.

## Tests

```text
npm ci
npm run compile
npm test
python manage.py test --settings=launchpad.test_settings
```

The Ganache test deploys campaigns for two issuers, advances time, and checks
withdrawals, ERC-20 token claims, and refunds. The Django tests cover the
catalog, approval and deployment permissions, and language selection.

## Deploy from GitHub to Render

1. Extract the release ZIP and upload its contents to the repository root.
2. In the Render dashboard, create a **Blueprint** linked to the repository.
   The `render.yaml` file configures the Django web service. The build script
   installs dependencies, collects static assets, and applies migrations.
3. Set `DATABASE_URL` to a persistent PostgreSQL connection string and
   `FACTORY_ADDRESS` to the public address of your Sepolia factory. Render
   generates the Django secret key and the app accepts the Render hostname.
4. Open the HTTPS URL shown by Render. Import your catalog before sharing
   the link if the hosted database is new.

To keep existing Sepolia campaigns, transfer their Django records and
associated startup accounts. Preserve the campaign UUIDs and the public
issuer addresses. Keep database exports and connection credentials outside
GitHub. Compare a campaign contract address before and after importing to
verify that both installations point to the same contract.

For a new database, the optional `DEMO_WALLETS` environment variable accepts
two or four space-separated public addresses to seed the catalog. Use the order
AtlasAI, GreenBox, AquaNorth, MedRoute.

Run `python manage.py createsuperuser` once against the hosted database to set
up administrator access. Use a Render shell if available, or a trusted local
terminal configured with the database's external connection URL. Set passwords
for startup accounts in Django admin or with `manage.py changepassword`.

## Portfolio links and mobile access

Use the Render HTTPS URL for a button on your portfolio. To redirect an existing
URL, configure an HTTP **302** at the source host and switch to **301** if the
redirect is permanent. To link to a single campaign, use its full
`/campagnes/<uuid>/` URL.

On iPhone or Android, open the HTTPS URL and add Sahliz Launchpad to the home
screen. To contribute, open a campaign and select **Open in MetaMask**.

All contributions use test ETH. Sepolia tokens carry no equity or dividend rights.

## Startup registration and campaign fees

New startups can register from the sign-in page with a contact email, then sign
a wallet verification message before submitting campaigns. Email confirmation
is deferred. The signature verifies control of the wallet for the current
session and does not broadcast a transaction.

Configure the fee-enabled factory separately from the original factory:

1. As a Django superuser, open the setup page and deploy the new factory on
   Sepolia using the wallet that will authorize campaigns. Set the resulting
   address in the server environment as `FEE_FACTORY_ADDRESS`.
2. Set `SEPOLIA_RPC_URL` to an HTTPS Sepolia JSON-RPC endpoint reachable from
   the server. Django uses it to verify deployment before public listing.
3. On an existing installation, keep the SQLite database and the original
   `FACTORY_ADDRESS`. Install the updated requirements, run
   `python manage.py migrate` and `python manage.py collectstatic --noinput` with
   the existing Django secret configured, then reload the web app.

For each new campaign, set an integer commission between 5 and 50 in Django
admin and approve the submission. Use the campaign link in admin and sign
**Approve on Sepolia** with the factory administrator wallet. The startup can
then use **Pay fee and deploy** from its own wallet. This single transaction
creates the campaign and transfers 0.0001 test ETH to Sahliz Treasury. The
startup then selects **Publish campaign**. Django lists the campaign after
verifying the on-chain deployment and approved terms.

When a successful campaign closes, the issuer's withdrawal splits sales
proceeds between the issuer and Sahliz Treasury at the approved rate. If a
campaign misses its goal, contributors can reclaim their full contributions.
The registration fee is charged on deployment and is separate from refunds.
Existing campaigns continue using the original factory.
