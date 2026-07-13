# LastScanned Analyzer za Enigma2 (Premium Edition)
![Version](https://img.shields.io/badge/version-v1.4-blue.svg)
<!-- Primer kako da ubaciš screenshot-ove -->
![Screenshot aplikacije](/Screeshot/screenshot1.jpg)
![Prikaz liste](/Screeshot/screenshot2.jpg)

*For the **English** version, scroll down.*

**LastScanned Analyzer** je koristan i izuzetno napredan Enigma2 plugin dizajniran da olakša posao analize, pregleda i prebacivanja novo-skeniranih kanala (Last Scanned). 

Ovaj plugin automatski analizira vaš fajl `userbouquet.LastScanned.tv` i upoređuje ga sa ostalim vašim korisničkim buketima. Svaki kanal koji ranije niste imali u listama automatski dobija status `[NEW]`, kao i oznaku kvaliteta (`[HD]`, `[4K]`, `[Radio]`).



## Premium Funkcije

Dizajniran je u modernom "Dark" HD interfejsu (1280x720) za maksimalnu čitljivost na TV-u, a nudi napredne funkcije grupisanja i pregleda:

- **INFO / EPG Dugme:** Prikazuje logotip kanala (Picon) i detaljne informacije o transponderu (Satelit, Frekvencija, Polarizacija, Symbol Rate), kao i osnovne podatke (Rezoluciju, Provajdera). Tako tačno znate odakle je taj kanal došao!
- **MENU Dugme (Opcije):** Otvara meni iz koga možete izabrati "Scan Channels" (za brzo pokretanje Enigma2 skeniranja kanala) ili "Check for Updates" (za manuelnu proveru i preuzimanje novijih verzija plugina).
- **Zeleno Dugme (Obeležavanje / Multi-Select):** Ne morate više da prebacujete kanal po kanal. Pritiskom na zeleno dugme stavljate zvezdicu `[ * ]` na kanale koje želite da zadržite.
- **Plavo Dugme (Kopiraj SVE nove):** Svi kanali sa oznakom `[NEW]` (ili oni koje ste obeležili zelenim dugmetom) se prebacuju u buket. Možete izabrati postojeći buket iz liste ili kliknuti na **"+ Create New Bouquet"** da direktno na ekranu ukucate ime i napravite potpuno novi buket! Najbolja opcija za masovno sortiranje.
- **Žuto Dugme (Samo NOVI):** Brzi filter. Jednim klikom sakriva sve stare kanale i na ekranu ostavlja isključivo `[NEW]` kanale. Ponovni pritisak prikazuje sve kanale.
- **Crveno Dugme:** Izlaz iz aplikacije.

> Sve izmene se primenjuju momentalno, a plugin komunicira sa Enigma2 sistemom (`reloadBouquets`), pa nije potrebno naknadno restartovati risiver nakon prebacivanja kanala.

## Instalacija

Možete instalirati plugin direktno na vaš risiver preko Putty/Telnet-a jednostavnom komandom:

```bash
wget -qO- https://raw.githubusercontent.com/andrejicd/Last-Scanned-Analyzer/refs/heads/main/installer.sh | sh
```

---

# LastScanned Analyzer for Enigma2 (Premium Edition)
![Version](https://img.shields.io/badge/version-v1.4-blue.svg)

**LastScanned Analyzer** is a powerful and advanced Enigma2 plugin designed to make analyzing, reviewing, and copying newly scanned channels (Last Scanned) incredibly easy.

This plugin automatically analyzes your `userbouquet.LastScanned.tv` file and cross-references it with your existing custom bouquets. Any channel that you didn't previously have in your lists automatically receives a `[NEW]` tag, along with an integrated quality badge (`[HD]`, `[4K]`, `[Radio]`).

## Premium Features

Designed with a modern "Dark" HD interface (1280x720) for maximum readability on your TV, it offers advanced grouping and preview features:

- **INFO / EPG Button:** Displays the channel logo (Picon) and detailed transponder information (Satellite Position, Frequency, Polarization, Symbol Rate) along with standard details. You know exactly what you are copying!
- **MENU Button (Options):** Opens the options menu where you can choose "Scan Channels" (to instantly launch the built-in Enigma2 channel scanner) or "Check for Updates" (to manually check for and install new plugin updates).
- **Green Button (Select / Multi-Select):** You no longer have to move channels one by one. Pressing the green button adds a star `[ * ]` to the channels you want to keep.
- **Blue Button (Copy NEW):** All channels marked as `[NEW]` (or those selected with the green button) are transferred to a bouquet. You can choose an existing bouquet from the list or select **"+ Create New Bouquet"** to type a name using the on-screen keyboard and create a brand new bouquet instantly!
- **Yellow Button (New Only):** A quick toggle filter. A single click hides all old channels, leaving only the `[NEW]` channels on screen. Pressing it again shows all channels.
- **Red Button:** Exit application.

> All changes are applied instantly. The plugin communicates directly with the Enigma2 core (`reloadBouquets`), so you don't need to restart your receiver after copying channels.

## Installation

You can easily install the plugin directly on your receiver via Putty/Telnet using a simple command:

```bash
wget -qO- https://raw.githubusercontent.com/andrejicd/Last-Scanned-Analyzer/refs/heads/main/installer.sh | sh
```

## Compatibility
The plugin is written to support both older systems (Python 2) and modern ones (Python 3).
It has been tested on OpenATV and other popular Enigma2 images.

## Changelog / Release Notes

### v1.4
- **Auto-Update System:** Added automatic background checks for new versions on startup.
- **Manual Update:** Replaced the direct Scan button with an Options menu offering a "Check for Updates" feature.
- **In-App Installer:** You can now update the plugin with a single click directly from the UI without using Telnet.
- **Fix:** Implemented accurate semantic version comparison to prevent false update prompts.

### v1.3
- **Premium UI:** Redesigned modern "Dark" HD interface.
- **Picon & TP Info:** Pressing `INFO` now displays the channel's Picon and detailed transponder data.
- **Quick Scan:** Integrated the `MENU` button to launch the Enigma2 scanner and auto-refresh the list upon return.
- **Multi-Select:** Use the `Green` button to tag multiple channels `[ * ]` for copying.
- **Smart Filter:** Use the `Yellow` button to instantly hide old channels and see only the `[NEW]` ones.
- **Bouquet Creator:** Use the `Blue` button to copy selected/new channels, and even create a brand new bouquet using the virtual keyboard.
