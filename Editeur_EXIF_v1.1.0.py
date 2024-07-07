# *******************************************************
# Nom ......... : Editeur_EXIF_v1.1.0.py
# Rôle ........ : Application d'édition de métadonnées EXIF pour les images (sans cartes POIs)
# Auteur ...... : Maxim Khomenko
# Version ..... : V1.1.0 du 31/05/2024
# Licence ..... : Réalisé dans le cadre du cours de l'Architecture des Machines
# Usage ....... : Exécuter le script avec "streamlit run Editeur_EXIF_v1.1.0.py" pour démarrer l'application
# *******************************************************

import streamlit as st  # Importer la bibliothèque Streamlit pour créer des applications web interactives
from PIL import Image, ExifTags  # Importer le module Image de PIL (Pillow) pour manipuler les images et ExifTags pour accéder aux tags EXIF
from PIL.ExifTags import TAGS, GPSTAGS  # Importer les dictionnaires TAGS et GPSTAGS de PIL pour traduire les identifiants de tags EXIF en noms lisibles
import folium  # Importer la bibliothèque Folium pour créer des cartes interactives
from streamlit_folium import folium_static  # Importer la fonction folium_static de streamlit_folium pour afficher des cartes Folium dans une application Streamlit
import piexif  # Importer la bibliothèque piexif pour manipuler les métadonnées EXIF des images
import io  # Importer le module io pour travailler avec les flux de données en mémoire

# Dictionnaires pour traduire les valeurs EXIF en descriptions compréhensibles
options_orientation = {
    1: "Normal (0°)",
    3: "À l'envers (180°)",
    6: "Pivoté 90° CW",
    8: "Pivoté 90° CCW"
}

options_mesure = {
    0: "Inconnu",
    1: "Moyenne",
    2: "Moyenne pondérée au centre",
    3: "Spot",
    4: "Multi-spot",
    5: "Multi-segment",
    6: "Partielle"
}

options_exposition = {
    0: "Exposition automatique",
    1: "Exposition manuelle",
}

options_source_lumiere = {
    0: "Inconnue",
    1: "Lumière du jour",
    2: "Fluorescente",
    3: "Tungstène",
    4: "Flash",
    9: "Beau temps",
    10: "Temps nuageux",
    11: "Ombre",
    12: "Fluorescente lumière du jour",
    13: "Fluorescente blanc chaud",
    14: "Fluorescente blanc froid",
    15: "Fluorescente blanc",
    17: "Lumière standard A",
    18: "Lumière standard B",
    19: "Lumière standard C",
    20: "D55",
    21: "D65",
    22: "D75",
    255: "Autre"
}

options_detection = {
    1: "Méthode inconnue",
    2: "Capteur 1 puce couleur",
    3: "Capteur 2 puces couleur",
    4: "Capteur 3 puces couleur",
    5: "Capteur séquentiel couleur",
    7: "Capteur trilinear",
    8: "Capteur couleur trilinear",
}

# Fonction pour convertir des coordonnées en format EXIF
def convertir_en_coord_exif(valeur, ref):
    # Calcul des degrés, minutes et secondes à partir de la valeur absolue des coordonnées
    deg, min, sec = abs(valeur), (abs(valeur) * 60) % 60, (abs(valeur) * 3600) % 60
    # Retourne les coordonnées EXIF au format tuple (degrés, minutes, secondes) et la référence N/S/E/W
    return ((int(deg), 1), (int(min), 1), (int(sec * 100), 100)), \
           'N' if ref in ['lat', 'latitude'] and valeur >= 0 else \
           'S' if ref in ['lat', 'latitude'] else \
           'E' if valeur >= 0 else 'W'

# Fonction pour convertir des coordonnées EXIF en valeurs décimales
def convertir_de_coord_exif(coords, ref):
    # Convertir les degrés, minutes et secondes de format EXIF en valeurs décimales
    deg = coords[0][0] / coords[0][1]
    min = coords[1][0] / coords[1][1]
    sec = coords[2][0] / coords[2][1] / 100
    # Calculer la valeur décimale totale
    valeur = deg + (min / 60) + (sec / 3600)
    # Retourner la valeur, positive ou négative selon la référence (N, E, S, W)
    return valeur if ref in ['N', 'E'] else -valeur

