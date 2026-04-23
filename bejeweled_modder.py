import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import re
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import webbrowser
import urllib.request
import zipfile
import io

ctk.set_appearance_mode("dark")  
ctk.set_default_color_theme("blue") 


class BejeweledModder:
    """Main application class for Bejeweled 3 modding tool."""
    
    DEFAULT_STEAM_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Bejeweled 3"
    CONFIG_FILE = "secret.cfg"
    PROPERTIES_FOLDER = "properties"
    MAIN_PAK = "main.pak"
    
    QUEST_MODES = {
        "butterflies": "Butterflies",
        "poker": "Poker",
        "icestorm": "Ice Storm",
        "diamondmine": "Diamond Mine"
    }
    
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("Modjeweled")
        self.root.geometry("1000x750")
        self.root.minsize(900, 650)
        
        self.game_path = ctk.StringVar(value=self.DEFAULT_STEAM_PATH)
        self.quickbms_path = ctk.StringVar()
        self.script_path = ctk.StringVar()
        self.config_loaded = False
        self.config_path = None
        self.config_content = ""
        self.parsed_sections = {}
        
        self.create_menu()
        self.create_main_ui()
        self.create_status_bar()
        
        self.load_settings()
        
    def create_menu(self):
        """Create the application menu bar."""
        self.menu_frame = ctk.CTkFrame(self.root, height=40)
        self.menu_frame.pack(fill="x", side="top")
        self.menu_frame.pack_propagate(False)
        
        file_btn = ctk.CTkButton(self.menu_frame, text="File", width=60, height=30,
                                  fg_color="transparent", text_color=("gray10", "#DCE4EE"),
                                  hover_color=("gray70", "gray30"), command=self.show_file_menu)
        file_btn.pack(side="left", padx=5, pady=5)
        
        tools_btn = ctk.CTkButton(self.menu_frame, text="Tools", width=60, height=30,
                                   fg_color="transparent", text_color=("gray10", "#DCE4EE"),
                                   hover_color=("gray70", "gray30"), command=self.show_tools_menu)
        tools_btn.pack(side="left", padx=5, pady=5)
        
        help_btn = ctk.CTkButton(self.menu_frame, text="Help", width=60, height=30,
                                 fg_color="transparent", text_color=("gray10", "#DCE4EE"),
                                 hover_color=("gray70", "gray30"), command=self.show_help_menu)
        help_btn.pack(side="left", padx=5, pady=5)
        
        theme_label = ctk.CTkLabel(self.menu_frame, text="Theme:", font=("", 12))
        theme_label.pack(side="right", padx=(0, 5))
        
        theme_menu = ctk.CTkOptionMenu(self.menu_frame, values=["System", "Dark", "Light"],
                                        command=self.change_theme, width=100, height=30)
        theme_menu.set("Dark")
        theme_menu.pack(side="right", padx=5)
        
    def show_file_menu(self):
        """Show file menu dropdown."""
        self._show_menu("file", [
            ("Open Game Directory", self.browse_game_path),
            ("Open Config File", self.open_config_direct),
            ("separator", None),
            ("Save Config", self.save_config),
            ("Save Config As...", self.save_config_as),
            ("separator", None),
            ("Exit", self.root.quit)
        ])
        
    def show_tools_menu(self):
        """Show tools menu dropdown."""
        self._show_menu("tools", [
            ("Extract main.pak", self.extract_main_pak),
            ("separator", None),
            ("Download QuickBMS", self.download_quickbms),
            ("Download 7x7m.bms Script", self.download_script),
            ("separator", None),
            ("Set QuickBMS Path", self.set_quickbms_path),
            ("Set Script Path (7x7m.bms)", self.set_script_path),
            ("separator", None),
            ("Backup Current Config", self.backup_config),
            ("Restore Backup", self.restore_backup)
        ])
        
    def show_help_menu(self):
        """Show help menu dropdown."""
        self._show_menu("help", [
            ("Quick Start Guide", self.show_quick_start),
            ("About", self.show_about)
        ])
    
    def _show_menu(self, menu_name, options):
        """Show a dropdown menu."""
        if hasattr(self, '_current_menu') and self._current_menu:
            try:
                self._current_menu.destroy()
            except:
                pass
        
        menu = ctk.CTkToplevel(self.root)
        menu.overrideredirect(True)
        menu.attributes("-topmost", True)
        menu.lift()
        
        self.root.update_idletasks()
        btn_x = 10 if menu_name == "file" else (75 if menu_name == "tools" else 140)
        x = self.root.winfo_x() + btn_x + 5
        y = self.root.winfo_y() + 75
        
        item_height = 32
        separator_height = 12
        num_items = len([o for o in options if o[0] != "separator"])
        num_separators = len([o for o in options if o[0] == "separator"])
        height = (num_items * item_height) + (num_separators * separator_height) + 20
        width = 220 if menu_name == "tools" else 200
        
        menu.geometry(f"{width}x{height}+{x}+{y}")
        
        menu_frame = ctk.CTkFrame(menu, corner_radius=8, border_width=1, border_color="gray50")
        menu_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        for text, command in options:
            if text == "separator":
                sep = ctk.CTkFrame(menu_frame, height=2, fg_color="gray40")
                sep.pack(fill="x", padx=10, pady=5)
            else:
                btn = ctk.CTkButton(menu_frame, text=text, 
                                    command=lambda c=command, m=menu: self._menu_click(m, c),
                                    fg_color="transparent", 
                                    text_color=("gray10", "#DCE4EE"),
                                    hover_color=("gray75", "gray25"), 
                                    anchor="w", height=30,
                                    corner_radius=6)
                btn.pack(fill="x", padx=5, pady=2)
        
        self._current_menu = menu
        
        menu.bind("<Escape>", lambda e: self._close_menu())
        
        self.root.bind("<Button-1>", lambda e: self._close_menu())
        menu.bind("<Button-1>", lambda e: "break")
        
        menu.focus_set()
        
    def _close_menu(self):
        """Close the current menu if open."""
        if hasattr(self, '_current_menu') and self._current_menu:
            try:
                self._current_menu.destroy()
            except:
                pass
            self._current_menu = None
        try:
            self.root.unbind("<Button-1>")
        except:
            pass
                
    def _menu_click(self, menu, command):
        """Handle menu item click."""
        menu.destroy()
        self._current_menu = None
        if command:
            self.root.after(50, command)
            
    def change_theme(self, theme):
        """Change the application theme."""
        ctk.set_appearance_mode(theme)
        
    def create_main_ui(self):
        """Create the main user interface."""
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        path_frame = ctk.CTkFrame(main_frame)
        path_frame.pack(fill="x", pady=(0, 10))
        
        path_label = ctk.CTkLabel(path_frame, text="Game Directory:", font=("", 14, "bold"))
        path_label.pack(side="left", padx=(10, 5))
        
        path_entry = ctk.CTkEntry(path_frame, textvariable=self.game_path, width=500)
        path_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        browse_btn = ctk.CTkButton(path_frame, text="Browse", command=self.browse_game_path, width=80)
        browse_btn.pack(side="left", padx=5)
        
        load_btn = ctk.CTkButton(path_frame, text="Load Config", command=self.load_config, 
                                  fg_color="green", hover_color="darkgreen", width=100)
        load_btn.pack(side="left", padx=5)
        
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True)
        
        self.tabview.add("Quick Mods")
        self.tabview.add("Butterflies")
        self.tabview.add("Poker")
        self.tabview.add("Ice Storm")
        self.tabview.add("Diamond Mine")
        self.tabview.add("Raw Editor")
        
        self.create_quick_mods_tab()
        self.create_butterflies_tab()
        self.create_poker_tab()
        self.create_icestorm_tab()
        self.create_diamondmine_tab()
        self.create_raw_editor_tab()
        
    def create_quick_mods_tab(self):
        """Create the quick mods tab for simple gem color modifications."""
        frame = self.tabview.tab("Quick Mods")
        
        desc_label = ctk.CTkLabel(frame, text="Quickly modify gem colors (ColorCount) for any quest mode.\nColorCount controls how many different gem types appear (1-6).",
                                  font=("", 13), justify="left")
        desc_label.pack(anchor="w", pady=(10, 15))
        
        quest_frame = ctk.CTkFrame(frame)
        quest_frame.pack(fill="x", pady=(0, 15))
        
        quest_label = ctk.CTkLabel(quest_frame, text="Select Quest Mode:", font=("", 14, "bold"))
        quest_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        quest_scroll = ctk.CTkScrollableFrame(quest_frame, height=150)
        quest_scroll.pack(fill="x", padx=10, pady=(0, 10))
        
        self.quest_selection = ctk.StringVar()
        for key, name in self.QUEST_MODES.items():
            rb = ctk.CTkRadioButton(quest_scroll, text=f"{name} ({key})", variable=self.quest_selection, value=key)
            rb.pack(anchor="w", pady=2)
        
        color_frame = ctk.CTkFrame(frame)
        color_frame.pack(fill="x", pady=(0, 15))
        
        color_label = ctk.CTkLabel(color_frame, text="ColorCount Settings", font=("", 14, "bold"))
        color_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        color_row = ctk.CTkFrame(color_frame, fg_color="transparent")
        color_row.pack(fill="x", padx=10, pady=10)
        
        color_label2 = ctk.CTkLabel(color_row, text="Number of Gem Colors (1-6):")
        color_label2.pack(side="left")
        
        self.colorcount_var = ctk.StringVar(value="6")
        color_spinbox = ctk.CTkOptionMenu(color_row, values=["1", "2", "3", "4", "5", "6"],
                                           variable=self.colorcount_var, width=80)
        color_spinbox.pack(side="left", padx=10)
        
        apply_btn = ctk.CTkButton(color_row, text="Apply to Selected Quest", command=self.apply_colorcount,
                                   fg_color="blue", hover_color="darkblue")
        apply_btn.pack(side="left", padx=10)
        
        apply_all_btn = ctk.CTkButton(color_row, text="Apply to All Quests", command=self.apply_colorcount_all,
                                       fg_color="purple", hover_color="darkviolet")
        apply_all_btn.pack(side="left", padx=10)
        
        reset_btn = ctk.CTkButton(color_row, text="Reset Selected", command=self.reset_colorcount,
                                   fg_color="red", hover_color="darkred")
        reset_btn.pack(side="left", padx=10)
        
        debug_btn = ctk.CTkButton(color_row, text="Debug Info", command=self.show_debug_info,
                                   fg_color="gray", hover_color="darkgray")
        debug_btn.pack(side="left", padx=10)
        
        current_frame = ctk.CTkFrame(frame)
        current_frame.pack(fill="both", expand=True)
        
        current_label = ctk.CTkLabel(current_frame, text="Current ColorCount Values", font=("", 14, "bold"))
        current_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.colorcount_text = ctk.CTkTextbox(current_frame, height=150, state="disabled")
        self.colorcount_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
    def create_butterflies_tab(self):
        """Create the Butterflies mod tab."""
        frame = self.tabview.tab("Butterflies")
        
        desc = ctk.CTkLabel(frame, text="Modify Butterflies game mode parameters.", font=("", 13))
        desc.pack(anchor="w", pady=(10, 15))
        
        self.butterflies_vars = {}
        
        settings_frame = ctk.CTkFrame(frame)
        settings_frame.pack(fill="x", pady=(0, 15))
        
        settings_label = ctk.CTkLabel(settings_frame, text="Butterflies Settings", font=("", 14, "bold"))
        settings_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        butterfly_settings = [
            ("SpawnCountStart", "Butterflies at Start (1-7):", 1, 0, 7),
            ("SpawnCountMax", "Max Butterflies on Screen:", 2.5, 0, 100),
            ("SpawnCountPerLevel", "Butterflies Per Level:", 0.02, 0, 10),
            ("SideSpawnChance", "Side Spawn Chance:", -0.2, -1, 1),
            ("SideSpawnChancePerLevel", "Side Spawn Per Level:", 0.002667, 0, 1),
            ("SideSpawnChanceMax", "Max Side Spawn Chance:", 0.20, 0, 1),
        ]
        
        for key, label, default, min_val, max_val in butterfly_settings:
            row_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=5)
            
            lbl = ctk.CTkLabel(row_frame, text=label, width=250, anchor="w")
            lbl.pack(side="left")
            
            var = ctk.DoubleVar(value=default)
            self.butterflies_vars[key] = var
            
            entry = ctk.CTkEntry(row_frame, textvariable=var, width=100)
            entry.pack(side="left", padx=10)
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(btn_frame, text="Load Current Values", command=self.load_butterflies_values).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Apply Changes", command=self.apply_butterflies, fg_color="green", hover_color="darkgreen").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Reset to Defaults", command=self.reset_butterflies, fg_color="gray", hover_color="darkgray").pack(side="left", padx=5)
        
    def create_poker_tab(self):
        """Create the Poker mod tab."""
        frame = self.tabview.tab("Poker")
        
        desc = ctk.CTkLabel(frame, text="Modify Poker game mode parameters.", font=("", 13))
        desc.pack(anchor="w", pady=(10, 15))
        
        self.poker_vars = {}
        
        settings_frame = ctk.CTkFrame(frame)
        settings_frame.pack(fill="x", pady=(0, 15))
        
        settings_label = ctk.CTkLabel(settings_frame, text="Poker Settings", font=("", 14, "bold"))
        settings_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        poker_basic = [
            ("FlameBonus", "Flame Gem Bonus:", 100),
            ("StarBonus", "Star Gem Bonus:", 250),
            ("SkullMax", "Max Hand for Skull:", 5),
        ]
        
        for key, label, default in poker_basic:
            row_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=5)
            
            lbl = ctk.CTkLabel(row_frame, text=label, width=200, anchor="w")
            lbl.pack(side="left")
            
            var = ctk.IntVar(value=default)
            self.poker_vars[key] = var
            
            entry = ctk.CTkEntry(row_frame, textvariable=var, width=100)
            entry.pack(side="left", padx=10)
        
        hand_frame = ctk.CTkFrame(frame)
        hand_frame.pack(fill="x", pady=(0, 15))
        
        hand_label = ctk.CTkLabel(hand_frame, text="Hand Values (Points per hand type)", font=("", 14, "bold"))
        hand_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        hand_desc = ctk.CTkLabel(hand_frame, text="Format: Pair, Spectrum, 2 Pair, 3 of a Kind, Full House, 4 of a Kind, Flush",
                                  font=("", 11, "italic"))
        hand_desc.pack(anchor="w", padx=10, pady=5)
        
        self.poker_handvalues = ctk.StringVar(value="2500, 5000, 7500, 10000, 15000, 30000, 50000")
        hand_entry = ctk.CTkEntry(hand_frame, textvariable=self.poker_handvalues, width=500)
        hand_entry.pack(fill="x", padx=10, pady=(0, 10))
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(btn_frame, text="Load Current Values", command=self.load_poker_values).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Apply Changes", command=self.apply_poker, fg_color="green", hover_color="darkgreen").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Reset to Defaults", command=self.reset_poker, fg_color="gray", hover_color="darkgray").pack(side="left", padx=5)
        
    def create_icestorm_tab(self):
        """Create the Ice Storm mod tab."""
        frame = self.tabview.tab("Ice Storm")
        
        desc = ctk.CTkLabel(frame, text="Modify Ice Storm game mode parameters. This mode has many settings.", font=("", 13))
        desc.pack(anchor="w", pady=(10, 15))
        
        self.icestorm_vars = {}
        
        scroll_frame = ctk.CTkScrollableFrame(frame)
        scroll_frame.pack(fill="both", expand=True)
        
        settings_frame = ctk.CTkFrame(scroll_frame)
        settings_frame.pack(fill="x", pady=(0, 15))
        
        settings_label = ctk.CTkLabel(settings_frame, text="Ice Storm Settings", font=("", 14, "bold"))
        settings_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        icestorm_settings = [
            ("MatchPushStr", "Match Push Strength:", 0.07),
            ("SpecialGemPushMod", "Special Gem Push Mod:", 1.3),
            ("SecondsUntilLose", "Seconds Until Lose:", 12),
            ("RemoveBonusColumn", "Remove Bonus Column:", 2),
            ("DoubleEdgeMult", "Double Edge Multiplier:", 1.0),
            ("FireSpeedMult", "Fire Speed Multiplier:", 2.0),
            ("ColDestroyBonus", "Column Destroy Bonus:", 1500),
            ("MaxRandFireSpeedColDelta", "Max Random Fire Speed Delta:", 0.1),
            ("DoubleColSpeedMult", "Double Column Speed Mult:", 1.5),
            ("FreezeDurationPerNegStrength", "Freeze Duration Per Neg Strength:", 50.0),
            ("FreezeMax", "Freeze Max:", 100.0),
            ("FirstPushImpulse", "First Push Impulse:", 0.0),
            ("FirstPushDecay", "First Push Decay:", 0.0),
        ]
        
        for key, label, default in icestorm_settings:
            row_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=3)
            
            lbl = ctk.CTkLabel(row_frame, text=label, width=280, anchor="w")
            lbl.pack(side="left")
            
            var = ctk.DoubleVar(value=default)
            self.icestorm_vars[key] = var
            
            entry = ctk.CTkEntry(row_frame, textvariable=var, width=100)
            entry.pack(side="left", padx=10)
        
        complex_frame = ctk.CTkFrame(scroll_frame)
        complex_frame.pack(fill="x", pady=(0, 15))
        
        complex_label = ctk.CTkLabel(complex_frame, text="Advanced Settings (Edit in Raw Editor for full control)", font=("", 14, "bold"))
        complex_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        complex_settings = [
            ("ColCountBonus", "Column Count Bonus:"),
            ("ColComboCoolDownVsCount", "Column Combo Cooldown:"),
            ("MultiplierIceReq", "Multiplier Ice Required:"),
            ("RowFireSpeed", "Row Fire Speed:"),
            ("ColDistribution", "Column Distribution:"),
            ("ReprieveStrVsRow", "Reprieve Strength vs Row:"),
        ]
        
        for key, label in complex_settings:
            row_frame = ctk.CTkFrame(complex_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=3)
            
            lbl = ctk.CTkLabel(row_frame, text=label, width=250, anchor="w")
            lbl.pack(side="left")
            
            var = ctk.StringVar()
            self.icestorm_vars[key] = var
            
            entry = ctk.CTkEntry(row_frame, textvariable=var, width=400)
            entry.pack(side="left", padx=10, fill="x", expand=True)
        
        level_frame = ctk.CTkFrame(scroll_frame)
        level_frame.pack(fill="x", pady=(0, 15))
        
        level_label = ctk.CTkLabel(level_frame, text="Level Settings (1-15)", font=("", 14, "bold"))
        level_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        level_desc = ctk.CTkLabel(level_frame, text="Format: doubleCols, colCount, fireSpeed, seconds, crackSpeedMod, levelProgressCv",
                                   font=("", 11, "italic"))
        level_desc.pack(anchor="w", padx=10, pady=5)
        
        self.icestorm_levels = {}
        for i in range(1, 16):
            row_frame = ctk.CTkFrame(level_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=2)
            
            lbl = ctk.CTkLabel(row_frame, text=f"Level {i}:", width=80, anchor="w")
            lbl.pack(side="left")
            
            var = ctk.StringVar()
            self.icestorm_levels[f"Level{i}"] = var
            
            entry = ctk.CTkEntry(row_frame, textvariable=var, width=500)
            entry.pack(side="left", padx=10, fill="x", expand=True)
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(btn_frame, text="Load Current Values", command=self.load_icestorm_values).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Apply Changes", command=self.apply_icestorm, fg_color="green", hover_color="darkgreen").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Reset to Defaults", command=self.reset_icestorm, fg_color="gray", hover_color="darkgray").pack(side="left", padx=5)
        
    def create_diamondmine_tab(self):
        """Create the Diamond Mine mod tab."""
        frame = self.tabview.tab("Diamond Mine")
        
        desc = ctk.CTkLabel(frame, text="Modify Diamond Mine game mode parameters.", font=("", 13))
        desc.pack(anchor="w", pady=(10, 15))
        
        self.diamondmine_vars = {}
        
        scroll_frame = ctk.CTkScrollableFrame(frame)
        scroll_frame.pack(fill="both", expand=True)
        
        basic_frame = ctk.CTkFrame(scroll_frame)
        basic_frame.pack(fill="x", pady=(0, 15))
        
        basic_label = ctk.CTkLabel(basic_frame, text="Basic Settings", font=("", 14, "bold"))
        basic_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        basic_settings = [
            ("Time", "Time (seconds):", 90),
            ("TargetCount", "Target Count:", 200),
            ("TimeBonus", "Time Bonus:", 30),
            ("MegaTimeBonus", "Mega Time Bonus:", 90),
            ("DigCountPerScroll", "Dig Count Per Scroll:", 2),
            ("HighScoreBase", "High Score Base:", 50000),
            ("HighScoreIncr", "High Score Increment:", 10000),
            ("ArtifactBaseValue", "Artifact Base Value:", 1500),
            ("GoldValue", "Gold Value:", 1000),
            ("DiamondValue", "Diamond Value:", 2500),
            ("ArtifactMinTiles", "Artifact Min Tiles:", 10),
            ("ArtifactMaxTiles", "Artifact Max Tiles:", 26),
            ("ArtifactSkipTileCount", "Artifact Skip Tile Count:", 4),
        ]
        
        for key, label, default in basic_settings:
            row_frame = ctk.CTkFrame(basic_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=3)
            
            lbl = ctk.CTkLabel(row_frame, text=label, width=200, anchor="w")
            lbl.pack(side="left")
            
            var = ctk.IntVar(value=default)
            self.diamondmine_vars[key] = var
            
            entry = ctk.CTkEntry(row_frame, textvariable=var, width=100)
            entry.pack(side="left", padx=10)
        
        bool_frame = ctk.CTkFrame(scroll_frame)
        bool_frame.pack(fill="x", pady=(0, 15))
        
        bool_label = ctk.CTkLabel(bool_frame, text="Boolean Settings", font=("", 14, "bold"))
        bool_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.diamondmine_vars["HyperMixers"] = ctk.BooleanVar(value=True)
        check = ctk.CTkCheckBox(bool_frame, text="Hyper Mixers Enabled", variable=self.diamondmine_vars["HyperMixers"])
        check.pack(anchor="w", padx=10, pady=10)
        
        string_frame = ctk.CTkFrame(scroll_frame)
        string_frame.pack(fill="x", pady=(0, 15))
        
        string_label = ctk.CTkLabel(string_frame, text="Advanced Settings", font=("", 14, "bold"))
        string_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        string_settings = [
            ("TreasureRange", "Treasure Range:"),
            ("DarkRockFrequency", "Dark Rock Frequency:"),
            ("PowerGemThresholdDepth0", "Power Gem Threshold Depth 0:"),
            ("PowerGemThresholdDepth20", "Power Gem Threshold Depth 20:"),
            ("PowerGemThresholdDepth40", "Power Gem Threshold Depth 40:"),
            ("ArtifactPossRange", "Artifact Poss Range:"),
            ("MinBrickStrPerLevel", "Min Brick Str Per Level:"),
            ("MaxBrickStrPerLevel", "Max Brick Str Per Level:"),
            ("EdgeBrickStrPerLevel", "Edge Brick Str Per Level:"),
            ("MinMineStrPerLevel", "Min Mine Str Per Level:"),
            ("MaxMineStrPerLevel", "Max Mine Str Per Level:"),
            ("MineProbPerLevel", "Mine Prob Per Level:"),
            ("BrickStrSpread", "Brick Str Spread:"),
            ("MineStrSpread", "Mine Str Spread:"),
            ("ArtifactSpread", "Artifact Spread:"),
        ]
        
        for key, label in string_settings:
            row_frame = ctk.CTkFrame(string_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=3)
            
            lbl = ctk.CTkLabel(row_frame, text=label, width=250, anchor="w")
            lbl.pack(side="left")
            
            var = ctk.StringVar()
            self.diamondmine_vars[key] = var
            
            entry = ctk.CTkEntry(row_frame, textvariable=var, width=400)
            entry.pack(side="left", padx=10, fill="x", expand=True)
        
        grid_frame = ctk.CTkFrame(scroll_frame)
        grid_frame.pack(fill="x", pady=(0, 15))
        
        grid_label = ctk.CTkLabel(grid_frame, text="Grid Settings (Advanced)", font=("", 14, "bold"))
        grid_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        grid_desc = ctk.CTkLabel(grid_frame, text="Grid codes: 0=empty, 1-4=block strength, 5=infinite block, m=money, h=hypercube, s=shuffle, r=randomized",
                                  font=("", 11, "italic"))
        grid_desc.pack(anchor="w", padx=10, pady=5)
        
        self.diamondmine_grid_text = ctk.CTkTextbox(grid_frame, height=200)
        self.diamondmine_grid_text.pack(fill="x", padx=10, pady=(0, 10))
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(btn_frame, text="Load Current Values", command=self.load_diamondmine_values).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Apply Changes", command=self.apply_diamondmine, fg_color="green", hover_color="darkgreen").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Reset to Defaults", command=self.reset_diamondmine, fg_color="gray", hover_color="darkgray").pack(side="left", padx=5)
        
    def create_raw_editor_tab(self):
        """Create the raw config editor tab."""
        frame = self.tabview.tab("Raw Editor")
        
        desc = ctk.CTkLabel(frame, text="Edit the config file directly. Use this for advanced modifications not available in other tabs.",
                            font=("", 13))
        desc.pack(anchor="w", pady=(10, 15))
        
        self.raw_editor = ctk.CTkTextbox(frame, font=("Consolas", 12))
        self.raw_editor.pack(fill="both", expand=True)
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(btn_frame, text="Load from File", command=self.load_raw_editor).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Save to File", command=self.save_raw_editor, fg_color="green", hover_color="darkgreen").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Search", command=self.search_raw_editor).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Go to Line", command=self.goto_line).pack(side="left", padx=5)
        
    def create_status_bar(self):
        """Create the status bar at the bottom of the window."""
        status_frame = ctk.CTkFrame(self.root, height=30)
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)
        
        self.status_var = ctk.StringVar(value="Ready. Please load a config file to begin.")
        status_label = ctk.CTkLabel(status_frame, textvariable=self.status_var, anchor="w")
        status_label.pack(fill="x", padx=10, pady=5)
        
    
    def browse_game_path(self):
        """Browse for the Bejeweled 3 game directory."""
        path = filedialog.askdirectory(initialdir=self.game_path.get(), 
                                       title="Select Bejeweled 3 Directory")
        if path:
            self.game_path.set(path)
            self.save_settings()
            
    def load_config(self):
        """Load the secret.cfg config file."""
        config_path = os.path.join(self.game_path.get(), self.PROPERTIES_FOLDER, self.CONFIG_FILE)
        
        if not os.path.exists(config_path):
            messagebox.showerror("Error", f"Config file not found at:\n{config_path}\n\nMake sure you've extracted main.pak first.")
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config_content = f.read()
            
            self.config_path = config_path
            self.config_loaded = True
            self.parse_config()
            
            self.update_colorcount_display()
            self.raw_editor.delete('1.0', 'end')
            self.raw_editor.insert('1.0', self.config_content)
            
            self.status_var.set(f"Loaded: {config_path}")
            messagebox.showinfo("Success", "Config file loaded successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config file:\n{str(e)}")
            
    def open_config_direct(self):
        """Open a config file directly."""
        path = filedialog.askopenfilename(
            title="Open Config File",
            filetypes=[("Config files", "*.cfg"), ("All files", "*.*")]
        )
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.config_content = f.read()
                
                self.config_path = path
                self.config_loaded = True
                self.parse_config()
                
                self.update_colorcount_display()
                self.raw_editor.delete('1.0', 'end')
                self.raw_editor.insert('1.0', self.config_content)
                
                self.status_var.set(f"Loaded: {path}")
                messagebox.showinfo("Success", "Config file loaded successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load config file:\n{str(e)}")
                
    def save_config(self):
        """Save the config file."""
        if not self.config_path:
            self.save_config_as()
            return
        
        try:
            backup_path = self.config_path + ".backup"
            if os.path.exists(self.config_path):
                shutil.copy2(self.config_path, backup_path)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write(self.config_content)
            
            self.status_var.set(f"Saved: {self.config_path}")
            
            game_running = False
            try:
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Bejeweled3.exe'], 
                                        capture_output=True, text=True)
                if 'Bejeweled3.exe' in result.stdout:
                    game_running = True
            except:
                pass
            
            if game_running:
                messagebox.showinfo("Saved", 
                    "Config file saved successfully!\n\n"
                    "⚠️ IMPORTANT: Bejeweled 3 is currently running.\n\n"
                    "For changes to take effect:\n"
                    "1. Close the game completely\n"
                    "2. Start a new game in the modified mode\n\n"
                    f"Backup created at:\n{backup_path}")
            else:
                messagebox.showinfo("Success", 
                    "Config file saved successfully!\n\n"
                    "For changes to take effect:\n"
                    "1. Start Bejeweled 3\n"
                    "2. Start a new game in the modified mode\n\n"
                    f"Backup created at:\n{backup_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config file:\n{str(e)}")
            
    def save_config_as(self):
        """Save the config file to a new location."""
        path = filedialog.asksaveasfilename(
            title="Save Config File As",
            defaultextension=".cfg",
            filetypes=[("Config files", "*.cfg"), ("All files", "*.*")]
        )
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.config_content)
                
                self.config_path = path
                self.status_var.set(f"Saved: {path}")
                messagebox.showinfo("Success", "Config file saved successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save config file:\n{str(e)}")
                
    def parse_config(self):
        """Parse the config file into sections."""
        self.parsed_sections = {}
        
        current_section = "global"
        self.parsed_sections[current_section] = []
        
        for line in self.config_content.split('\n'):
            stripped = line.strip()
            
            section_found = False
            for quest_key in self.QUEST_MODES.keys():
                if stripped.lower().startswith(quest_key.lower()) and (stripped.endswith('{') or '{' in stripped):
                    current_section = quest_key.lower()
                    self.parsed_sections[current_section] = [line]
                    section_found = True
                    break
            
            if not section_found:
                if current_section in self.parsed_sections:
                    self.parsed_sections[current_section].append(line)
                else:
                    self.parsed_sections[current_section] = [line]
                    
    def update_colorcount_display(self):
        """Update the ColorCount display in the Quick Mods tab."""
        self.colorcount_text.configure(state="normal")
        self.colorcount_text.delete('1.0', 'end')
        
        for section, lines in self.parsed_sections.items():
            for line in lines:
                if 'ColorCount' in line and '=' in line:
                    match = re.search(r'ColorCount\s*=\s*(\d+)', line)
                    if match:
                        value = match.group(1)
                        display_name = self.QUEST_MODES.get(section, section)
                        self.colorcount_text.insert('end', f"{display_name}: {value}\n")
        
        self.colorcount_text.configure(state="disabled")
        
    
    def apply_colorcount(self):
        """Apply ColorCount to selected quest."""
        if not self.config_loaded:
            messagebox.showwarning("Warning", "Please load a config file first.")
            return
        
        quest_key = self.quest_selection.get()
        if not quest_key:
            messagebox.showwarning("Warning", "Please select a quest mode.")
            return
        
        try:
            value = int(self.colorcount_var.get())
        except (ValueError, TypeError):
            value = 6
        
        self.set_colorcount(quest_key, value)
            
    def apply_colorcount_all(self):
        """Apply ColorCount to all quests."""
        if not self.config_loaded:
            messagebox.showwarning("Warning", "Please load a config file first.")
            return
        
        value = self.colorcount_var.get()
        for quest_key in self.QUEST_MODES.keys():
            self.set_colorcount(quest_key, value)
            
    def set_colorcount(self, quest_key: str, value: int):
        """Set ColorCount for a specific quest."""
        lines = self.config_content.split('\n')
        
        quest_name_map = {
            "poker": "Poker",
            "butterflies": "Butterflies",
            "icestorm": "Ice Storm",
            "diamondmine": "Diamond Mine",
            "zen": "Zen",
            "quest": "Quest",
            "lightning": "Lightning",
            "classic": "Classic"
        }
        
        quest_name = quest_name_map.get(quest_key.lower(), quest_key)
        
        section_start = -1
        section_end = -1
        background_idx = -1
        colorcount_idx = -1
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.search(rf'^Quest\s+"{re.escape(quest_name)}"', stripped, re.IGNORECASE):
                section_start = i
                break
        
        if section_start == -1:
            messagebox.showwarning("Warning", f"Could not find Quest \"{quest_name}\" in config file.\n\nCheck the Raw Editor to see the config structure.")
            return
        
        for i in range(section_start + 1, len(lines)):
            line = lines[i]
            stripped = line.strip()
            
            if re.match(r'^#\d+$', stripped):
                section_end = i
                break
            
            if stripped.lower().startswith('quest "') and i > section_start:
                section_end = i
                break
            
            if 'BackgroundIdx' in line and '=' in line:
                background_idx = i
            
            if 'ColorCount' in line and '=' in line:
                colorcount_idx = i
        
        if section_end == -1:
            section_end = len(lines)
        
        print(f"\n=== DEBUG for {quest_name} ===")
        print(f"Section start: {section_start} -> '{lines[section_start].strip()[:50] if section_start >= 0 else 'N/A'}'")
        print(f"Section end: {section_end}")
        print(f"BackgroundIdx line: {background_idx} -> '{lines[background_idx].strip() if background_idx >= 0 else 'N/A'}'")
        print(f"ColorCount line: {colorcount_idx} -> '{lines[colorcount_idx].strip() if colorcount_idx >= 0 else 'N/A'}'")
        print(f"========================\n")
        
        debug_info = f"Section: lines {section_start}-{section_end}\nBackgroundIdx: line {background_idx}\nColorCount: line {colorcount_idx}"
        
        new_lines = []
        inserted = False
        
        print(f"\n=== BUILDING NEW CONTENT ===")
        print(f"Total lines to process: {len(lines)}")
        print(f"background_idx = {background_idx}")
        print(f"colorcount_idx = {colorcount_idx}")
        print(f"Condition check: background_idx >= 0: {background_idx >= 0}")
        print(f"Condition check: colorcount_idx == -1: {colorcount_idx == -1}")
        print(f"Will insert after BackgroundIdx: {background_idx >= 0 and colorcount_idx == -1}")
        
        for i, line in enumerate(lines):
            if i == colorcount_idx and colorcount_idx != -1:
                print(f"Line {i}: Updating existing ColorCount")
                indent_match = re.match(r'^(\s*)', line)
                indent = indent_match.group(1) if indent_match else '\t'
                new_lines.append(f'{indent}ColorCount = {value}')
                inserted = True
            elif i == background_idx and colorcount_idx == -1:
                print(f"Line {i}: Found BackgroundIdx, adding ColorCount after it")
                new_lines.append(line) 
                indent_match = re.match(r'^(\s*)', line)
                indent = indent_match.group(1) if indent_match else '\t'
                print(f"Indentation found: '{repr(indent)}'")
                new_colorcount_line = f'{indent}ColorCount = {value}'
                print(f"Adding line: '{new_colorcount_line}'")
                new_lines.append(new_colorcount_line)
                inserted = True
            else:
                new_lines.append(line)
        
        print(f"\nInserted: {inserted}")
        print(f"========================\n")
        
        if not inserted and section_end != -1:
            indent = '\t'
            for j in range(section_end - 1, section_start, -1):
                if lines[j].strip():
                    indent_match = re.match(r'^(\s*)', lines[j])
                    if indent_match:
                        indent = indent_match.group(1)
                    break
            
            final_lines = []
            for i, line in enumerate(lines):
                if i == section_end and not inserted:
                    final_lines.append(f'{indent}ColorCount = {value}')
                    inserted = True
                final_lines.append(line)
            new_lines = final_lines
        
        if inserted:
            self.config_content = '\n'.join(new_lines)
            
            self.raw_editor.delete('1.0', 'end')
            self.raw_editor.insert('1.0', self.config_content)
            
            for i, line in enumerate(new_lines):
                if 'ColorCount' in line and quest_name.lower() in self.config_content.lower():
                    self.raw_editor.see(f'{i+1}.0')
                    break
            
            self.parse_config()
            self.update_colorcount_display()
            
            self.status_var.set(f"Set ColorCount = {value} for {quest_name} - Click Save Config to apply!")
            
            if messagebox.askyesno("ColorCount Applied", 
                f"ColorCount set to {value} for {quest_name}.\n\nWould you like to save the config file now?"):
                self.save_config()
        else:
            messagebox.showwarning("Warning", f"Could not insert ColorCount for {quest_name}.")
        
    def reset_colorcount(self):
        """Remove ColorCount from the selected quest."""
        if not self.config_loaded:
            messagebox.showwarning("Warning", "Please load a config file first.")
            return
        
        quest_key = self.quest_selection.get()
        if not quest_key:
            messagebox.showwarning("Warning", "Please select a quest mode.")
            return
        
        quest_name_map = {
            "poker": "Poker",
            "butterflies": "Butterflies",
            "icestorm": "Ice Storm",
            "diamondmine": "Diamond Mine"
        }
        
        quest_name = quest_name_map.get(quest_key.lower(), quest_key)
        lines = self.config_content.split('\n')
        
        section_start = -1
        section_end = -1
        colorcount_idx = -1
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.search(rf'^Quest\s+"{re.escape(quest_name)}"', stripped, re.IGNORECASE):
                section_start = i
                break
        
        if section_start == -1:
            messagebox.showwarning("Warning", f"Could not find Quest \"{quest_name}\" in config file.")
            return
        
        for i in range(section_start + 1, len(lines)):
            stripped = lines[i].strip()
            
            if re.match(r'^#\d+$', stripped):
                section_end = i
                break
            
            if re.search(r'^Quest\s+"[^"]+"', stripped, re.IGNORECASE):
                section_end = i
                break
            
            if 'ColorCount' in lines[i] and '=' in lines[i]:
                colorcount_idx = i
        
        if section_end == -1:
            section_end = len(lines)
        
        if colorcount_idx == -1:
            messagebox.showinfo("Info", f"No ColorCount found for {quest_name}.\n\nThe quest is already using default gem colors.")
            return
        
        new_lines = []
        for i, line in enumerate(lines):
            if i != colorcount_idx:
                new_lines.append(line)
        
        self.config_content = '\n'.join(new_lines)
        
        self.raw_editor.delete('1.0', 'end')
        self.raw_editor.insert('1.0', self.config_content)
        
        self.parse_config()
        self.update_colorcount_display()
        
        self.status_var.set(f"Removed ColorCount for {quest_name}")
        
        if messagebox.askyesno("ColorCount Removed", 
            f"ColorCount removed for {quest_name}.\n\nWould you like to save the config file now?"):
            self.save_config()
    
    def show_debug_info(self):
        """Show debug information about the config file structure."""
        if not self.config_loaded:
            messagebox.showwarning("Warning", "Please load a config file first.")
            return
        
        quest_key = self.quest_selection.get()
        if not quest_key:
            messagebox.showwarning("Warning", "Please select a quest mode first.")
            return
        
        quest_name_map = {
            "poker": "Poker",
            "butterflies": "Butterflies",
            "icestorm": "Ice Storm",
            "diamondmine": "Diamond Mine",
            "zen": "Zen",
            "quest": "Quest",
            "lightning": "Lightning",
            "classic": "Classic"
        }
        
        quest_name = quest_name_map.get(quest_key.lower(), quest_key)
        lines = self.config_content.split('\n')
        
        quest_sections = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.search(r'^Quest\s+"[^"]+"', stripped, re.IGNORECASE):
                quest_sections.append((i, stripped))
        
        section_start = -1
        section_end = -1
        background_idx = -1
        colorcount_idx = -1
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.search(rf'^Quest\s+"{re.escape(quest_name)}"', stripped, re.IGNORECASE):
                section_start = i
                break
        
        if section_start >= 0:
            for i in range(section_start + 1, len(lines)):
                stripped = lines[i].strip()
                if re.match(r'^#\d+$', stripped):
                    section_end = i
                    break
                if re.search(r'^Quest\s+"[^"]+"', stripped, re.IGNORECASE):
                    section_end = i
                    break
                if 'BackgroundIdx' in lines[i] and '=' in lines[i]:
                    background_idx = i
                if 'ColorCount' in lines[i] and '=' in lines[i]:
                    colorcount_idx = i
            
            if section_end == -1:
                section_end = len(lines)
        
        debug_output = []
        debug_output.append(f"=== DEBUG INFO FOR {quest_name.upper()} ===\n")
        debug_output.append(f"Total lines in config: {len(lines)}")
        debug_output.append(f"Total Quest sections found: {len(quest_sections)}\n")
        
        debug_output.append("All Quest sections:")
        for idx, name in quest_sections:
            debug_output.append(f"  Line {idx}: {name}")
        
        debug_output.append(f"\nSelected Quest: {quest_name}")
        debug_output.append(f"  Section start: {section_start}")
        debug_output.append(f"  Section end: {section_end}")
        debug_output.append(f"  BackgroundIdx line: {background_idx}")
        debug_output.append(f"  ColorCount line: {colorcount_idx}\n")
        
        if section_start >= 0:
            debug_output.append(f"Content of section (lines {section_start}-{section_end}):")
            start = max(0, section_start)
            end = min(len(lines), section_end + 1)
            for i in range(start, end):
                marker = ""
                if i == background_idx:
                    marker = " [BackgroundIdx]"
                if i == colorcount_idx:
                    marker = " [ColorCount]"
                debug_output.append(f"  {i}: {lines[i][:80]}{marker}")
        
        debug_window = ctk.CTkToplevel(self.root)
        debug_window.title(f"Debug Info - {quest_name}")
        debug_window.geometry("700x500")
        
        text = ctk.CTkTextbox(debug_window, font=("Consolas", 11))
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert('1.0', '\n'.join(debug_output))
        text.configure(state="disabled")
        
    
    def load_butterflies_values(self):
        """Load current Butterflies values from config."""
        if not self.config_loaded:
            messagebox.showwarning("Warning", "Please load a config file first.")
            return
        
        for line in self.config_content.split('\n'):
            for key in self.butterflies_vars.keys():
                if key in line and '=' in line:
                    match = re.search(rf'{key}\s*=\s*([-\d.]+)', line)
                    if match:
                        try:
                            self.butterflies_vars[key].set(float(match.group(1)))
                        except ValueError:
                            pass
        
        self.status_var.set("Loaded Butterflies values")
        
    def apply_butterflies(self):
        """Apply Butterflies settings to config."""
        if not self.config_loaded:
            messagebox.showwarning("Warning", "Please load a config file first.")
            return
        
        lines = self.config_content.split('\n')
        new_lines = []
        in_butterflies = False
        
        for line in lines:
            new_line = line
            
            if re.search(r'^butterflies\s*\{', line, re.IGNORECASE):
                in_butterflies = True
            
            if in_butterflies and line.strip() == '}':
                in_butterflies = False
            
            if in_butterflies:
                for key, var in self.butterflies_vars.items():
                    if key in line and '=' in line:
                        new_line = re.sub(rf'({key}\s*=\s*)[-\d.]+', rf'\g<1>{var.get()}', line)
                        break
            
            new_lines.append(new_line)
        
        self.config_content = '\n'.join(new_lines)
        self.raw_editor.delete('1.0', 'end')
        self.raw_editor.insert('1.0', self.config_content)
        self.parse_config()
        
        self.status_var.set("Applied Butterflies settings")
        messagebox.showinfo("Success", "Butterflies settings applied!")
        
    def reset_butterflies(self):
        """Reset Butterflies settings to defaults."""
        defaults = {
            "SpawnCountStart": 1,
            "SpawnCountMax": 2.5,
            "SpawnCountPerLevel": 0.02,
            "SideSpawnChance": -0.2,
            "SideSpawnChancePerLevel": 0.002667,
            "SideSpawnChanceMax": 0.20,
        }
        for key, value in defaults.items():
            self.butterflies_vars[key].set(value)
        
    
    def load_poker_values(self):
        """Load current Poker values from config."""
        if not self.config_loaded:
            messagebox.showwarning("Warning", "Please load a config file first.")
            return
        
        for line in self.config_content.split('\n'):
            for key in ["FlameBonus", "StarBonus", "SkullMax"]:
                if key in line and '=' in line:
                    match = re.search(rf'{key}\s*=\s*(\d+)', line)
                    if match and key in self.poker_vars:
                        try:
                            self.poker_vars[key].set(int(match.group(1)))
                        except ValueError:
                            pass
            
            if 'HandValues' in line and '=' in line:
                match = re.search(r'HandValues\s*=\s*"([^"]+)"', line)
                if match:
                    self.poker_handvalues.set(match.group(1))
        
        self.status_var.set("Loaded Poker values")
        
    def apply_poker(self):
        """Apply Poker settings to config."""
        if not self.config_loaded:
            messagebox.showwarning("Warning", "Please load a config file first.")
            return
        
        lines = self.config_content.split('\n')
        new_lines = []
        in_poker = False
        
        for line in lines:
            new_line = line
            
            if re.search(r'^poker\s*\{', line, re.IGNORECASE):
                in_poker = True
            
            if in_poker and line.strip() == '}':
                in_poker = False
            
            if in_poker:
                for key, var in self.poker_vars.items():
                    if key in line and '=' in line:
                        new_line = re.sub(rf'({key}\s*=\s*)\d+', rf'\g<1>{var.get()}', line)
                        break
                
                if 'HandValues' in line and '=' in line:
                    new_line = re.sub(r'HandValues\s*=\s*"[^"]+"', 
                                     f'HandValues = "{self.poker_handvalues.get()}"', line)
            
            new_lines.append(new_line)
        
        self.config_content = '\n'.join(new_lines)
        self.raw_editor.delete('1.0', 'end')
        self.raw_editor.insert('1.0', self.config_content)
        self.parse_config()
        
        self.status_var.set("Applied Poker settings")
        messagebox.showinfo("Success", "Poker settings applied!")
        
    def reset_poker(self):
        """Reset Poker settings to defaults."""
        self.poker_vars["FlameBonus"].set(100)
        self.poker_vars["StarBonus"].set(250)
        self.poker_vars["SkullMax"].set(5)
        self.poker_handvalues.set("2500, 5000, 7500, 10000, 15000, 30000, 50000")
        
    
    def load_icestorm_values(self):
        """Load current Ice Storm values from config."""
        if not self.config_loaded:
            messagebox.showwarning("Warning", "Please load a config file first.")
            return
        
        in_icestorm = False
        for line in self.config_content.split('\n'):
            if re.search(r'^icestorm\s*\{', line, re.IGNORECASE):
                in_icestorm = True
                continue
            
            if in_icestorm and line.strip() == '}':
                in_icestorm = False
                continue
            
            if in_icestorm:
                for key in self.icestorm_vars.keys():
                    if key in line and '=' in line:
                        if key.startswith('Level'):
                            match = re.search(rf'{key}\s*=\s*"([^"]+)"', line)
                            if match and key in self.icestorm_levels:
                                self.icestorm_levels[key].set(match.group(1))
                        elif isinstance(self.icestorm_vars[key], ctk.StringVar):
                            match = re.search(rf'{key}\s*=\s*"([^"]+)"', line)
                            if match:
                                self.icestorm_vars[key].set(match.group(1))
                        else:
                            match = re.search(rf'{key}\s*=\s*([-\d.]+)', line)
                            if match:
                                try:
                                    self.icestorm_vars[key].set(float(match.group(1)))
                                except ValueError:
                                    pass
        
        self.status_var.set("Loaded Ice Storm values")
        
    def apply_icestorm(self):
        """Apply Ice Storm settings to config."""
        if not self.config_loaded:
            messagebox.showwarning("Warning", "Please load a config file first.")
            return
        
        lines = self.config_content.split('\n')
        new_lines = []
        in_icestorm = False
        
        for line in lines:
            new_line = line
            
            if re.search(r'^icestorm\s*\{', line, re.IGNORECASE):
                in_icestorm = True
            
            if in_icestorm and line.strip() == '}':
                in_icestorm = False
            
            if in_icestorm:
                for key, var in self.icestorm_vars.items():
                    if key in line and '=' in line and not key.startswith('Level'):
                        if isinstance(var, ctk.StringVar):
                            new_line = re.sub(rf'{key}\s*=\s*"[^"]+"', 
                                             f'{key} = "{var.get()}"', line)
                        else:
                            new_line = re.sub(rf'({key}\s*=\s*)[-\d.]+', 
                                             rf'\g<1>{var.get()}', line)
                        break
                
                for key, var in self.icestorm_levels.items():
                    if key in line and '=' in line:
                        new_line = re.sub(rf'{key}\s*=\s*"[^"]+"', 
                                         f'{key} = "{var.get()}"', line)
                        break
            
            new_lines.append(new_line)
        
        self.config_content = '\n'.join(new_lines)
        self.raw_editor.delete('1.0', 'end')
        self.raw_editor.insert('1.0', self.config_content)
        self.parse_config()
        
        self.status_var.set("Applied Ice Storm settings")
        messagebox.showinfo("Success", "Ice Storm settings applied!")
        
    def reset_icestorm(self):
        """Reset Ice Storm settings to defaults."""
        defaults = {
            "MatchPushStr": 0.07,
            "SpecialGemPushMod": 1.3,
            "SecondsUntilLose": 12,
            "RemoveBonusColumn": 2,
            "DoubleEdgeMult": 1.0,
            "FireSpeedMult": 2.0,
            "ColDestroyBonus": 1500,
            "MaxRandFireSpeedColDelta": 0.1,
            "DoubleColSpeedMult": 1.5,
            "FreezeDurationPerNegStrength": 50.0,
            "FreezeMax": 100.0,
            "FirstPushImpulse": 0.0,
            "FirstPushDecay": 0.0,
        }
        for key, value in defaults.items():
            if key in self.icestorm_vars:
                self.icestorm_vars[key].set(value)
        
        for key in ["ColCountBonus", "ColComboCoolDownVsCount", "MultiplierIceReq", 
                    "RowFireSpeed", "ColDistribution", "ReprieveStrVsRow"]:
            if key in self.icestorm_vars:
                self.icestorm_vars[key].set("")
        
        for key in self.icestorm_levels:
            self.icestorm_levels[key].set("")
        
    
    def load_diamondmine_values(self):
        """Load current Diamond Mine values from config."""
        if not self.config_loaded:
            messagebox.showwarning("Warning", "Please load a config file first.")
            return
        
        in_diamondmine = False
        grid_lines = []
        in_grid = False
        
        for line in self.config_content.split('\n'):
            if re.search(r'^diamondmine\s*\{', line, re.IGNORECASE):
                in_diamondmine = True
                continue
            
            if in_diamondmine and line.strip() == '}':
                in_diamondmine = False
                continue
            
            if in_diamondmine:
                if 'Grids' in line and '=' in line:
                    in_grid = True
                    grid_lines.append(line)
                    continue
                
                if in_grid:
                    grid_lines.append(line)
                    if '";' in line:
                        in_grid = False
                        self.diamondmine_grid_text.delete('1.0', 'end')
                        self.diamondmine_grid_text.insert('1.0', '\n'.join(grid_lines))
                    continue
                
                for key in self.diamondmine_vars.keys():
                    if key in line and '=' in line:
                        if isinstance(self.diamondmine_vars[key], ctk.BooleanVar):
                            if 'true' in line.lower():
                                self.diamondmine_vars[key].set(True)
                            elif 'false' in line.lower():
                                self.diamondmine_vars[key].set(False)
                        elif isinstance(self.diamondmine_vars[key], ctk.IntVar):
                            match = re.search(rf'{key}\s*=\s*(\d+)', line)
                            if match:
                                try:
                                    self.diamondmine_vars[key].set(int(match.group(1)))
                                except ValueError:
                                    pass
                        elif isinstance(self.diamondmine_vars[key], ctk.StringVar):
                            match = re.search(rf'{key}\s*=\s*"([^"]+)"', line)
                            if match:
                                self.diamondmine_vars[key].set(match.group(1))
        
        self.status_var.set("Loaded Diamond Mine values")
        
    def apply_diamondmine(self):
        """Apply Diamond Mine settings to config."""
        if not self.config_loaded:
            messagebox.showwarning("Warning", "Please load a config file first.")
            return
        
        lines = self.config_content.split('\n')
        new_lines = []
        in_diamondmine = False
        in_grid = False
        grid_replaced = False
        
        grid_content = self.diamondmine_grid_text.get('1.0', 'end').strip()
        
        for line in lines:
            new_line = line
            
            if re.search(r'^diamondmine\s*\{', line, re.IGNORECASE):
                in_diamondmine = True
            
            if in_diamondmine and line.strip() == '}':
                in_diamondmine = False
            
            if in_diamondmine:
                if 'Grids' in line and '=' in line:
                    in_grid = True
                    if not grid_replaced:
                        new_lines.append(grid_content)
                        grid_replaced = True
                    continue
                
                if in_grid:
                    if '";' in line:
                        in_grid = False
                    continue
                
                for key, var in self.diamondmine_vars.items():
                    if key in line and '=' in line:
                        if isinstance(var, ctk.BooleanVar):
                            value = "true" if var.get() else "false"
                            new_line = re.sub(rf'({key}\s*=\s*)(true|false)', 
                                             rf'\g<1>{value}', line, flags=re.IGNORECASE)
                        elif isinstance(var, ctk.IntVar):
                            new_line = re.sub(rf'({key}\s*=\s*)\d+', 
                                             rf'\g<1>{var.get()}', line)
                        elif isinstance(var, ctk.StringVar):
                            new_line = re.sub(rf'{key}\s*=\s*"[^"]+"', 
                                             f'{key} = "{var.get()}"', line)
                        break
            
            new_lines.append(new_line)
        
        self.config_content = '\n'.join(new_lines)
        self.raw_editor.delete('1.0', 'end')
        self.raw_editor.insert('1.0', self.config_content)
        self.parse_config()
        
        self.status_var.set("Applied Diamond Mine settings")
        messagebox.showinfo("Success", "Diamond Mine settings applied!")
        
    def reset_diamondmine(self):
        """Reset Diamond Mine settings to defaults."""
        defaults = {
            "Time": 90,
            "TargetCount": 200,
            "TimeBonus": 30,
            "MegaTimeBonus": 90,
            "DigCountPerScroll": 2,
            "HighScoreBase": 50000,
            "HighScoreIncr": 10000,
            "ArtifactBaseValue": 1500,
            "GoldValue": 1000,
            "DiamondValue": 2500,
            "ArtifactMinTiles": 10,
            "ArtifactMaxTiles": 26,
            "ArtifactSkipTileCount": 4,
        }
        for key, value in defaults.items():
            if key in self.diamondmine_vars:
                self.diamondmine_vars[key].set(value)
        
        self.diamondmine_vars["HyperMixers"].set(True)
        
        for key in ["TreasureRange", "DarkRockFrequency", "PowerGemThresholdDepth0",
                    "PowerGemThresholdDepth20", "PowerGemThresholdDepth40", "ArtifactPossRange",
                    "MinBrickStrPerLevel", "MaxBrickStrPerLevel", "EdgeBrickStrPerLevel",
                    "MinMineStrPerLevel", "MaxMineStrPerLevel", "MineProbPerLevel",
                    "BrickStrSpread", "MineStrSpread", "ArtifactSpread"]:
            if key in self.diamondmine_vars:
                self.diamondmine_vars[key].set("")
        
    
    def load_raw_editor(self):
        """Load content into raw editor from file."""
        if self.config_loaded:
            self.raw_editor.delete('1.0', 'end')
            self.raw_editor.insert('1.0', self.config_content)
        else:
            self.load_config()
        
    def save_raw_editor(self):
        """Save raw editor content to config."""
        if not self.config_loaded:
            messagebox.showwarning("Warning", "Please load a config file first.")
            return
        
        self.config_content = self.raw_editor.get('1.0', 'end')
        self.parse_config()
        self.save_config()
        
    def search_raw_editor(self):
        """Search in raw editor."""
        search_window = ctk.CTkToplevel(self.root)
        search_window.title("Search")
        search_window.geometry("350x120")
        search_window.transient(self.root)
        
        ctk.CTkLabel(search_window, text="Search for:").pack(pady=10)
        
        search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(search_window, textvariable=search_var, width=300)
        search_entry.pack(pady=5)
        search_entry.focus()
        
        def do_search():
            term = search_var.get()
            if term:
                content = self.raw_editor.get('1.0', 'end')
                start_idx = content.find(term)
                if start_idx != -1:
                    line_num = content[:start_idx].count('\n') + 1
                    self.raw_editor.see(f'{line_num}.0')
                else:
                    messagebox.showinfo("Search", "Text not found.")
        
        ctk.CTkButton(search_window, text="Find", command=do_search).pack(pady=10)
        search_entry.bind('<Return>', lambda e: do_search())
        
    def goto_line(self):
        """Go to a specific line in the raw editor."""
        line_window = ctk.CTkToplevel(self.root)
        line_window.title("Go to Line")
        line_window.geometry("300x120")
        line_window.transient(self.root)
        
        ctk.CTkLabel(line_window, text="Line number:").pack(pady=10)
        
        line_var = ctk.StringVar()
        line_entry = ctk.CTkEntry(line_window, textvariable=line_var, width=150)
        line_entry.pack(pady=5)
        line_entry.focus()
        
        def do_goto():
            try:
                line_num = int(line_var.get())
                self.raw_editor.see(f'{line_num}.0')
                line_window.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid line number.")
        
        ctk.CTkButton(line_window, text="Go", command=do_goto).pack(pady=10)
        line_entry.bind('<Return>', lambda e: do_goto())
        
    
    def set_quickbms_path(self):
        """Set the path to QuickBMS executable."""
        path = filedialog.askopenfilename(
            title="Select QuickBMS Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if path:
            self.quickbms_path.set(path)
            self.save_settings()
            
    def set_script_path(self):
        """Set the path to 7x7m.bms script."""
        path = filedialog.askopenfilename(
            title="Select BMS Script",
            filetypes=[("BMS scripts", "*.bms"), ("All files", "*.*")]
        )
        if path:
            self.script_path.set(path)
            self.save_settings()
            
    def extract_main_pak(self):
        """Extract main.pak using QuickBMS."""
        if not self.quickbms_path.get():
            messagebox.showwarning("Warning", "Please set the QuickBMS executable path first.\n\nGo to Tools > Set QuickBMS Path")
            return
        
        if not self.script_path.get():
            messagebox.showwarning("Warning", "Please set the 7x7m.bms script path first.\n\nGo to Tools > Set Script Path")
            return
        
        main_pak_path = os.path.join(self.game_path.get(), self.MAIN_PAK)
        if not os.path.exists(main_pak_path):
            messagebox.showerror("Error", f"main.pak not found at:\n{main_pak_path}")
            return
        
        try:
            cmd = [
                self.quickbms_path.get(),
                "-o",
                self.script_path.get(),
                main_pak_path,
                self.game_path.get()
            ]
            
            self.status_var.set("Extracting main.pak...")
            
            def run_extraction():
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.game_path.get())
                    self.root.after(0, lambda: self.extraction_complete(result))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Extraction failed:\n{str(e)}"))
            
            thread = threading.Thread(target=run_extraction)
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run QuickBMS:\n{str(e)}")
            
    def extraction_complete(self, result):
        """Handle extraction completion."""
        if result.returncode == 0:
            self.status_var.set("Extraction complete!")
            messagebox.showinfo("Success", "main.pak extracted successfully!\n\nYou can now load the config file.")
        else:
            self.status_var.set("Extraction failed")
            messagebox.showerror("Error", f"Extraction failed:\n{result.stderr}")
            
    def backup_config(self):
        """Create a backup of the current config."""
        if not self.config_path or not os.path.exists(self.config_path):
            messagebox.showwarning("Warning", "No config file loaded.")
            return
        
        backup_path = filedialog.asksaveasfilename(
            title="Save Backup",
            defaultextension=".cfg.backup",
            filetypes=[("Backup files", "*.backup"), ("All files", "*.*")]
        )
        
        if backup_path:
            try:
                shutil.copy2(self.config_path, backup_path)
                messagebox.showinfo("Success", f"Backup saved to:\n{backup_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create backup:\n{str(e)}")
                
    def restore_backup(self):
        """Restore a backup of the config."""
        backup_path = filedialog.askopenfilename(
            title="Select Backup",
            filetypes=[("Backup files", "*.backup"), ("All files", "*.*")]
        )
        
        if backup_path:
            try:
                if self.config_path:
                    shutil.copy2(backup_path, self.config_path)
                    self.load_config()
                    messagebox.showinfo("Success", "Backup restored successfully!")
                else:
                    messagebox.showwarning("Warning", "Please load a config file first.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to restore backup:\n{str(e)}")
    
    
    def download_quickbms(self):
        """Download QuickBMS tool."""
        download_window = ctk.CTkToplevel(self.root)
        download_window.title("Download QuickBMS")
        download_window.geometry("550x350")
        download_window.transient(self.root)
        download_window.grab_set()
        
        ctk.CTkLabel(download_window, text="Download QuickBMS", font=("", 18, "bold")).pack(pady=15)
        ctk.CTkLabel(download_window, text="QuickBMS is a file extraction tool by Luigi Auriemma.").pack(pady=5)
        ctk.CTkLabel(download_window, text="Official website: aluigi.org", font=("", 11, "italic")).pack(pady=5)
        
        loc_frame = ctk.CTkFrame(download_window, fg_color="transparent")
        loc_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(loc_frame, text="Save to:").pack(side="left")
        
        download_dir = ctk.StringVar(value=os.path.join(os.path.dirname(__file__), "tools"))
        ctk.CTkEntry(loc_frame, textvariable=download_dir, width=300).pack(side="left", padx=10)
        ctk.CTkButton(loc_frame, text="Browse", command=lambda: download_dir.set(
            filedialog.askdirectory(title="Select Download Folder"))).pack(side="left")
        
        progress_bar = ctk.CTkProgressBar(download_window, width=500)
        progress_bar.pack(pady=10)
        progress_bar.set(0)
        
        status_label = ctk.CTkLabel(download_window, text="")
        status_label.pack(pady=5)
        
        size_label = ctk.CTkLabel(download_window, text="")
        size_label.pack(pady=2)
        
        btn_frame = ctk.CTkFrame(download_window, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        download_btn = ctk.CTkButton(btn_frame, text="Download", command=lambda: start_download())
        download_btn.pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Open Website", command=lambda: webbrowser.open("https://aluigi.altervista.org/papers.htm#quickbms")).pack(side="left", padx=5)
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=download_window.destroy, fg_color="gray", hover_color="darkgray")
        cancel_btn.pack(side="left", padx=5)
        
        def start_download():
            save_dir = download_dir.get()
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            download_btn.configure(state="disabled")
            cancel_btn.configure(state="disabled")
            status_label.configure(text="Connecting to server...")
            download_window.update()
            
            def do_download():
                try:
                    quickbms_url = "https://aluigi.altervista.org/papers/quickbms.zip"
                    zip_path = os.path.join(save_dir, "quickbms.zip")
                    
                    def progress_hook(block_num, block_size, total_size):
                        downloaded = block_num * block_size
                        if total_size > 0:
                            percent = min(100, (downloaded / total_size) * 100)
                            downloaded_mb = downloaded / (1024 * 1024)
                            total_mb = total_size / (1024 * 1024)
                            
                            def update_ui():
                                progress_bar.set(percent / 100)
                                status_label.configure(text=f"Downloading QuickBMS... {percent:.1f}%")
                                size_label.configure(text=f"{downloaded_mb:.2f} MB / {total_mb:.2f} MB")
                            self.root.after(0, update_ui)
                    
                    urllib.request.urlretrieve(quickbms_url, zip_path, progress_hook)
                    
                    def update_extract():
                        progress_bar.set(0)
                        status_label.configure(text="Extracting files...")
                        size_label.configure(text="Please wait...")
                    self.root.after(0, update_extract)
                    
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        file_list = zip_ref.namelist()
                        for i, file in enumerate(file_list):
                            zip_ref.extract(file, save_dir)
                            percent = ((i + 1) / len(file_list)) * 100
                            def update_extract_progress(p=percent):
                                progress_bar.set(p / 100)
                                status_label.configure(text=f"Extracting... {p:.1f}%")
                            self.root.after(0, update_extract_progress)
                    
                    exe_path = None
                    for root_dir, dirs, files in os.walk(save_dir):
                        for file in files:
                            if file == "quickbms.exe":
                                exe_path = os.path.join(root_dir, file)
                                break
                    
                    os.remove(zip_path)
                    
                    def on_success():
                        progress_bar.set(1)
                        status_label.configure(text="Download complete!")
                        size_label.configure(text="Done!")
                        if exe_path:
                            self.quickbms_path.set(exe_path)
                            self.save_settings()
                            messagebox.showinfo("Success", 
                                f"QuickBMS downloaded successfully!\n\nLocation: {exe_path}\n\n"
                                "The path has been set automatically.")
                        else:
                            messagebox.showinfo("Success", 
                                f"QuickBMS downloaded to:\n{save_dir}\n\n"
                                "Please set the path manually via Tools > Set QuickBMS Path")
                        download_window.destroy()
                    
                    self.root.after(0, on_success)
                    
                except Exception as e:
                    def on_error():
                        progress_bar.set(0)
                        status_label.configure(text="Download failed")
                        size_label.configure(text="")
                        download_btn.configure(state="normal")
                        cancel_btn.configure(state="normal")
                        messagebox.showerror("Error", f"Failed to download QuickBMS:\n{str(e)}\n\n"
                            "Please download manually from:\nhttps://aluigi.altervista.org/papers/quickbms.zip")
                    self.root.after(0, on_error)
            
            thread = threading.Thread(target=do_download)
            thread.start()
        
    def download_script(self):
        """Download 7x7m.bms script."""
        download_window = ctk.CTkToplevel(self.root)
        download_window.title("Download 7x7m.bms Script")
        download_window.geometry("550x400")
        download_window.transient(self.root)
        download_window.grab_set()
        
        ctk.CTkLabel(download_window, text="Download 7x7m.bms Script", font=("", 18, "bold")).pack(pady=15)
        ctk.CTkLabel(download_window, text="The 7x7m.bms script is used to extract Bejeweled 3 game files.").pack(pady=5)
        ctk.CTkLabel(download_window, text="Official source: aluigi.org", font=("", 11, "italic")).pack(pady=5)
        
        loc_frame = ctk.CTkFrame(download_window, fg_color="transparent")
        loc_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(loc_frame, text="Save to:").pack(side="left")
        
        download_dir = ctk.StringVar(value=os.path.join(os.path.dirname(__file__), "tools"))
        ctk.CTkEntry(loc_frame, textvariable=download_dir, width=300).pack(side="left", padx=10)
        ctk.CTkButton(loc_frame, text="Browse", command=lambda: download_dir.set(
            filedialog.askdirectory(title="Select Download Folder"))).pack(side="left")
        
        progress_bar = ctk.CTkProgressBar(download_window, width=500)
        progress_bar.pack(pady=10)
        progress_bar.set(0)
        
        status_label = ctk.CTkLabel(download_window, text="")
        status_label.pack(pady=5)
        
        size_label = ctk.CTkLabel(download_window, text="")
        size_label.pack(pady=2)
        
        btn_frame = ctk.CTkFrame(download_window, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        download_btn = ctk.CTkButton(btn_frame, text="Download", command=lambda: start_download())
        download_btn.pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Open Website", command=lambda: webbrowser.open("https://aluigi.altervista.org/bms.htm")).pack(side="left", padx=5)
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=download_window.destroy, fg_color="gray", hover_color="darkgray")
        cancel_btn.pack(side="left", padx=5)
        
        def start_download():
            save_dir = download_dir.get()
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            download_btn.configure(state="disabled")
            cancel_btn.configure(state="disabled")
            status_label.configure(text="Connecting to server...")
            download_window.update()
            
            def do_download():
                try:
                    script_url = "http://aluigi.org/papers/bms/7x7m.bms"
                    script_path = os.path.join(save_dir, "7x7m.bms")
                    
                    def progress_hook(block_num, block_size, total_size):
                        downloaded = block_num * block_size
                        if total_size > 0:
                            percent = min(100, (downloaded / total_size) * 100)
                            downloaded_kb = downloaded / 1024
                            total_kb = total_size / 1024
                            
                            def update_ui():
                                progress_bar.set(percent / 100)
                                status_label.configure(text=f"Downloading 7x7m.bms... {percent:.1f}%")
                                size_label.configure(text=f"{downloaded_kb:.1f} KB / {total_kb:.1f} KB")
                            self.root.after(0, update_ui)
                    
                    urllib.request.urlretrieve(script_url, script_path, progress_hook)
                    
                    def on_success():
                        progress_bar.set(1)
                        status_label.configure(text="Download complete!")
                        size_label.configure(text="Done!")
                        self.script_path.set(script_path)
                        self.save_settings()
                        
                        main_pak_path = os.path.join(self.game_path.get(), self.MAIN_PAK)
                        main_pak_bak_path = main_pak_path + ".bak"
                        rename_message = ""
                        
                        if os.path.exists(main_pak_path):
                            try:
                                if os.path.exists(main_pak_bak_path):
                                    os.remove(main_pak_bak_path)
                                os.rename(main_pak_path, main_pak_bak_path)
                                rename_message = f"\n\n✓ Renamed main.pak to main.pak.bak\n(This is required for mods to work)"
                            except Exception as e:
                                rename_message = f"\n\n⚠ Could not rename main.pak:\n{str(e)}"
                        
                        messagebox.showinfo("Success", 
                            f"7x7m.bms downloaded successfully!\n\nLocation: {script_path}\n\n"
                            f"The path has been set automatically.{rename_message}")
                        download_window.destroy()
                    
                    self.root.after(0, on_success)
                    
                except Exception as e:
                    def on_error():
                        progress_bar.set(0)
                        status_label.configure(text="Download failed")
                        size_label.configure(text="")
                        download_btn.configure(state="normal")
                        cancel_btn.configure(state="normal")
                        messagebox.showerror("Error", f"Failed to download 7x7m.bms:\n{str(e)}\n\n"
                            "Please download manually from:\nhttp://aluigi.org/papers/bms/7x7m.bms")
                    self.root.after(0, on_error)
            
            thread = threading.Thread(target=do_download)
            thread.start()
                
    
    def load_settings(self):
        """Load saved settings from file."""
        settings_file = os.path.join(os.path.dirname(__file__), "settings.json")
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                
                if 'game_path' in settings:
                    self.game_path.set(settings['game_path'])
                if 'quickbms_path' in settings:
                    self.quickbms_path.set(settings['quickbms_path'])
                if 'script_path' in settings:
                    self.script_path.set(settings['script_path'])
                    
            except Exception:
                pass
                
    def save_settings(self):
        """Save settings to file."""
        settings_file = os.path.join(os.path.dirname(__file__), "settings.json")
        try:
            settings = {
                'game_path': self.game_path.get(),
                'quickbms_path': self.quickbms_path.get(),
                'script_path': self.script_path.get()
            }
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception:
            pass
                
    def show_quick_start(self):
        """Show quick start guide."""
        guide = """
BEJEWELED 3 MODDING TOOL - QUICK START GUIDE

1. SETUP
   - Download QuickBMS from aluigi.org
   - Download the 7x7m.bms script from aluigi.org
   - Go to Tools > Set QuickBMS Path and select quickbms.exe
   - Go to Tools > Set Script Path and select 7x7m.bms

2. EXTRACT GAME FILES
   - Set your Bejeweled 3 game directory (default: Steam path)
   - Go to Tools > Extract main.pak
   - This will extract game files to the game directory

3. LOAD CONFIG
   - Click "Load Config" to load secret.cfg
   - The config file is in the "properties" folder

4. MODIFY SETTINGS
   - Use the tabs to modify different game modes
   - Quick Mods: Change gem colors (ColorCount)
   - Butterflies: Modify butterfly spawn settings
   - Poker: Change hand values and bonuses
   - Ice Storm: Adjust ice column settings
   - Diamond Mine: Modify mining parameters
   - Raw Editor: Direct config file editing

5. SAVE CHANGES
   - Click "Save Config" to save your changes
   - A backup is automatically created
   - Restart the game to see changes

TIPS:
   - Always backup your main.pak before modding
   - ColorCount ranges from 1-6 gems
   - Changes require starting a new game in that mode
"""
        
        help_window = ctk.CTkToplevel(self.root)
        help_window.title("Quick Start Guide")
        help_window.geometry("650x550")
        
        text = ctk.CTkTextbox(help_window, font=("", 12))
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert('1.0', guide)
        text.configure(state="disabled")
        
    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo("About", 
            "Modjeweled\n\n"
            "Version 2.0 (CustomTkinter Edition)\n\n"
            "An unofficial modding tool for Bejeweled 3.\n\n"
            "Features:\n"
            "- Extract main.pak using QuickBMS\n"
            "- Modify gem colors (ColorCount)\n"
            "- Edit Butterflies, Poker, Ice Storm, Diamond Mine settings\n"
            "- Raw config editor for advanced modifications\n"
            "- Modern dark/light theme support\n\n"
            )


def main():
    """Main entry point."""
    root = ctk.CTk()
    app = BejeweledModder(root)
    root.mainloop()


if __name__ == "__main__":
    main()