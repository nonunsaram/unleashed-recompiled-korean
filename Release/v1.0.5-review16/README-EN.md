# Korean Translation 1.0.5-review16 — local review candidate

For Unleashed Recompiled v1.0.3 on Windows x64. Install either Basic or Full, not both. Basic translates in-game text, subtitles, and image UI. Full adds the executable UI translation setup tool; its EXE patch is unchanged from 1.0.4.

Set the game's text language to **English** and enable subtitles. If you use UnleasHD 1.4.2 **1440p**, place the Korean mod above UnleasHD in HedgeModManager and select **Korean UI resolution → UnleasHD UI (1440p)**. Save the configuration and restart the game. Otherwise keep **Basic UI (720p)**. Choose the DLC option that matches your installation.

This revision adds an HD Korean UI profile, corrects three character names, updates the Empire City night Act 2 preview, and synchronizes Korean title and opening logos. See `CHANGELOG-KO.md` for the full list and verification limits. Fifteen legacy Japanese glyph pages remain at 512×512; their use in game is unconfirmed.

The review build includes UnleasHD-derived files. The UI compatibility files (HUD, shop, world map, dialogue nameplate, DLC preview) are based on UnleasHD 1.4.2 (1440p); the optional Korean title logos and their glow textures are based on assets from the UnleasHD 4K repository (revision c7a70974). Do not publicly redistribute it until asset permission or an on-device generation path is established.

Review16 removes 28 unchanged HD UI texture instances and four unchanged HD title-logo instances. The separate UnleasHD mod supplies them. All Korean-edited HD graphics, Korean font/subtitle pages, and opening-logo edits remain byte-identical to review15. Original English/Japanese title-logo choices now use the resolution of the installed lower-priority mod, or the stock game if no logo mod is installed. Redistribution permission for the retained modified UnleasHD artwork is still pending.