# Fonction pour extraire les métadonnées EXIF d'une image
def obtenir_donnees_exif(image):
    donnees_exif = image._getexif()  # Utilise la méthode _getexif() pour obtenir les métadonnées EXIF de l'image
    if not donnees_exif:  # Vérifie si les métadonnées EXIF sont présentes
        return {}  # Si aucune métadonnée n'est trouvée, retourne un dictionnaire vide

    exif = {}  # Initialise un dictionnaire pour stocker les métadonnées EXIF avec des noms de tags lisibles
    for tag, value in donnees_exif.items():  # Parcourt chaque tag et sa valeur dans les métadonnées EXIF
        nom_tag = TAGS.get(tag, tag)  # Utilise la table de correspondance TAGS pour obtenir un nom lisible du tag. Si le tag n'est pas trouvé, utilise le tag lui-même
        exif[nom_tag] = value  # Ajoute le nom du tag et sa valeur au dictionnaire EXIF
    return exif  # Retourne le dictionnaire des métadonnées EXIF

# Interface utilisateur Streamlit
st.title("Éditeur de métadonnées EXIF")  # Titre de l'application Streamlit
fichier_charge = st.file_uploader("Choisissez une image...", type=["jpg", "jpeg"])  # Créer un widget pour uploader un fichier image

