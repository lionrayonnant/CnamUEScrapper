from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json

ue_results = {}

url = "https://formation.cnam.fr/servlet/com.jsbsoft.jtf.core.SG?EXT=cnam&PROC=RECHERCHE_FORMATION&ACTION=RECHERCHER&RF=&RH=&ID_REQ=1750526853551&motcle-AUTO=ue&metier-AUTO=&rechercherUE=true&region=&centre=&equipePedagogique=&departementEnseignement=#RESULTAT"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url)

    page.wait_for_selector("table#resultatSelecteur tbody", timeout=15000)

    while True:
        tbody = page.query_selector("table#resultatSelecteur tbody")
        old_html = tbody.inner_html()

        soup = BeautifulSoup(old_html, "html.parser")

        for a in soup.select("td.ligne-resultat-intitule a"):
            href = a.get("href", "")
            if "CODE=" in href:
                code = href.split("CODE=")[-1].split("&")[0]
                title = a.get_text(strip=True).replace("\xa0", " ")
                ue_results[code] = title

        next_btn = page.query_selector("#resultatSelecteur_next")
        if not next_btn:
            print("Bouton 'next' introuvable, fin de la pagination.")
            break

        classes = next_btn.get_attribute("class") or ""
        if "ui-state-disabled" in classes:
            print("Dernière page atteinte.")
            break

        next_btn.click()

        try:
            page.wait_for_function(
                """
                (old_html) => {
                    const tbody = document.querySelector('table#resultatSelecteur tbody');
                    return tbody && tbody.innerHTML !== old_html;
                }
                """,
                arg=old_html,
                timeout=15000
            )
        except Exception as e:
            print(f"Timeout ou erreur lors de l'attente du changement : {e}")
            break

    browser.close()

with open("ue_results.json", "w", encoding="utf-8") as f:
    json.dump(ue_results, f, ensure_ascii=False, indent=4)

print(f"{len(ue_results)} UEs extraites et sauvegardées dans 'ue_results.json'")
