# Server (`/pyserver`)
Server en python avec module Flask

## Consignes d'utilisation (mode developpement)
1. Activer un environnement virtuel python si besoin
2. Installer les modules python dans `pyserver/requirements.txt`
3. Lancer l'application `py app.py`. Le server est accessible à `http://localhost:5000/`

## Déploiement
1. Activer l'environnement virtuel `source .venv/bin/activate`
2. Lancer le daemon `gunicorn -w 2 -b "0.0.0.0:8080" app:app --daemon`

# Client (`/spectro-cli`)
Client React avec TypeScript (NodeJS requis)
## Consignes d'utilisation (mode developpement)
1. Installer les packages avec `npm`
2. Lancer l'application `npm run dev`. Le client est accessible à `http://localhost:5173/`

## Déploiement
1. Générer le fichier de distribution `npm run build`
2. Supprimer l'ancien fichier `sudo rm -rf /var/www/spectro-cli/*`
3. Copier le nouveau fichier `sudo cp -r dist/* /var/www/spectro-cli/` 
4. Reinitiliaser nginx `sudo systemctl reload nginx`