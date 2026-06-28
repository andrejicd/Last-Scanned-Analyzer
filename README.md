# LastScanned Analyzer za Enigma2 (Premium Edition)

**LastScanned Analyzer** je koristan i izuzetno napredan Enigma2 plugin dizajniran da olakša posao analize, pregleda i prebacivanja novo-skeniranih kanala (Last Scanned). 

Ovaj plugin automatski analizira vaš fajl `userbouquet.LastScanned.tv` i upoređuje ga sa ostalim vašim korisničkim buketima. Svaki kanal koji ranije niste imali u listama automatski dobija status `[NOVI]`, kao i oznaku kvaliteta (`[HD]`, `[4K]`, `[Radio]`).

![Screenshot](link_do_slike_na_githubu_ili_imgur.png)

## Premium Funkcije

Dizajniran je u modernom "Dark" HD interfejsu (1280x720) za maksimalnu čitljivost na TV-u, a nudi napredne funkcije grupisanja i pregleda:

- **INFO / EPG Dugme:** Prikazuje detaljne podatke o selektovanom kanalu sa desne strane ekrana (Rezolucija, Provajder i Referenca). Tako tačno znate šta prebacujete!
- **Zeleno Dugme (Obeležavanje / Multi-Select):** Ne morate više da prebacujete kanal po kanal. Pritiskom na zeleno dugme stavljate kvačicu `[ * ]` na kanale koje želite da zadržite.
- **Plavo Dugme (Kopiraj SVE nove):** Svi kanali sa oznakom `[NOVI]` se istog trenutka prebacuju u buket koji izaberete. Najbolja opcija za masovno sortiranje! (Ukoliko ste zelenim dugmetom prethodno obeležili neke kanale, plavo dugme će prebaciti samo te obeležene).
- **Žuto Dugme (Samo NOVI):** Brzi filter. Jednim klikom sakriva sve stare kanale i na ekranu ostavlja isključivo `[NOVI]` kanale. Ponovni pritisak prikazuje sve kanale.
- **Crveno Dugme:** Izlaz iz aplikacije.

> Sve izmene se primenjuju momentalno, a plugin komunicira sa Enigma2 sistemom (`reloadBouquets`), pa nije potrebno naknadno restartovati risiver nakon prebacivanja kanala.

## Instalacija

Možete instalirati plugin direktno na vaš risiver preko Putty/Telnet-a jednostavnom komandom:

```bash
wget -qO- https://raw.githubusercontent.com/andrejicd/Last-Scanned-Analyzer/refs/heads/main/installer.sh | sh
```

## Kompatibilnost
Plugin je napisan tako da podržava i starije sisteme (Python 2) i najmodernije (Python 3).
Testiran je na OpenATV i drugim popularnim "image"-ima za Enigma2 operativni sistem.
