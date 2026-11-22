# Sahliz Launchpad

Sahliz Launchpad helps startups create crowdfunding campaigns and mint ERC-20
tokens on Ethereum Sepolia. Startups set a funding goal, token price, and supply.
After administrator approval, the startup deploys the campaign through MetaMask.
Contributors use test ETH to participate, then claim tokens if the goal is met
or request a refund if the campaign falls short.

Built with Django, Solidity, and ethers.js. The interface defaults to English
and offers French, Arabic with right-to-left layout, and light and dark themes.

## Démarrer en local (PowerShell)

Pré-requis de développement : Python 3.12 ou 3.13. Node.js est nécessaire
pour recompiler ou tester les contrats.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DEBUG = "1"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Ouvrir http://127.0.0.1:8000/. Sous Linux, utiliser `python3 -m venv .venv`,
`.venv/bin/python` et `export DEBUG=1`.

## Mise à jour du catalogue Startups

Pour mettre à jour une installation existante, copier les fichiers du ZIP dans le dossier
contenant `manage.py`. L'archive ne contient ni base SQLite ni environnement virtuel.
Arrêter le serveur, puis exécuter dans PowerShell avec l'environnement activé :

```powershell
$env:DEBUG = "1"
python manage.py migrate
python manage.py seed_startups
python manage.py runserver
```

Lorsque les comptes du premier catalogue existent, la commande réutilise leurs deux
adresses publiques pour les quatre startups et masque les deux anciennes campagnes.
Sur une installation vierge, passer deux ou quatre adresses publiques distinctes dans
l'ordre AtlasAI, GreenBox, AquaNorth, MedRoute. Avec deux adresses, AtlasAI et AquaNorth
partagent la première, et GreenBox et MedRoute partagent la seconde. Réexécuter la commande
conserve les campagnes et les portefeuilles déjà configurés.

## Parcours de contribution sur Sepolia

1. Alimenter les portefeuilles émetteurs utilisés et le portefeuille participant en ETH de test.
2. Sur `/installation/`, se connecter en administrateur et déployer la factory si nécessaire.
   Copier son adresse publique, définir `$env:FACTORY_ADDRESS = "0x..."` dans le
   terminal et redémarrer Django. Une factory déjà déployée peut être réutilisée.
3. Pour AtlasAI et GreenBox, activer les connexions avec `python manage.py changepassword atlas-ai`
   et `python manage.py changepassword greenbox-ventures`. Chaque société se connecte et
   déploie sa levée avec le portefeuille qui lui est associé. L’échéance est de quinze minutes.
4. Avec un portefeuille participant, contribuer pour **100 ATLS** (0,001 ETH de test,
   objectif atteint) et pour **10 GBX** (0,0001 ETH de test, objectif non atteint).
5. Après les échéances, actualiser les pages pour récupérer 100 ATLS et demander le remboursement
   GreenBox. L’émetteur d’AtlasAI peut retirer le financement. Les transactions sont vérifiables
   sur Etherscan Sepolia.

Les deux autres émetteurs utilisent les comptes Django `aquanorth` et `medroute`.

Pour une nouvelle campagne, le compte société la soumet depuis son espace
et l'administrateur l'approuve dans `/admin/`. La société la déploie
ensuite. Un contrat est lié à une référence de campagne et au portefeuille
public attribué à la société.

## Vérification

```text
npm ci
npm run compile
npm test
python manage.py test --settings=launchpad.test_settings
```

Le test Ganache déploie les contrats de deux émetteurs, avance l'horloge
et vérifie retrait, livraison ERC-20 et remboursement. Les tests Django
vérifient catalogue, approbation et séparation entre les sociétés.

## GitHub et publication

### GitHub et Render

1. Décompresser le ZIP et envoyer son contenu à la racine du dépôt GitHub.
2. Dans Render, créer un **Blueprint** relié à ce dépôt. Le fichier `render.yaml`
   configure le serveur Django, les migrations et les fichiers statiques.
3. Renseigner `DATABASE_URL` avec la connexion PostgreSQL persistante et
   `FACTORY_ADDRESS` avec l’adresse de la factory Sepolia existante.
   La clé Django est générée par Render et le domaine Render est accepté automatiquement.
4. Ouvrir l’URL HTTPS indiquée par Render et vérifier le catalogue. Sur une base
   vide, importer les données voulues avant de partager le lien.

Pour conserver les campagnes déjà déployées, transférer les enregistrements Django
des entreprises et campagnes d’origine en conservant les UUID de campagne et les
adresses des émetteurs. Importer les comptes associés de façon privée, avec un
contenu limité aux comptes nécessaires. Garder les exports et la base hors de GitHub.
Vérifier au moins une campagne existante en comparant l’adresse du contrat avant
et après la migration. Pour une installation vierge, le paramètre facultatif
`DEMO_WALLETS` permet de créer le catalogue initial avec deux ou quatre adresses
publiques (AtlasAI, GreenBox, AquaNorth, MedRoute).

### Lien depuis un autre site

Pour un bouton sur le site existant, utiliser directement l’URL HTTPS affichée
par Render. Pour rediriger une URL entière, configurer chez l’hébergeur du site
source une redirection HTTP **302** vers cette URL. Une fois le lien vérifié,
le statut **301** peut être utilisé pour une redirection permanente. Pour une
campagne précise, utiliser son URL complète `/campagnes/<uuid>/`.
Copier l’URL finale dans Safari ou Chrome pour ajouter l’icône à l’écran
d’accueil. Pour contribuer, utiliser **Ouvrir dans MetaMask** sur la page de campagne.

Pour accéder à l’administration et lancer de nouvelles campagnes, exécuter
`python manage.py createsuperuser` une fois sur la base hébergée depuis un shell
Render compatible ou un terminal de confiance configuré avec l’URL externe de
la base. Définir ensuite les mots de passe des comptes des entreprises depuis
l’administration Django ou `manage.py changepassword`.

Le périmètre de cette version est le financement avec seuil, retrait ou
remboursement, sur réseau de test. Les tokens ne donnent droit à aucune action ni à aucun dividende.
