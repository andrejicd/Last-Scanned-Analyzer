# LastScanned Analyzer za Enigma2

**LastScanned Analyzer** je koristan Enigma2 plugin dizajniran da olakša posao analize, čišćenja i prebacivanja novo-skeniranih kanala (Last Scanned). Pomaže vam da ne morate ručno da listate hiljade skeniranih kanala tražeći šta je zapravo novo dodato.

Ovaj plugin automatski analizira vaš fajl `userbouquet.LastScanned.tv` i upoređuje ga sa ostalim vašim korisničkim buketima. Svaki kanal koji ranije niste imali u listama automatski dobija status `[NOVI]`, što vam omogućava lako grupisanje.

![Screenshot](link_do_slike_na_githubu_ili_imgur.png)

## Glavne Funkcije

Dizajniran je u modernom "Dark" HD interfejsu za maksimanu čitljivost na TV-u.

- **OK Dugme (Zapping):** Pritisnite na bilo koji kanal iz liste da ga TV pusti u pozadini. Na taj način vidite program kanala pre nego što odlučite gde ga smeštate.
- **INFO / EPG Dugme:** Prikazuje prozor sa stvarnim imenom kanala, provajderom (pročitanim direktno iz `lamedb`) i servisnom referencom.
- **Crveno Dugme:** Izlaz iz aplikacije.
- **Zeleno Dugme (Kopiraj kanal):** Dodaje selektovani kanal u korisnički buket po vašem izboru.
- **Žuto Dugme (Samo NOVI):** Brzi filter. Jednim klikom sakriva sve stare kanale i na ekranu ostavlja isključivo `[NOVI]` kanale. Ponovni pritisak prikazuje sve kanale.
- **Plavo Dugme (Kopiraj SVE nove):** Svi kanali sa oznakom `[NOVI]` se istog trenutka prebacuju u buket koji izaberete. Najbolja opcija za masovno sortiranje!

> Sve izmene se primenjuju momentalno, a plugin komunicira sa Enigma2 sistemom (`reloadBouquets`), pa nije potrebno naknadno restartovati risiver nakon prebacivanja kanala.

## Instalacija

Možete instalirati plugin direktno na vaš risiver preko Putty/Telnet-a komandom ispod:

```bash
wget -qO- https://raw.githubusercontent.com/andrejicd/Last-Scanned-Analyzer/refs/heads/main/installer.sh | sh
```

## Kompatibilnost
Plugin je napisan tako da podržava i starije sisteme (Python 2) i najmodernije (Python 3).
Testiran na OpenATV i drugim popularnim Image-ima.
