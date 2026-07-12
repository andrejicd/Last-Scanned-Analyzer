#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.Label import Label
from Components.Pixmap import Pixmap
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.LoadPixmap import LoadPixmap
import os
import glob
import io
import re
from twisted.web.client import getPage, downloadPage
from Components.Console import Console

try:
    from enigma import eDVBDB, eServiceReference
except ImportError:
    pass

PLUGIN_VERSION = "v1.4"

class LastScannedAnalyzerScreen(Screen):
    skin = """
        <screen name="LastScannedAnalyzerScreen" position="center,center" size="1280,720" title="LastScanned Analyzer" backgroundColor="#1e1e1e" flags="wfNoBorder">
            <!-- Main Header -->
            <eLabel position="0,0" size="1280,60" backgroundColor="#00142238" zPosition="-1" />
            <eLabel text="LastScanned Channel Analyzer """ + PLUGIN_VERSION + """" position="30,10" size="600,40" font="Regular;32" foregroundColor="#ffffff" backgroundColor="#000e355c" transparent="1" halign="left" valign="center" zPosition="1" />
            <widget name="key_menu" position="650,15" size="300,30" font="Regular;22" foregroundColor="#cccccc" backgroundColor="#000e355c" transparent="1" halign="right" valign="center" zPosition="1" />
            <widget name="key_info" position="1000,15" size="250,30" font="Regular;22" foregroundColor="#cccccc" backgroundColor="#000e355c" transparent="1" halign="right" valign="center" zPosition="1" />
            
            <!-- List frame -->
            <eLabel position="30,80" size="700,550" backgroundColor="#00000000" zPosition="0" />
            <widget name="list" position="40,90" size="680,530" itemHeight="35" font="Regular;26" foregroundColor="#ffffff" scrollbarMode="showOnDemand" transparent="1" backgroundColor="#00000000" zPosition="1" />
            
            <!-- Informacije o Kanalu (desna strana umesto videa) -->
            <widget name="picon" position="890,120" size="220,132" alphatest="blend" transparent="1" scale="1" zPosition="2" />
            <widget name="channel_info" position="760,280" size="480,300" font="Regular;24" foregroundColor="#cccccc" backgroundColor="#00000000" transparent="1" halign="center" valign="top" zPosition="1" />
            
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
        
        self["key_red"] = Label("Exit")
        self["key_green"] = Label("Select / Deselect")
        self["key_yellow"] = Label("New Only")
        self["key_blue"] = Label("Copy NEW")
        self["key_info"] = Label("INFO / OK")
        self["key_menu"] = Label("MENU = Options")
        
        self["picon"] = Pixmap()
        self["channel_info"] = Label("Press OK to play channel\nand see Transponder / Picon info")
        
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
        
        self["SetupActions"] = ActionMap(["SetupActions", "EPGSelectActions", "MenuActions"],
        {
            "cancel": self.close,
            "ok": self.ok_pressed,
            "info": self.info_pressed,
            "epg": self.info_pressed,
            "menu": self.open_scan,
        }, -1)
        
        self.onLayoutFinish.append(self.load_channels)
        self.onLayoutFinish.append(self.run_auto_update_check)

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
        transponders = {}
        if not os.path.exists(lamedb_path):
            return services, transponders
            
        with io.open(lamedb_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.read().splitlines()
            
        in_services = False
        in_transponders = False
        i = 0
        current_tp_key = None
        
        while i < len(lines):
            line = lines[i].strip()
            
            if line == "transponders":
                in_transponders = True
                i += 1
                continue
            if line == "end" and in_transponders:
                in_transponders = False
                i += 1
                continue
            if line == "services":
                in_services = True
                i += 1
                continue
            if line == "end" and in_services:
                break
                
            if in_transponders:
                if ':' in line and not line.startswith('s ') and not line.startswith('c ') and not line.startswith('t ') and not line.startswith('/'):
                    current_tp_key = line
                elif line.startswith('s ') or line.startswith('c ') or line.startswith('t '):
                    if current_tp_key:
                        transponders[current_tp_key] = line
                i += 1
                continue
                
            if in_services and ':' in line:
                parts = line.split(':')
                if len(parts) >= 4:
                    try:
                        s_id = int(parts[0], 16)
                        s_ns = int(parts[1], 16)
                        s_tsid = int(parts[2], 16)
                        s_onid = int(parts[3], 16)
                        
                        key = (s_id, s_ns, s_tsid, s_onid)
                        tp_key = "%08x:%04x:%04x" % (s_ns, s_tsid, s_onid)
                        
                        channel_type = 1
                        if len(parts) >= 5:
                            try:
                                channel_type = int(parts[4], 16) if parts[4].startswith('0x') else int(parts[4])
                            except Exception:
                                pass
                        
                        name = "Unknown"
                        provider = "Unknown"
                        vpid = ""
                        apid = ""
                        encrypted = False
                        
                        if i + 1 < len(lines):
                            name = lines[i+1]
                        
                        if i + 2 < len(lines) and (lines[i+2].startswith("p:") or lines[i+2].startswith("c:") or lines[i+2].startswith("C:") or lines[i+2].startswith("f:")):
                            prov_line = lines[i+2]
                            p_parts = prov_line.split(',')
                            for p in p_parts:
                                if p.startswith('p:'):
                                    provider = p[2:]
                                elif p.startswith('c:00'):
                                    vpid = str(int(p[4:], 16))
                                elif p.startswith('c:01'):
                                    apid = str(int(p[4:], 16))
                                elif p.startswith('C:') or p.startswith('c:09'):
                                    encrypted = True
                                    
                        services[key] = (name, provider, channel_type, tp_key, vpid, apid, encrypted)
                        i += 2
                        continue
                    except ValueError:
                        pass
            i += 1
            
        return services, transponders

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

        lamedb_info, self.lamedb_transponders = self.parse_lamedb(lamedb_file)
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
                        name = "Unknown Channel"
                        provider = "Unknown Provider"
                        # Čitamo pravi Service Type iz same reference (npr. 1:0:19:... -> tip je 19 u hexu)
                        c_type = 1
                        try:
                            ref_parts = ref.split(':')
                            if len(ref_parts) >= 3:
                                c_type = int(ref_parts[2], 16)
                        except:
                            pass
                            
                        tp_key = ""
                        vpid = ""
                        apid = ""
                        encrypted = False
                        if key and key in lamedb_info:
                            name, provider, _, tp_key, vpid, apid, encrypted = lamedb_info[key]
                            
                        # Formatiramo oznake
                        tags = ""
                        if is_new:
                            tags += "[NEW]  "
                        else:
                            tags += "       " # 7 spaces
                            
                        if encrypted:
                            tags += "[$] "
                        else:
                            tags += "    "
                        
                        if c_type == 2:
                            tags += "[Radio] "
                        elif c_type in [0x19, 25, 0x11, 17]:
                            tags += "[HD] "
                        elif c_type in [0x1f, 31]:
                            tags += "[4K] "
                            
                        sel_tag = "[ * ] " if ref in self.selected_refs else "      "
                            
                        display_text = "%s%s%s" % (sel_tag, tags, name)
                        
                        self.list.append(display_text)
                        self.channel_data.append((ref, name, provider, is_new, c_type, tp_key, vpid, apid, encrypted))
                        if is_new:
                            novi += 1
        except Exception as e:
            self.list.append("Error reading LastScanned.tv: " + str(e))
            self.channel_data.append(None)
            
        self.list[0] = "TOTAL CHANNELS: %d  |  NEW FOUND: %d" % (ukupno, novi)
        self.list[1] = "-" * 80
        
        self["list"].setList(self.list)
        # Obrisali smo moveToIndex jer u MenuList klasi to ne postoji i izazivalo je krah aplikacije.
        if self["list"].instance is not None:
            self["list"].instance.moveSelectionTo(0)

    def get_tp_info(self, tp_key):
        if not hasattr(self, 'lamedb_transponders') or not tp_key:
            return "No Transponder Info"
        tp_data = self.lamedb_transponders.get(tp_key, "")
        if not tp_data:
            return "Unknown Transponder"
            
        tp_data = tp_data.strip()
        try:
            if tp_data.startswith('s '):
                parts = tp_data[2:].split(':')
                freq = int(parts[0]) / 1000
                sr = int(parts[1]) / 1000
                pol_map = {0: 'H', 1: 'V', 2: 'L', 3: 'R'}
                pol = pol_map.get(int(parts[2]), '?')
                pos = int(parts[4]) if len(parts) > 4 else 0
                dir = "E"
                if pos > 1800:
                    pos = 3600 - pos
                    dir = "W"
                    
                fec_map = {0:'Auto', 1:'1/2', 2:'2/3', 3:'3/4', 4:'5/6', 5:'7/8', 6:'8/9', 7:'3/5', 8:'4/5', 9:'9/10', 10:'None'}
                fec = fec_map.get(int(parts[3]) if len(parts)>3 else 0, 'Auto')
                
                sys_map = {0: 'DVB-S', 1: 'DVB-S2'}
                system = sys_map.get(int(parts[7]) if len(parts)>7 else 0, 'DVB-S')
                
                mod_map = {0:'Auto', 1:'QPSK', 2:'8PSK', 3:'16APSK', 4:'32APSK'}
                modulation = mod_map.get(int(parts[8]) if len(parts)>8 else 1, 'QPSK')
                
                return "Satellite: %.1f°%s\nFreq: %d MHz\nPol: %s   SR: %d\n%s  %s  FEC: %s" % (pos / 10.0, dir, freq, pol, sr, system, modulation, fec)
            elif tp_data.startswith('c '):
                parts = tp_data[2:].split(':')
                return "Cable\nFreq: %d MHz" % (int(parts[0]) / 1000)
            elif tp_data.startswith('t '):
                parts = tp_data[2:].split(':')
                return "Terrestrial (DVB-T)\nFreq: %d MHz" % (int(parts[0]) / 1000000)
        except Exception:
            return "Error parsing TP"
        return "Unknown DVB Type"

    def show_picon(self, ref_string):
        ref_parts = ref_string.split(':')
        if len(ref_parts) > 10:
            ref_parts = ref_parts[:10]
            
        # Picon names always expect the first part to be '1' even for IPTV (4097)
        if len(ref_parts) > 0 and ref_parts[0] != '1':
            try:
                # Samo ako je neki broj tipa 4097, 5002, itd.
                if int(ref_parts[0], 16) != 1:
                    ref_parts[0] = '1'
            except:
                ref_parts[0] = '1'
                
        while len(ref_parts) > 0 and ref_parts[-1] == '':
            ref_parts.pop()
            
        picon_name = "_".join(ref_parts) + ".png"
        picon_name_lower = picon_name.lower()
        picon_paths = [
            "/usr/share/enigma2/picon/",
            "/media/usb/picon/",
            "/media/hdd/picon/",
            "/hdd/picon/",
            "/picon/",
            "/usr/share/picon/"
        ]
        
        found_path = ""
        for p in picon_paths:
            path = os.path.join(p, picon_name)
            path_lower = os.path.join(p, picon_name_lower)
            if os.path.exists(path):
                self["picon"].instance.setPixmap(LoadPixmap(path))
                self["picon"].show()
                found_path = path
                break
            elif os.path.exists(path_lower):
                self["picon"].instance.setPixmap(LoadPixmap(path_lower))
                self["picon"].show()
                found_path = path_lower
                break
                
        if not found_path:
            self["picon"].hide()
            
        return found_path, picon_name_lower

    def ok_pressed(self):
        idx = self["list"].getSelectedIndex()
        if idx < 2 or not self.channel_data[idx]:
            return
            
        ref, name, provider, is_new, c_type, tp_key, vpid, apid, encrypted = self.channel_data[idx]
        try:
            self.session.nav.playService(eServiceReference(ref))
            
            # Prikaz Picona i vracanje debug putanje
            p_path, p_expected = self.show_picon(ref)
            
            # Prikaz informacija u interfejsu
            res_tag = "Standard (SD)"
            if c_type in [0x19, 25, 0x11, 17]:
                res_tag = "High Definition (HD)"
            elif c_type in [0x1f, 31]:
                res_tag = "Ultra HD (4K)"
            elif c_type == 2:
                res_tag = "Radio Channel"
                
            enc_tag = "🔒 Encrypted" if encrypted else "🔓 Free To Air (FTA)"
            pid_info = "VPID: %s  |  APID: %s" % (vpid if vpid else "N/A", apid if apid else "N/A")
                
            tp_info = self.get_tp_info(tp_key)
                
            info_text = "Channel: %s\nProvider: %s\nStatus: %s\n%s\n\n%s\n\n%s" % (name, provider, enc_tag, pid_info, tp_info, ref)
            
            if p_path:
                info_text += "\n\n[Picon: %s]" % p_path
            else:
                info_text += "\n\n[Picon not found: %s]" % p_expected
                
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
            self.session.open(MessageBox, "No channels to copy!", MessageBox.TYPE_INFO)
            return
            
        try:
            naslov = "to copy SELECTED channels:" if self.selected_refs else "to copy ALL NEW channels:"
            self._channels_to_copy = to_copy
            self.session.openWithCallback(self.bouquet_chosen_multi, ChoiceBox, title="Choose bouquet " + naslov, list=self.get_bouquets())
        except Exception as e:
            self.session.open(MessageBox, "Error: " + str(e), MessageBox.TYPE_ERROR)

    def bouquet_chosen_multi(self, choice):
        if choice is None:
            return
            
        target = choice[1]
        
        if target == "CREATE_NEW":
            self.session.openWithCallback(self.new_bouquet_name_entered, VirtualKeyBoard, title="Enter new bouquet name:", text="")
            return
            
        self._copy_channels_to_bouquet(target)
        
    def new_bouquet_name_entered(self, name):
        if not name:
            return
            
        safe_name = "".join(x for x in name if x.isalnum() or x in " -_")
        if not safe_name:
            safe_name = "New_Bouquet"
            
        filename = "userbouquet.ls_%s.tv" % safe_name.replace(" ", "_").lower()
        filepath = os.path.join("/etc/enigma2", filename)
        
        # Create new bouquet file
        try:
            with io.open(filepath, 'w', encoding='utf-8') as f:
                f.write(u"#NAME %s\n" % name)
                
            # Add to bouquets.tv
            bouquets_tv = "/etc/enigma2/bouquets.tv"
            bq_line = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet\n' % filename
            
            needs_append = True
            if os.path.exists(bouquets_tv):
                with io.open(bouquets_tv, 'r', encoding='utf-8', errors='ignore') as f:
                    if bq_line in f.read():
                        needs_append = False
            
            if needs_append:
                with io.open(bouquets_tv, 'a', encoding='utf-8') as f:
                    f.write(u"" + bq_line)
                    
        except Exception as e:
            self.session.open(MessageBox, "Error creating bouquet: " + str(e), MessageBox.TYPE_ERROR)
            return
            
        self._copy_channels_to_bouquet(filepath)

    def _copy_channels_to_bouquet(self, bq_file):
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
                        f.write(u"#SERVICE %s\n" % ref)
                        
            try:
                eDVBDB.getInstance().reloadBouquets()
            except Exception:
                pass
                
            self.session.open(MessageBox, "Successfully copied %d channels!" % len(channels), MessageBox.TYPE_INFO)
            self.selected_refs.clear()
            self.load_channels()
        except Exception as e:
            self.session.open(MessageBox, "Copy Error: " + str(e), MessageBox.TYPE_ERROR)

    def get_bouquets(self):
        base_dir = "/etc/enigma2"
        bouquets_tv = os.path.join(base_dir, "bouquets.tv")
        choices = [("+ Create New Bouquet", "CREATE_NEW")]
        
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

    def open_scan(self):
        options = [
            ("Scan Channels", "scan"),
            ("Check for Updates", "update")
        ]
        self.session.openWithCallback(self.menu_callback, ChoiceBox, title="Options Menu", list=options)

    def menu_callback(self, choice):
        if choice:
            if choice[1] == "scan":
                try:
                    from Screens.ScanSetup import ScanSetup
                    self.session.openWithCallback(self.scan_finished, ScanSetup)
                except ImportError:
                    self.session.open(MessageBox, "Greška: Ne mogu da učitam ScanSetup modul.", MessageBox.TYPE_ERROR)
            elif choice[1] == "update":
                self.check_for_update(auto_check=False)

    def run_auto_update_check(self):
        self.check_for_update(auto_check=True)

    def check_for_update(self, auto_check=False):
        url = b"https://raw.githubusercontent.com/andrejicd/Last-Scanned-Analyzer/main/plugin.py"
        try:
            getPage(url, timeout=5).addCallback(self.update_check_callback, auto_check).addErrback(self.update_check_errback, auto_check)
        except Exception as e:
            if not auto_check:
                self.session.open(MessageBox, "Error checking for updates: " + str(e), MessageBox.TYPE_ERROR)

    def update_check_callback(self, html, auto_check):
        try:
            if not isinstance(html, str):
                html = html.decode('utf-8')
            m = re.search(r'PLUGIN_VERSION\s*=\s*"([^"]+)"', html)
            if m:
                remote_version = m.group(1)
                
                def parse_ver(v):
                    v_clean = ""
                    for char in v:
                        if char.isdigit() or char == '.':
                            v_clean += char
                    return [int(x) for x in v_clean.split('.') if x]

                remote_parts = parse_ver(remote_version)
                local_parts = parse_ver(PLUGIN_VERSION)
                
                is_newer = False
                for i in range(max(len(remote_parts), len(local_parts))):
                    r = remote_parts[i] if i < len(remote_parts) else 0
                    l = local_parts[i] if i < len(local_parts) else 0
                    if r > l:
                        is_newer = True
                        break
                    elif r < l:
                        break

                if is_newer:
                    msg = "New version %s is available! (Current: %s)\n\nDo you want to update now?" % (remote_version, PLUGIN_VERSION)
                    self.session.openWithCallback(self.update_prompt_callback, MessageBox, msg, MessageBox.TYPE_YESNO)
                else:
                    if not auto_check:
                        self.session.open(MessageBox, "You have the latest version (%s)." % PLUGIN_VERSION, MessageBox.TYPE_INFO)
            else:
                if not auto_check:
                    self.session.open(MessageBox, "Could not determine remote version.", MessageBox.TYPE_ERROR)
        except Exception as e:
            if not auto_check:
                self.session.open(MessageBox, "Error parsing update data: " + str(e), MessageBox.TYPE_ERROR)

    def update_check_errback(self, error, auto_check):
        if not auto_check:
            self.session.open(MessageBox, "Failed to connect to update server.", MessageBox.TYPE_ERROR)

    def update_prompt_callback(self, answer):
        if answer:
            self.do_update()

    def do_update(self):
        url = b"https://raw.githubusercontent.com/andrejicd/Last-Scanned-Analyzer/main/installer.sh"
        self.installer_path = "/tmp/installer.sh"
        try:
            downloadPage(url, self.installer_path).addCallback(self.update_download_callback).addErrback(self.update_download_errback)
        except Exception as e:
            self.session.open(MessageBox, "Error starting download: " + str(e), MessageBox.TYPE_ERROR)

    def update_download_callback(self, result):
        os.chmod(self.installer_path, 0o755)
        self.session.open(MessageBox, "Updating plugin...\nGUI will restart automatically if successful.", MessageBox.TYPE_INFO, timeout=5)
        self.console = Console()
        self.console.ePopen(self.installer_path, self.update_finished)

    def update_download_errback(self, error):
        self.session.open(MessageBox, "Failed to download update script.", MessageBox.TYPE_ERROR)

    def update_finished(self, result, retval, extra_args):
        pass

    def scan_finished(self, *args):
        # Nakon zatvaranja prozora za skeniranje (ScanSetup), ponovo učitavamo kanale
        # jer je fajl LastScanned.tv verovatno ažuriran novim kanalima.
        self.load_channels()

    def info_pressed(self):
        idx = self["list"].getSelectedIndex()
        if idx < 2 or not self.channel_data[idx]:
            return
            
        ref, name, provider, is_new, c_type, tp_key, vpid, apid, encrypted = self.channel_data[idx]
        tp_info = self.get_tp_info(tp_key)
        enc_tag = "Encrypted" if encrypted else "FTA"
        msg = "Channel Name: %s\nProvider: %s\nStatus: %s\n\n%s\n\nReference: %s" % (name, provider, enc_tag, tp_info, ref)
        self.session.open(MessageBox, msg, MessageBox.TYPE_INFO)



def main(session, **kwargs):
    session.open(LastScannedAnalyzerScreen)

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="LastScanned Analyzer %s" % PLUGIN_VERSION, 
            description="Analyze and sort Last Scanned channels", 
            where=PluginDescriptor.WHERE_PLUGINMENU, 
            icon="plugin.png",
            fnc=main
        )
    ]
