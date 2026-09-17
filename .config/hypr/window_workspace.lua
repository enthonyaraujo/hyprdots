-- ██     ██ ██ ███  ██ ████▄  ▄████▄ ██     ██ ▄█████   ▄████▄ ███  ██ ████▄    
-- ██ ▄█▄ ██ ██ ██ ▀▄██ ██  ██ ██  ██ ██ ▄█▄ ██ ▀▀▀▄▄▄   ██▄▄██ ██ ▀▄██ ██  ██   
--  ▀██▀██▀  ██ ██   ██ ████▀  ▀████▀  ▀██▀██▀  █████▀   ██  ██ ██   ██ ████▀    
                                                                                                                        
-- ██     ██ ▄████▄ █████▄  ██ ▄█▀ ▄█████ █████▄ ▄████▄ ▄█████ ██████ ▄█████ 
-- ██ ▄█▄ ██ ██  ██ ██▄▄██▄ ████   ▀▀▀▄▄▄ ██▄▄█▀ ██▄▄██ ██     ██▄▄   ▀▀▀▄▄▄ 
--  ▀██▀██▀  ▀████▀ ██   ██ ██ ▀█▄ █████▀ ██     ██  ██ ▀█████ ██▄▄▄▄ █████▀ 

-- See https://wiki.hypr.land/configuring/core/rules/

-- Example window rules:
-- hl.window_rule({
--     name  = "kitty-float",
--     match = { class = "^(kitty)$" },
--     float = true,
-- })

-- hl.window_rule({
--     name   = "kitty-size",
--     match  = { class = "^(kitty)$" },
--     size   = "900 600",
--     center = true,
-- })

-- hl.window_rule({
--     name  = "fix-xwayland-drags",
--     match = {
--         class      = "^$",
--         title      = "^$",
--         xwayland   = true,
--         float      = true,
--         fullscreen = false,
--         pin        = false,
--     },
--     no_focus = true,
-- })

-- Example workspace rule:
-- hl.workspace_rule({
--     workspace = 1,
--     monitor   = "eDP-1",
-- })

-- Rules for GTK Applets (Volume, Calendar, Wi-Fi, Bluetooth, Battery, Session, Wallpaper)
hl.window_rule({
    name    = "gtk-applets-rules",
    match   = { class = "^(volume-applet|calendar-applet|wifi-applet|bluetooth-applet|power-applet|session-applet|wallpaper-applet).*$" },
    float   = true,
    pin     = true,
})