if fichier_charge is not None:  # Si un fichier est chargé
    image = Image.open(fichier_charge)  # Ouvrir l'image en utilisant PIL
    donnees_exif = obtenir_donnees_exif(image)  # Obtenir les données EXIF de l'image
    if not donnees_exif:  # Si aucune donnée EXIF n'est trouvée
        st.write("Pas de métadonnées EXIF trouvées dans l'image.")  # Afficher un message indiquant qu'aucune donnée EXIF n'est trouvée
    else:
        st.image(image, caption='Image chargée', use_column_width=True)  # Afficher l'image chargée
        st.write("**Métadonnées EXIF :**")  # Afficher un titre pour les métadonnées EXIF
        st.write(donnees_exif)  # Afficher les données EXIF

        exif_dict = piexif.load(image.info.get("exif", b""))  # Charger les métadonnées EXIF de l'image sous forme de dictionnaire
        
        # Vérifier et initialiser les sections nécessaires des données EXIF
        if "0th" not in exif_dict:
            exif_dict["0th"] = {}  # Initialiser la section "0th" si elle n'existe pas
        if "Exif" not in exif_dict:
            exif_dict["Exif"] = {}  # Initialiser la section "Exif" si elle n'existe pas
        if "GPS" not in exif_dict:
            exif_dict["GPS"] = {}  # Initialiser la section "GPS" si elle n'existe pas

        # Obtenir les valeurs EXIF actuelles ou définir des valeurs par défaut
        orientation_actuelle = exif_dict["0th"].get(piexif.ImageIFD.Orientation, 1)
        mesure_actuelle = exif_dict["Exif"].get(piexif.ExifIFD.MeteringMode, 0)
        exposition_actuelle = exif_dict["Exif"].get(piexif.ExifIFD.ExposureMode, 0)
        source_lumiere_actuelle = exif_dict["Exif"].get(piexif.ExifIFD.LightSource, 0)
        flash_actuel = exif_dict["Exif"].get(piexif.ExifIFD.Flash, 0)
        detection_actuelle = exif_dict["Exif"].get(piexif.ExifIFD.SensingMethod, 1)
        
        # Valider et ajuster les valeurs d'index si nécessaire
        orientation_actuelle = orientation_actuelle if orientation_actuelle in options_orientation else 1
        mesure_actuelle = mesure_actuelle if mesure_actuelle in options_mesure else 0
        exposition_actuelle = exposition_actuelle if exposition_actuelle in options_exposition else 0
        source_lumiere_actuelle = source_lumiere_actuelle if source_lumiere_actuelle in options_source_lumiere else 0
        flash_actuel = 0 if flash_actuel not in [0, 1] else flash_actuel
        detection_actuelle = detection_actuelle if detection_actuelle in options_detection else 1

        # Afficher le formulaire
        st.subheader("Modifier les métadonnées EXIF")

        # Champs de texte pour les métadonnées de base
        fabricant = st.text_input("Fabricant", value=exif_dict["0th"].get(piexif.ImageIFD.Make, b'').decode('utf-8'))
        modele = st.text_input("Modèle", value=exif_dict["0th"].get(piexif.ImageIFD.Model, b'').decode('utf-8'))
        orientation = st.selectbox("Orientation", options=list(options_orientation.keys()), format_func=lambda x: options_orientation[x], index=list(options_orientation.keys()).index(orientation_actuelle))
        date_heure = st.text_input("Date et Heure", value=exif_dict["0th"].get(piexif.ImageIFD.DateTime, b'').decode('utf-8'))
        logiciel = st.text_input("Logiciel", value=exif_dict["0th"].get(piexif.ImageIFD.Software, b'').decode('utf-8'))
        artiste = st.text_input("Artiste", value=exif_dict["0th"].get(piexif.ImageIFD.Artist, b'').decode('utf-8'))
        droits_auteur = st.text_input("Droits d'auteur", value=exif_dict["0th"].get(piexif.ImageIFD.Copyright, b'').decode('utf-8'))

        # Champs numériques pour les métadonnées EXIF techniques
        temps_exposition = st.number_input("Temps d'exposition (en secondes)", value=exif_dict["Exif"].get(piexif.ExifIFD.ExposureTime, (1, 1))[0] / exif_dict["Exif"].get(piexif.ExifIFD.ExposureTime, (1, 1))[1])
        ouverture = st.number_input("Ouverture (f/)", value=exif_dict["Exif"].get(piexif.ExifIFD.FNumber, (1, 1))[0] / exif_dict["Exif"].get(piexif.ExifIFD.FNumber, (1, 1))[1])
        iso = st.number_input("ISO", value=exif_dict["Exif"].get(piexif.ExifIFD.ISOSpeedRatings, 100))
        balance_blancs = st.selectbox("Balance des blancs", options=[0, 1], format_func=lambda x: "Auto" if x == 0 else "Manuelle", index=exif_dict["Exif"].get(piexif.ExifIFD.WhiteBalance, 0))
        longueur_focale = st.number_input("Longueur focale (mm)", value=exif_dict["Exif"].get(piexif.ExifIFD.FocalLength, (1, 1))[0] / exif_dict["Exif"].get(piexif.ExifIFD.FocalLength, (1, 1))[1])
        flash = st.selectbox("Flash", options=[0, 1], format_func=lambda x: "Pas de flash" if x == 0 else "Flash", index=flash_actuel)
        mesure = st.selectbox("Mode de mesure", options=list(options_mesure.keys()), format_func=lambda x: options_mesure[x], index=list(options_mesure.keys()).index(mesure_actuelle))
        exposition = st.selectbox("Mode d'exposition", options=list(options_exposition.keys()), format_func=lambda x: options_exposition[x], index=list(options_exposition.keys()).index(exposition_actuelle))
        source_lumiere = st.selectbox("Source lumineuse", options=list(options_source_lumiere.keys()), format_func=lambda x: options_source_lumiere[x], index=list(options_source_lumiere.keys()).index(source_lumiere_actuelle))
        detection = st.selectbox("Méthode de détection", options=list(options_detection.keys()), format_func=lambda x: options_detection[x], index=list(options_detection.keys()).index(detection_actuelle))
        lens_model = st.text_input("Modèle de l'objectif", value=exif_dict["Exif"].get(piexif.ExifIFD.LensModel, b'').decode('utf-8'))

        # Champs pour les métadonnées GPS
        gps_version_id = st.text_input("Version GPS", value=",".join(map(str, exif_dict["GPS"].get(piexif.GPSIFD.GPSVersionID, (2, 2, 0, 0)))))
        gps_altitude = st.number_input("Altitude GPS (m)", value=exif_dict["GPS"].get(piexif.GPSIFD.GPSAltitude, (0, 1))[0] / exif_dict["GPS"].get(piexif.GPSIFD.GPSAltitude, (0, 1))[1])
        gps_speed = st.number_input("Vitesse GPS (m/s)", value=exif_dict["GPS"].get(piexif.GPSIFD.GPSSpeed, (0, 1))[0] / exif_dict["GPS"].get(piexif.GPSIFD.GPSSpeed, (0, 1))[1])
        gps_img_direction = st.number_input("Direction de l'image GPS", value=exif_dict["GPS"].get(piexif.GPSIFD.GPSImgDirection, (0, 1))[0] / exif_dict["GPS"].get(piexif.GPSIFD.GPSImgDirection, (0, 1))[1])
        gps_date_stamp = st.text_input("Date GPS", value=exif_dict["GPS"].get(piexif.GPSIFD.GPSDateStamp, b'').decode('utf-8'))

        # Champs pour les coordonnées GPS
        lat = st.number_input("Latitude", value=convertir_de_coord_exif(exif_dict["GPS"].get(piexif.GPSIFD.GPSLatitude, ((0, 1), (0, 1), (0, 1))), exif_dict["GPS"].get(piexif.GPSIFD.GPSLatitudeRef, 'N')))
        lon = st.number_input("Longitude", value=convertir_de_coord_exif(exif_dict["GPS"].get(piexif.GPSIFD.GPSLongitude, ((0, 1), (0, 1), (0, 1))), exif_dict["GPS"].get(piexif.GPSIFD.GPSLongitudeRef, 'E')))

        if st.button("Sauvegarder les modifications"):
            # Mettre à jour les données EXIF avec les nouvelles valeurs
            exif_dict["0th"][piexif.ImageIFD.Make] = fabricant.encode('utf-8')
            exif_dict["0th"][piexif.ImageIFD.Model] = modele.encode('utf-8')
            exif_dict["0th"][piexif.ImageIFD.Orientation] = orientation
            exif_dict["0th"][piexif.ImageIFD.DateTime] = date_heure.encode('utf-8')
            exif_dict["0th"][piexif.ImageIFD.Software] = logiciel.encode('utf-8')
            exif_dict["0th"][piexif.ImageIFD.Artist] = artiste.encode('utf-8')
            exif_dict["0th"][piexif.ImageIFD.Copyright] = droits_auteur.encode('utf-8')

            exif_dict["Exif"][piexif.ExifIFD.ExposureTime] = (int(temps_exposition * 1000000), 1000000)
            exif_dict["Exif"][piexif.ExifIFD.FNumber] = (int(ouverture * 100), 100)
            exif_dict["Exif"][piexif.ExifIFD.ISOSpeedRatings] = int(iso)
            exif_dict["Exif"][piexif.ExifIFD.WhiteBalance] = balance_blancs
            exif_dict["Exif"][piexif.ExifIFD.FocalLength] = (int(longueur_focale * 100), 100)
            exif_dict["Exif"][piexif.ExifIFD.Flash] = flash
            exif_dict["Exif"][piexif.ExifIFD.MeteringMode] = mesure
            exif_dict["Exif"][piexif.ExifIFD.ExposureMode] = exposition
            exif_dict["Exif"][piexif.ExifIFD.LightSource] = source_lumiere
            exif_dict["Exif"][piexif.ExifIFD.SensingMethod] = int(detection)
            exif_dict["Exif"][piexif.ExifIFD.LensModel] = lens_model.encode('utf-8')

            exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = convertir_en_coord_exif(lat, 'lat')[0]
            exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = 'N' if lat >= 0 else 'S'
            exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = convertir_en_coord_exif(lon, 'lon')[0]
            exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = 'E' if lon >= 0 else 'W'
            exif_dict["GPS"][piexif.GPSIFD.GPSAltitude] = (int(gps_altitude * 100), 100)
            exif_dict["GPS"][piexif.GPSIFD.GPSSpeed] = (int(gps_speed * 100), 100)
            exif_dict["GPS"][piexif.GPSIFD.GPSImgDirection] = (int(gps_img_direction * 100), 100)
            exif_dict["GPS"][piexif.GPSIFD.GPSDateStamp] = gps_date_stamp.encode('utf-8')
            exif_dict["GPS"][piexif.GPSIFD.GPSVersionID] = tuple(map(int, gps_version_id.split(',')))

            # Sauvegarder l'image avec les nouvelles métadonnées
            exif_bytes = piexif.dump(exif_dict)
            with io.BytesIO() as output:
                image.save(output, format="jpeg", exif=exif_bytes)
                # Télécharger l'image modifiée
                st.download_button(
                    label="Télécharger l'image modifiée",
                    data=output.getvalue(),
                    file_name="modified_image.jpg",
                    mime="image/jpeg"
                )
            st.success("Les métadonnées ont été modifiées avec succès!")

        # Afficher la carte avec les coordonnées GPS modifiées
        st.subheader("Carte des coordonnées GPS")
        m = folium.Map(location=[lat, lon], zoom_start=15)
        folium.Marker([lat, lon], tooltip='Coordonnées GPS').add_to(m)
        folium_static(m)
