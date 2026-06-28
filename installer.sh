#!/bin/sh
echo "========================================================="
echo " Instalacija LastScannedAnalyzer plugina"
echo "========================================================="

# Podesite vase github podatke. Ako je repozitorijum javan ovo radi automatski.
GITHUB_USER="andrejicd"
REPO_NAME="Last-Scanned-Analyzer"
BRANCH="main"

URL="https://github.com/${GITHUB_USER}/${REPO_NAME}/archive/refs/heads/${BRANCH}.zip"
TMP_DIR="/tmp/lastscanned_tmp"
PLUGIN_DIR="/usr/lib/enigma2/python/Plugins/Extensions/LastScannedAnalyzer"

mkdir -p $TMP_DIR
echo "-> Preuzimanje plugina sa Github-a..."
wget -qO $TMP_DIR/plugin.zip $URL

if [ -f $TMP_DIR/plugin.zip ]; then
    echo "-> Raspakivanje arhive..."
    unzip -qo $TMP_DIR/plugin.zip -d $TMP_DIR
    
    echo "-> Kopiranje fajlova na pravo mesto..."
    mkdir -p $PLUGIN_DIR
    
    # Radi bez obzira da li je sve spakovano direktno ili u root folderu na Githubu
    cp -rf $TMP_DIR/*${BRANCH}/* $PLUGIN_DIR/ 2>/dev/null
    
    # Cistimo fajlove koji Enigmi nisu potrebni za sam rad
    rm -f $PLUGIN_DIR/installer.sh
    rm -f $PLUGIN_DIR/README.md
    
    echo "-> Brisanje privremenih fajlova..."
    rm -rf $TMP_DIR
    
    echo "========================================================="
    echo " Instalacija potpuno uspesna!"
    echo " GUI ce se restartovati za 3 sekunde..."
    echo "========================================================="
    sleep 3
    killall -9 enigma2
else
    echo "========================================================="
    echo " GRESKA! Nije moguće preuzeti fajl."
    echo " Uverite se da ste ispravno uneli GITHUB_USER i REPO_NAME!"
    echo "========================================================="
    rm -rf $TMP_DIR
fi
exit 0
