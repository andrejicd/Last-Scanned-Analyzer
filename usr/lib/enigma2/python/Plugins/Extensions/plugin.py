#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.Label import Label
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
import os
import glob
import io

try:
    from enigma import eDVBDB, eServiceReference
except ImportError:
    pass

class LastScannedAnalyzerScreen(Screen):
    skin = """
        <screen name="LastScannedAnalyzerScreen" position="center,center" size="1280,720" flags="wfNoBorder" backgroundColor="transparent">
            <!-- Glavna tamna pozadina (skoro skroz crna, A=10) -->
            <eLabel position="0,0" size="1280,720" backgroundColor="#10000000" zPosition="-1" />
            
            <!-- Moderno Zaglavlje (Header) -->
            <eLabel position="0,0" size="1280,60" backgroundColor="#000e355c" zPosition="0" />
            <eLabel text="Analiza LastScanned Kanala" position="30,10" size="1000,40" font="Regular;32" foregroundColor="#ffffff" backgroundColor="#000e355c" transparent="1" halign="left" valign="center" zPosition="1" />
            <widget name="key_info" position="1000,15" size="250,30" font="Regular;22" foregroundColor="#cccccc" backgroundColor="#000e355c" transparent="1" halign="right" valign="center" zPosition="1" />
            
            <!-- Okvir za listu (potpuno crna, A=00 za maskimalan kontrast) -->
            <eLabel position="30,80" size="1220,550" backgroundColor="#00000000" zPosition="0" />
            <widget name="list" position="40,90" size="1200,530" itemHeight="35" font="Regular;26" foregroundColor="#ffffff" scrollbarMode="showOnDemand" transparent="1" backgroundColor="#00000000" zPosition="1" />
            
            <!-- Linija razdvajanja na dnu (svetlo siva) -->
            <eLabel position="30,650" size="1220,2" backgroundColor="#00666666" zPosition="0" />
            
            <!-- Flat Dugmici u boji -->
            <!-- Crveno dugme -->
            <eLabel position="40,665" size="275,45" backgroundColor="#00e74c3c" zPosition="0" />
            <widget name="key_red" position="40,665" size="275,45" font="Regular;24" foregroundColor="#000000" backgroundColor="#00e74c3c" transparent="1" halign="center" valign="center" zPosition="1" />
            
            <!-- Zeleno dugme -->
            <eLabel position="345,665" size="275,45" backgroundColor="#002ecc71" zPosition="0" />
            <widget name="key_green" position="345,665" size="275,45" font="Regular;24" foregroundColor="#000000" backgroundColor="#002ecc71" transparent="1" halign="center" valign="center" zPosition="1" />
            
            <!-- Zuto dugme -->
            <eLabel position="650,665" size="275,45" backgroundColor="#00f1c40f" zPosition="0" />
            <widget name="key_yellow" position="650,665" size="275,45" font="Regular;24" foregroundColor="#000000" backgroundColor="#00f1c40f" transparent="1" halign="center" valign="center" zPosition="1" />
            
            <!-- Plavo dugme -->
            <eLabel position="955,665" size="275,45" backgroundColor="#003498db" zPosition="0" />
            <widget name="key_blue" position="955,665" size="275,45" font="Regular;24" foregroundColor="#000000" backgroundColor="#003498db" transparent="1" halign="center" valign="center" zPosition="1" />
        </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        
        self.show_only_new = False
        
        self["key_red"] = Label("Samo NOVI")
        self["key_green"] = Label("Kopiraj jedan")
        self["key_yellow"] = Label("Obriši")
        self["key_blue"] = Label("Kopiraj NOVE")
        self["key_info"] = Label("INFO / OK")
        
        self.list = []
        self.channel_data = []  # Cuvamo (ref, ime, provajder, is_new)
        self["list"] = MenuList([])
        
        self["ColorActions"] = ActionMap(["ColorActions"],
        {
            "red": self.red_pressed,
            "green": self.green_pressed,
            "yellow": self.yellow_pressed,
            "blue": self.blue_pressed,
        }, 3)
        
        self["SetupActions"] = ActionMap(["SetupActions", "EPGSelectActions"],
        {
            "cancel": self.close,
            "ok": self.ok_pressed,
            "info": self.info_pressed,
            "epg": self.info_pressed,
        }, -1)
        
        self.onLayoutFinish.append(self.load_channels)

    def get_service_tuple(self, ref_string):
        parts = ref_string.split(':')
        if len(parts) >= 7:
            try:
                s_id = int(parts[3], 16)
                s_tsid = int(parts[4], 16)
                s_onid = int(parts[5], 16)
                s_ns = int(parts[6], 16)
                return (s_id, s_ns, s_tsid, s_onid)
            except ValueError:
                pass
        return None

    def parse_lamedb(self, lamedb_path):
        services = {}
        if not os.path.exists(lamedb_path):
            return services
            
        with io.open(lamedb_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.read().splitlines()
            
        in_services = False
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line == "services":
                in_services = True
                i += 1
                continue
            if line == "end" and in_services:
                break
                
            if in_services and ':' in line:
                parts = line.split(':')
                if len(parts) >= 4:
                    try:
                        s_id = int(parts[0], 16)
                        s_ns = int(parts[1], 16)
                        s_tsid = int(parts[2], 16)
                        s_onid = int(parts[3], 16)
                        
                        key = (s_id, s_ns, s_tsid, s_onid)
                        
                        name = "Nepoznato"
                        provider = "Nepoznat"
                        
                        if i + 1 < len(lines):
                            name = lines[i+1]
                        
                        if i + 2 < len(lines) and lines[i+2].startswith("p:"):
                            prov_line = lines[i+2]
                            p_parts = prov_line.split(',')
                            for p in p_parts:
                                if p.startswith('p:'):
                                    provider = p[2:]
                                    break
                                    
                        services[key] = (name, provider)
                        i += 2
                        continue
                    except ValueError:
                        pass
            i += 1
            
        return services

    def load_channels(self):
        base_dir = "/etc/enigma2"
        last_scanned_file = os.path.join(base_dir, "userbouquet.LastScanned.tv")
        lamedb_file = os.path.join(base_dir, "lamedb")
        
        self.list = []
        self.channel_data = []
        
        if not os.path.exists(last_scanned_file):
            self.list.append("GRESKA: userbouquet.LastScanned.tv nije pronadjen!")
            self.channel_data.append(None)
            self["list"].setList(self.list)
            return

        lamedb_info = self.parse_lamedb(lamedb_file)
        existing_services = set()
        
        bouquet_files = glob.glob(os.path.join(base_dir, "userbouquet.*.tv")) + \
                        glob.glob(os.path.join(base_dir, "userbouquet.*.radio"))
        
        for b_file in bouquet_files:
            if os.path.basename(b_file) == "userbouquet.LastScanned.tv":
                continue
            try:
                with io.open(b_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if line.startswith("#SERVICE"):
                            parts = line.split()
                            if len(parts) > 1:
                                ref = parts[1]
                            else:
                                ref = line.strip()[9:]
                            key = self.get_service_tuple(ref)
                            if key:
                                existing_services.add(key)
            except Exception:
                pass
                            
        ukupno = 0
        novi = 0
        
        self.list.append("")
        self.list.append("")
        self.channel_data.append(None)
        self.channel_data.append(None)
        
        try:
            with io.open(last_scanned_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if line.startswith("#SERVICE"):
                        ukupno += 1
                        parts = line.split()
                        if len(parts) > 1:
                            ref = parts[1]
                        else:
                            ref = line.strip()[9:]
                            
                        key = self.get_service_tuple(ref)
                        is_new = key not in existing_services if key else False
                        
                        info = lamedb_info.get(key, ("Nepoznato ime", "Nepoznat")) if key else ("Greska ref", "Nepoznat")
                        channel_name = info[0]
                        provider = info[1]
                        
                        if is_new:
                            status_text = "[NOVI]"
                            novi += 1
                        else:
                            status_text = "       "
                            
                        if self.show_only_new and not is_new:
                            continue
                            
                        display_text = "%s  %s" % (status_text, channel_name)
                        self.list.append(display_text)
                        self.channel_data.append((ref, channel_name, provider, is_new))
        except Exception as e:
            self.list.append("Greska pri citanju LastScanned.tv: " + str(e))
            self.channel_data.append(None)
            
        self.list[0] = "UKUPNO KANALA: %d  |  PRONADJENO NOVIH: %d" % (ukupno, novi)
        self.list[1] = "-" * 80
        
        self["list"].setList(self.list)
        self["list"].moveToIndex(0)

    def ok_pressed(self):
        idx = self["list"].getSelectedIndex()
        if idx < 2 or not self.channel_data[idx]:
            return
            
        ref = self.channel_data[idx][0]
        try:
            self.session.nav.playService(eServiceReference(ref))
        except Exception:
            pass

    def red_pressed(self):
        self.show_only_new = not self.show_only_new
        if self.show_only_new:
            self["key_red"].setText("Prikaži SVE")
        else:
            self["key_red"].setText("Samo NOVI")
        self.load_channels()

    def info_pressed(self):
        idx = self["list"].getSelectedIndex()
        if idx < 2 or not self.channel_data[idx]:
            return
            
        ref, name, provider, is_new = self.channel_data[idx]
        msg = "Ime kanala: %s\nProvajder: %s\n\nReferenca: %s" % (name, provider, ref)
        self.session.open(MessageBox, msg, MessageBox.TYPE_INFO)

    def yellow_pressed(self):
        idx = self["list"].getSelectedIndex()
        if idx < 2 or not self.channel_data[idx]:
            return
            
        ref, name, _, _ = self.channel_data[idx]
        base_dir = "/etc/enigma2"
        last_scanned_file = os.path.join(base_dir, "userbouquet.LastScanned.tv")
        
        try:
            with io.open(last_scanned_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            with io.open(last_scanned_file, 'w', encoding='utf-8') as f:
                for line in lines:
                    if line.startswith("#SERVICE") and ref in line:
                        continue 
                    f.write(line)
                    
            try:
                eDVBDB.getInstance().reloadBouquets()
            except Exception:
                pass
                
            self.load_channels() 
            self.session.open(MessageBox, "Kanal '%s' obrisan iz Last Scanned!" % name, MessageBox.TYPE_INFO, timeout=2)
            
        except Exception as e:
            self.session.open(MessageBox, "Greska pri brisanju: " + str(e), MessageBox.TYPE_ERROR)

    def green_pressed(self):
        idx = self["list"].getSelectedIndex()
        if idx < 2 or not self.channel_data[idx]:
            return
        
        self.selected_refs = [(self.channel_data[idx][0], self.channel_data[idx][1])]
        self.show_bouquet_selection(title_suffix="za '%s'" % self.selected_refs[0][1])

    def blue_pressed(self):
        self.selected_refs = []
        for data in self.channel_data:
            if data and data[3]: 
                self.selected_refs.append((data[0], data[1]))
                
        if not self.selected_refs:
            self.session.open(MessageBox, "Nema novih kanala za prebacivanje!", MessageBox.TYPE_INFO, timeout=3)
            return
            
        self.show_bouquet_selection(title_suffix="za %d NOVIH kanala" % len(self.selected_refs))

    def show_bouquet_selection(self, title_suffix=""):
        base_dir = "/etc/enigma2"
        bouquets_tv = os.path.join(base_dir, "bouquets.tv")
        choices = []
        
        if os.path.exists(bouquets_tv):
            with io.open(bouquets_tv, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.startswith("#SERVICE") and "FROM BOUQUET" in line:
                        try:
                            filename = line.split('"')[1]
                            bq_path = os.path.join(base_dir, filename)
                            if os.path.exists(bq_path):
                                bq_name = filename
                                with io.open(bq_path, "r", encoding="utf-8", errors="ignore") as bf:
                                    first_line = bf.readline()
                                    if first_line.startswith("#NAME"):
                                        bq_name = first_line[6:].strip()
                                choices.append((bq_name, filename))
                        except:
                            pass
                            
        if not choices:
            self.session.open(MessageBox, "Nijedan korisnički buket nije pronađen!", MessageBox.TYPE_ERROR)
            return
            
        self.session.openWithCallback(self.bouquet_selected, ChoiceBox, title="Izaberi buket " + title_suffix, list=choices)

    def bouquet_selected(self, choice):
        if choice and hasattr(self, 'selected_refs') and self.selected_refs:
            target_filename = choice[1]
            target_path = os.path.join("/etc/enigma2", target_filename)
            
            try:
                with io.open(target_path, "a", encoding="utf-8") as f:
                    for ref, name in self.selected_refs:
                        f.write(u"\n#SERVICE " + ref)
                
                try:
                    eDVBDB.getInstance().reloadBouquets()
                except Exception:
                    pass
                
                msg = "Uspesno dodato %d kanala u buket:\n%s" % (len(self.selected_refs), choice[0])
                self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, timeout=3)
                
                self.load_channels()
                
            except Exception as e:
                self.session.open(MessageBox, "Greška prilikom upisa: " + str(e), MessageBox.TYPE_ERROR)

def main(session, **kwargs):
    session.open(LastScannedAnalyzerScreen)

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="LastScanned Analyzer", 
            description="Analiziraj i sortiraj Last Scanned kanale", 
            where=PluginDescriptor.WHERE_PLUGINMENU, 
            icon="plugin.png",
            fnc=main
        )
    ]
