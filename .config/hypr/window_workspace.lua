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
