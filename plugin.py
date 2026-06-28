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
            
            <!-- Okvir za listu -->
            <eLabel position="30,80" size="700,550" backgroundColor="#00000000" zPosition="0" />
            <widget name="list" position="40,90" size="680,530" itemHeight="35" font="Regular;26" foregroundColor="#ffffff" scrollbarMode="showOnDemand" transparent="1" backgroundColor="#00000000" zPosition="1" />
            
            <!-- Informacije o Kanalu (desna strana umesto videa) -->
            <widget name="channel_info" position="760,150" size="480,400" font="Regular;26" foregroundColor="#cccccc" backgroundColor="#00000000" transparent="1" halign="center" valign="top" zPosition="1" />
            
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
        
        self["key_red"] = Label("Izlaz")
        self["key_green"] = Label("Obeleži / Poništi")
        self["key_yellow"] = Label("Samo NOVI")
        self["key_blue"] = Label("Kopiraj NOVE")
        self["key_info"] = Label("INFO / OK")
        
        self["channel_info"] = Label("Pritisnite OK za puštanje kanala")
        
        self.list = []
        self.channel_data = []  # Cuvamo (ref, ime, provajder, is_new, type)
        self.selected_refs = set()
        self["list"] = MenuList([])
        
        self["ColorActions"] = ActionMap(["ColorActions"],
        {
            "red": self.close,
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
                        
                        channel_type = 1
                        if len(parts) >= 5:
                            try:
                                channel_type = int(parts[4], 16) if parts[4].startswith('0x') else int(parts[4])
                            except Exception:
                                pass
                        
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
                                    
                        services[key] = (name, provider, channel_type)
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
                        
                        if self.show_only_new and not is_new:
                            continue
                            
                        # Default vrednosti
                        name = "Nepoznat Kanal"
                        provider = "Nepoznat Provajder"
                        # Čitamo pravi Service Type iz same reference (npr. 1:0:19:... -> tip je 19 u hexu)
                        c_type = 1
                        try:
                            ref_parts = ref.split(':')
                            if len(ref_parts) >= 3:
                                c_type = int(ref_parts[2], 16)
                        except:
                            pass
                            
                        if key and key in lamedb_info:
                            name, provider, _ = lamedb_info[key]
                            
                        # Formatiramo oznake
                        tags = ""
                        if is_new:
                            tags += "[NOVI] "
                        else:
                            tags += "        " # 8 razmaka da bi se poravnalo sa [NOVI] 
                        
                        if c_type == 2:
                            tags += "[Radio] "
                        elif c_type in [0x19, 25, 0x11, 17]:
                            tags += "[HD] "
                        elif c_type in [0x1f, 31]:
                            tags += "[4K] "
                            
                        sel_tag = "[ * ] " if ref in self.selected_refs else "      "
                            
                        display_text = "%s%s%s" % (sel_tag, tags, name)
                        
                        self.list.append(display_text)
                        self.channel_data.append((ref, name, provider, is_new, c_type))
                        if is_new:
                            novi += 1
        except Exception as e:
            self.list.append("Greska pri citanju LastScanned.tv: " + str(e))
            self.channel_data.append(None)
            
        self.list[0] = "UKUPNO KANALA: %d  |  PRONADJENO NOVIH: %d" % (ukupno, novi)
        self.list[1] = "-" * 80
        
        self["list"].setList(self.list)
        # Obrisali smo moveToIndex jer u MenuList klasi to ne postoji i izazivalo je krah aplikacije.
        if self["list"].instance is not None:
            self["list"].instance.moveSelectionTo(0)

    def ok_pressed(self):
        idx = self["list"].getSelectedIndex()
        if idx < 2 or not self.channel_data[idx]:
            return
            
        ref, name, provider, is_new, c_type = self.channel_data[idx]
        try:
            self.session.nav.playService(eServiceReference(ref))
            # Prikaz informacija u interfejsu
            res_tag = "Standard (SD)"
            if c_type in [0x19, 25, 0x11, 17]:
                res_tag = "High Definition (HD)"
            elif c_type in [0x1f, 31]:
                res_tag = "Ultra HD (4K)"
            elif c_type == 2:
                res_tag = "Radio Kanal"
                
            info_text = "Kanal: %s\nProvajder: %s\nKvalitet: %s\n\n%s" % (name, provider, res_tag, ref)
            self["channel_info"].setText(info_text)
        except Exception:
            pass

    def yellow_pressed(self):
        try:
            self.show_only_new = not self.show_only_new
            if self.show_only_new:
                self["key_yellow"].setText("Prikaži SVE")
            else:
                self["key_yellow"].setText("Samo NOVI")
            self.load_channels()
        except Exception as e:
            self.session.open(MessageBox, "Greška u filteru: " + str(e), MessageBox.TYPE_ERROR)

    def green_pressed(self):
        idx = self["list"].getSelectedIndex()
        if idx < 2 or not self.channel_data[idx]:
            return
            
        ref = self.channel_data[idx][0]
        if ref in self.selected_refs:
            self.selected_refs.remove(ref)
        else:
            self.selected_refs.add(ref)
            
        self.load_channels()
        if self["list"].instance is not None:
            self["list"].instance.moveSelectionTo(idx)

    def blue_pressed(self):
        to_copy = []
        for ch in self.channel_data:
            if not ch:
                continue
            if self.selected_refs:
                if ch[0] in self.selected_refs:
                    to_copy.append(ch)
            else:
                if ch[3]: # is_new
                    to_copy.append(ch)
                    
        if not to_copy:
            self.session.open(MessageBox, "Nema kanala za kopiranje!", MessageBox.TYPE_INFO)
            return
            
        try:
            naslov = "prebaciti OBELEŽENE kanale:" if self.selected_refs else "prebaciti SVE NOVE kanale:"
            self._channels_to_copy = to_copy
            self.session.openWithCallback(self.bouquet_chosen_multi, ChoiceBox, title="Izaberi buket gde zelis " + naslov, list=self.get_bouquets())
        except Exception as e:
            self.session.open(MessageBox, "Greska: " + str(e), MessageBox.TYPE_ERROR)

    def bouquet_chosen_multi(self, choice):
        if choice is None:
            return
            
        bq_file = choice[1]
        channels = getattr(self, '_channels_to_copy', [])
        
        try:
            existing_refs = set()
            if os.path.exists(bq_file):
                with io.open(bq_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if line.startswith("#SERVICE"):
                            p = line.split()
                            if len(p) > 1:
                                existing_refs.add(p[1])
            
            with io.open(bq_file, 'a', encoding='utf-8') as f:
                for ch in channels:
                    ref = ch[0]
                    if ref not in existing_refs:
                        f.write(u"\n#SERVICE %s\n" % ref)
                        
            try:
                eDVBDB.getInstance().reloadBouquets()
            except Exception:
                pass
                
            self.session.open(MessageBox, "Uspešno prebačeno %d kanala u izabrani buket!" % len(channels), MessageBox.TYPE_INFO)
            self.selected_refs.clear()
            self.load_channels()
        except Exception as e:
            self.session.open(MessageBox, "Greška pri kopiranju: " + str(e), MessageBox.TYPE_ERROR)

    def get_bouquets(self):
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
                                choices.append((bq_name, bq_path))
                        except Exception:
                            pass
        return choices

    def info_pressed(self):
        idx = self["list"].getSelectedIndex()
        if idx < 2 or not self.channel_data[idx]:
            return
            
        ref, name, provider, is_new = self.channel_data[idx]
        msg = "Ime kanala: %s\nProvajder: %s\n\nReferenca: %s" % (name, provider, ref)
        self.session.open(MessageBox, msg, MessageBox.TYPE_INFO)



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
